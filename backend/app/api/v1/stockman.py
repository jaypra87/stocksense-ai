"""Stock-man: conversations and the streaming turn endpoint.

The turn streams as server-sent events. The generator owns its own database
session because the request's session is closed when the handler returns,
which with a streaming body is before the first byte goes out.
"""

import json
import logging
import uuid
from collections.abc import Iterator
from functools import lru_cache

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.cache.redis_client import get_redis
from app.core.config import get_settings
from app.core.rate_limit import rate_limit
from app.db.models.conversation import Conversation, ConversationMessage
from app.db.models.digest import Digest
from app.db.models.user import User
from app.db.session import SessionLocal, get_db, set_rls_user
from app.schemas.stockman import (
    ConversationCreate,
    ConversationOut,
    ConversationSummary,
    DigestOut,
    MessageCreate,
    StatusOut,
)
from app.services.market_data.base import MarketDataProvider
from app.services.market_data.registry import get_provider
from app.services.stockman import agent, budget, digest
from app.services.stockman.budget import BudgetExceeded
from app.services.stockman.digest import DigestBusy
from app.services.stockman.tools import ToolContext

logger = logging.getLogger("stocksense.stockman")

_settings = get_settings()
_message_limiter = rate_limit(
    "stockman", _settings.stockman_rate_limit, _settings.stockman_rate_window_seconds
)

router = APIRouter(prefix="/stockman", tags=["stockman"], dependencies=[Depends(get_current_user)])

DISCLAIMER = (
    "Stock-man is an educational assistant. Its answers come from this app's "
    "models and data, which are often wrong. Not financial advice."
)

OFFLINE = "Stock-man is offline: no model API key is configured on the server."
RESTING = "Stock-man has used up its budget for today and is resting until tomorrow."


@lru_cache
def get_anthropic_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=_settings.anthropic_api_key, max_retries=2, timeout=90.0)


@router.get("/status", response_model=StatusOut)
def status(user: User = Depends(get_current_user), redis: Redis = Depends(get_redis)) -> dict:
    used, _ = budget.usage(redis, user.id)
    return {
        "enabled": _settings.stockman_enabled,
        "model": _settings.stockman_model,
        "budget": {"used": used, "limit": _settings.stockman_user_daily_tokens},
        "disclaimer": DISCLAIMER,
    }


@router.get("/digest", response_model=DigestOut)
def get_digest(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
    client: anthropic.Anthropic = Depends(get_anthropic_client),
) -> dict:
    """Today's digest, written on the first call of the day."""
    return _digest(db, redis, provider, client, user.id, force=False)


@router.post("/digest/refresh", response_model=DigestOut, dependencies=[Depends(_message_limiter)])
def refresh_digest(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
    client: anthropic.Anthropic = Depends(get_anthropic_client),
) -> dict:
    return _digest(db, redis, provider, client, user.id, force=True)


def _digest(
    db: Session,
    redis: Redis,
    provider: MarketDataProvider,
    client: anthropic.Anthropic,
    user_id: uuid.UUID,
    force: bool,
) -> dict:
    unavailable = {"available": False, "disclaimer": DISCLAIMER}
    if not _settings.stockman_enabled:
        return {**unavailable, "reason": OFFLINE}
    if not force:
        cached = digest.today(db, user_id)
        if cached is not None:
            return {**cached, "disclaimer": DISCLAIMER}
    try:
        budget.check(redis, user_id)
        written = digest.generate(db, redis, provider, client, user_id, force=force)
    except BudgetExceeded:
        return {**unavailable, "reason": RESTING}
    except DigestBusy:
        raise HTTPException(status_code=409, detail="Today's digest is being written.") from None
    except anthropic.APIError:
        logger.exception("stockman: digest failed")
        return {**unavailable, "reason": "Stock-man couldn't write the digest right now."}
    budget.charge(redis, user_id, _digest_tokens(db, user_id))
    return {**written, "disclaimer": DISCLAIMER}


