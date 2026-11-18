"""The daily digest: a short note on the user's paper portfolio, written by
Stock-man from the same tools the chat uses.

There is no scheduler on the public deployment, so the digest is written by
the first dashboard visit of the day and cached as a row. A short Redis lock
stops two tabs from paying for the same digest; the unique (user, day) key
is the backstop if the lock is ever lost.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import anthropic
    from anthropic.types import MessageParam
from redis import Redis, RedisError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.digest import Digest
from app.services import portfolio_service, watchlist_service
from app.services.market_data.base import MarketDataProvider
from app.services.stockman import grounding, tools
from app.services.stockman.prompts import DIGEST_SYSTEM
from app.services.stockman.tools import ToolContext, ToolError

logger = logging.getLogger(__name__)

MAX_POSITIONS = 6
MAX_FORECASTS = 3
MAX_OUTPUT_TOKENS = 700
_LOCK_SECONDS = 90
# With nothing in the portfolio or the watchlist, the digest covers the market.
_DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "SPY"]


class DigestBusy(Exception):
    """Another request is writing today's digest right now."""


def today(db: Session, user_id: uuid.UUID) -> dict | None:
    row = db.execute(
        select(Digest).where(Digest.user_id == user_id, Digest.for_date == _day())
    ).scalar_one_or_none()
    return _out(row) if row is not None else None


def generate(
    db: Session,
    redis: Redis,
    provider: MarketDataProvider,
    client: anthropic.Anthropic,
    user_id: uuid.UUID,
    force: bool = False,
) -> dict:
    existing = today(db, user_id)
    if existing is not None and not force:
        return existing

    lock = f"stockman:digest:lock:{user_id}:{_day()}"
    if not _acquire(redis, lock):
        raise DigestBusy()
    try:
        context, sources, mode = _gather(ToolContext(db, redis, provider, user_id))
        settings = get_settings()
        response = client.messages.create(
            model=settings.stockman_model,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=[
                {"type": "text", "text": DIGEST_SYSTEM, "cache_control": {"type": "ephemeral"}}
            ],
            output_config={"effort": "low"},
            messages=[_prompt(context, mode)],
        )
        body = "".join(b.text for b in response.content if b.type == "text").strip()
        if response.stop_reason == "refusal" or not body:
            body = (
                "Stock-man couldn't write a digest today. "
                "The numbers are still on the portfolio page."
            )

        row = db.execute(
            select(Digest).where(Digest.user_id == user_id, Digest.for_date == _day())
        ).scalar_one_or_none()
        if row is None:
            row = Digest(user_id=user_id, for_date=_day())
            db.add(row)
        row.mode = mode
        row.body = body
        row.sources = sources
        row.grounding = grounding.check(body, context.values())
        row.model = settings.stockman_model
        row.input_tokens = response.usage.input_tokens
        row.output_tokens = response.usage.output_tokens
        row.created_at = datetime.now(UTC)
        db.commit()
        db.refresh(row)
        return _out(row)
    finally:
        _release(redis, lock)


def _gather(ctx: ToolContext) -> tuple[dict, list[dict], str]:
    """Pull what the digest is allowed to talk about. Tools that fail are
    recorded as unavailable rather than dropped, so the model can say so."""
    context: dict = {}
    sources: list[dict] = []

    def call(name: str, args: dict, key: str) -> None:
        try:
            context[key] = tools.run(ctx, name, args)
            sources.append(
                {"tool": name, **({"ticker": args["ticker"]} if "ticker" in args else {})}
            )
        except ToolError as exc:
            context[key] = {"unavailable": str(exc)}

    summary = portfolio_service.summary(ctx.db, ctx.redis, ctx.provider, ctx.user_id)
    positions = sorted(summary["positions"], key=lambda p: p["weight"], reverse=True)
    if positions:
        mode = "portfolio"
        call("get_portfolio", {}, "portfolio")
        tickers = [p["ticker"] for p in positions[:MAX_POSITIONS]]
    else:
        mode = "market"
        saved = [w["ticker"] for w in watchlist_service.list_watchlist(ctx.db, ctx.user_id)]
        tickers = (saved or _DEFAULT_TICKERS)[:4]
        context["portfolio"] = {"cash": summary["cash"], "positions": []}

    for i, ticker in enumerate(tickers):
        call("get_risk", {"ticker": ticker}, f"risk:{ticker}")
        call("get_sentiment", {"ticker": ticker}, f"sentiment:{ticker}")
        if i < MAX_FORECASTS:
            call("get_forecast", {"ticker": ticker, "horizon": "7d"}, f"forecast:{ticker}")
    return context, sources, mode


def _prompt(context: dict, mode: str) -> MessageParam:
    lead = (
        "Write today's digest for this paper portfolio."
        if mode == "portfolio"
        else "The portfolio holds only cash. Write today's digest on these tickers instead, "
        "and mention in one clause that the account is uninvested."
    )
    message: MessageParam = {
        "role": "user",
        "content": (
            f"{lead}\n\nDate: {_day().isoformat()}\n\nData:\n{json.dumps(context, default=str)}"
        ),
    }
    return message


def _acquire(redis: Redis, key: str) -> bool:
    try:
        return bool(redis.set(key, "1", nx=True, ex=_LOCK_SECONDS))
    except RedisError as exc:
        logger.warning("digest lock unavailable (%s); proceeding without it", exc)
        return True


def _release(redis: Redis, key: str) -> None:
    try:
        redis.delete(key)
    except RedisError:
        pass


def _day() -> date:
    return datetime.now(UTC).date()


def _out(row: Digest) -> dict:
    return {
        "available": True,
        "for_date": row.for_date.isoformat(),
        "mode": row.mode,
        "body": row.body,
        "sources": row.sources,
        "grounding": row.grounding,
        "generated_at": row.created_at.isoformat() if row.created_at else None,
    }
