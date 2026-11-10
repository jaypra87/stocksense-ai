"""Identity endpoints.

There is no login wall. A first visit calls POST /auth/guest and gets a
session cookie for a fresh guest identity; everything the user saves hangs off
that id. Signing up later turns the guest into an account in place, and
signing in from a guest browser folds the guest's data into the account.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from redis import Redis
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user
from app.cache.redis_client import get_redis
from app.core.client_ip import client_ip
from app.core.config import get_settings
from app.core.crypto import decrypt_email
from app.core.rate_limit import rate_limit, too_many_requests
from app.core.security import create_session_token
from app.core.turnstile import verify_turnstile
from app.db.models.session import UserSession
from app.db.models.user import User
from app.db.session import get_db, set_rls_user
from app.schemas.auth import GuestRequest, LoginRequest, SessionOut, UserCreate, UserOut
from app.services import auth_service
from app.services.auth_service import (
    AlreadyRegisteredError,
    EmailTakenError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_settings = get_settings()
_login_limiter = rate_limit(
    "login", _settings.login_rate_limit, _settings.login_rate_window_seconds
)
_signup_limiter = rate_limit(
    "signup", _settings.signup_rate_limit, _settings.signup_rate_window_seconds
)
_guest_limiter = rate_limit(
    "guest", _settings.guest_rate_limit, _settings.guest_rate_window_seconds
)


# --- helpers ----------------------------------------------------------------


def user_out(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": decrypt_email(user.email) if user.email else None,
        "is_guest": user.is_guest,
        "preferences": user.preferences,
    }


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_settings.session_cookie_name,
        value=token,
        max_age=_settings.session_ttl_days * 24 * 3600,
        httponly=True,
        secure=_settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=_settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=_settings.cookie_secure,
        samesite="lax",
    )


def _start_session(db: Session, request: Request, response: Response, user: User) -> dict:
    # From here on the request acts as this user: every later query on `db`
    # (including re-loading the user row for the response) is scoped to them.
    set_rls_user(db, user.id)
    session = auth_service.create_session(db, user, request.headers.get("user-agent"))
    token = create_session_token(user.id, session.id, session.expires_at)
    set_session_cookie(response, token)
    return {"access_token": token, "token_type": "bearer", "user": user_out(user)}


def _require_human(request: Request, token: str | None) -> None:
    if not verify_turnstile(token, client_ip(request)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": "Verification failed. Please try again.", "challenge": "turnstile"},
        )


# --- routes -----------------------------------------------------------------


@router.post("/guest", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def guest(
    request: Request,
    response: Response,
    body: GuestRequest | None = None,
    current: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """Start a session. Idempotent for a caller that already has one: it gets
    its existing identity back rather than a second one.

    Per-IP limited; once the allowance is spent, a Turnstile token (when the
    challenge is configured) buys another session. Without Turnstile the limit
    is simply a limit.
    """
    if current is not None:
        return _start_session(db, request, response, current)

    verdict = _guest_limiter.check(redis, client_ip(request))
    if not verdict.allowed:
        token = body.turnstile_token if body else None
        passed = (
            _settings.turnstile_enabled and token and verify_turnstile(token, client_ip(request))
        )
        if not passed:
            raise too_many_requests(verdict.retry_after, challenge=_settings.turnstile_enabled)

    user = auth_service.create_guest(db)
    return _start_session(db, request, response, user)


@router.post(
    "/signup",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_signup_limiter)],
)
def signup(
    body: UserCreate,
    request: Request,
    response: Response,
    current: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    """Create an account, or — for a signed-in guest — save the current guest
    *as* that account, keeping everything it has stored."""
    _require_human(request, body.turnstile_token)
    try:
        user = auth_service.signup(db, body.email, body.password, guest=current)
    except EmailTakenError:
        raise HTTPException(status_code=409, detail="Email already registered") from None
    except AlreadyRegisteredError:
        raise HTTPException(status_code=400, detail="You already have an account") from None
    return _start_session(db, request, response, user)


@router.post("/login", response_model=SessionOut, dependencies=[Depends(_login_limiter)])
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    current: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    _require_human(request, body.turnstile_token)
    try:
        user = auth_service.authenticate(db, body.email, body.password)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password") from None
    # The request arrived scoped to whoever held the cookie (possibly a guest
    # about to be merged away); from here it acts as the account.
    set_rls_user(db, user.id)
    if current is not None and current.is_guest:
        # Whatever the guest saved before signing in comes along.
        auth_service.merge_guest_into(db, current, user)
    elif current is not None:
        sid = getattr(request.state, "session_id", None)
        if sid is not None:
            auth_service.revoke_session(db, current, sid)
    return _start_session(db, request, response, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    sid = getattr(request.state, "session_id", None)
    if sid is not None:
        auth_service.revoke_session(db, user, sid)
    clear_session_cookie(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Revoke every session for this account, this browser's included."""
    auth_service.revoke_all_sessions(db, user)
    clear_session_cookie(response)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> dict:
    return user_out(user)


@router.get("/sessions", response_model=list[dict])
def sessions(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """The account's live sessions (RLS scopes the query to this user)."""
    current = getattr(request.state, "session_id", None)
    rows = db.query(UserSession).filter(UserSession.user_id == user.id).all()
    return [
        {
            "id": str(s.id),
            "current": s.id == current,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
            "user_agent": s.user_agent,
        }
        for s in rows
    ]