def _digest_tokens(db: Session, user_id: uuid.UUID) -> int:
    row = (
        db.execute(
            select(Digest).where(Digest.user_id == user_id).order_by(Digest.created_at.desc())
        )
        .scalars()
        .first()
    )
    return (row.input_tokens + row.output_tokens) if row is not None else 0


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[dict]:
    rows = db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    ).scalars()
    return [_summary(c) for c in rows]


@router.post("/conversations", response_model=ConversationSummary, status_code=201)
def create_conversation(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    conversation = Conversation(user_id=user.id, title=body.title or "New conversation")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return _summary(conversation)


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    conversation = _owned(db, user.id, conversation_id)
    messages = db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.seq)
    ).scalars()
    return {
        **_summary(conversation),
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    db.delete(_owned(db, user.id, conversation_id))
    db.commit()


@router.post(
    "/conversations/{conversation_id}/messages",
    dependencies=[Depends(_message_limiter)],
    responses={200: {"content": {"text/event-stream": {}}}},
)
def send_message(
    conversation_id: uuid.UUID,
    body: MessageCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    provider: MarketDataProvider = Depends(get_provider),
    client: anthropic.Anthropic = Depends(get_anthropic_client),
) -> StreamingResponse:
    if not _settings.stockman_enabled:
        raise HTTPException(status_code=503, detail=OFFLINE)
    conversation = _owned(db, user.id, conversation_id)
    try:
        budget.check(redis, user.id)
    except BudgetExceeded:
        raise HTTPException(status_code=429, detail=RESTING) from None

    history = [
        {"role": m.role, "content": m.content}
        for m in db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation.id)
            .order_by(ConversationMessage.seq)
        ).scalars()
    ]
    text = body.content.strip()
    db.add(
        ConversationMessage(
            conversation_id=conversation.id, role="user", content=[{"type": "text", "text": text}]
        )
    )
    if conversation.title == "New conversation":
        conversation.title = text[:117] + "..." if len(text) > 120 else text
    db.commit()

    def events() -> Iterator[str]:
        session = SessionLocal()
        set_rls_user(session, user.id)
        ctx = ToolContext(db=session, redis=redis, provider=provider, user_id=user.id)
        done: dict | None = None
        try:
            for name, data in agent.run_turn(client, ctx, history, text):
                if name == "done":
                    done = data
                    yield _sse("done", {"grounding": data["grounding"], "usage": data["usage"]})
                else:
                    yield _sse(name, data)
        except anthropic.RateLimitError:
            yield _sse("error", {"message": "The model is busy. Try again in a moment."})
        except anthropic.APIStatusError as exc:
            logger.warning("stockman: API error %s", exc.status_code)
            yield _sse("error", {"message": "The model returned an error. Try again."})
        except anthropic.APIConnectionError:
            yield _sse("error", {"message": "Couldn't reach the model. Try again."})
        except Exception:
            logger.exception("stockman: turn failed")
            yield _sse("error", {"message": "Something went wrong on our side."})
        finally:
            if done is not None:
                _persist(session, conversation.id, done)
                budget.charge(
                    redis, user.id, done["usage"]["input_tokens"] + done["usage"]["output_tokens"]
                )
            session.close()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _persist(session: Session, conversation_id: uuid.UUID, done: dict) -> None:
    usage = done["usage"]
    turns = done["transcript"]
    for i, turn in enumerate(turns):
        last = i == len(turns) - 1
        session.add(
            ConversationMessage(
                conversation_id=conversation_id,
                role=turn["role"],
                content=turn["content"],
                input_tokens=usage["input_tokens"] if last else 0,
                output_tokens=usage["output_tokens"] if last else 0,
            )
        )
    conversation = session.get(Conversation, conversation_id)
    if conversation is not None:
        conversation.updated_at = func.now()
    session.commit()


def _owned(db: Session, user_id: uuid.UUID, conversation_id: uuid.UUID) -> Conversation:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


def _summary(c: Conversation) -> dict:
    return {
        "id": str(c.id),
        "title": c.title,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"
