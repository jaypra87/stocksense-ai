"""Shared FastAPI dependencies."""

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_session_token
from app.db.models.session import UserSession
from app.db.models.user import User
from app.db.session import get_db, set_rls_user

_settings = get_settings()

# How often a session's last_seen_at is refreshed. One write per request would
# double the DB traffic of the cheapest endpoints for a timestamp nobody reads
# at that resolution.
_TOUCH_INTERVAL = timedelta(minutes=5)


def _token_from(request: Request) -> str | None:
    """Browsers send the session cookie; API clients may send a Bearer header.
    Both carry the same signed session token."""
    cookie = request.cookies.get(_settings.session_cookie_name)
    if cookie:
        return cookie
    auth = request.headers.get("authorization", "")
    scheme, _, value = auth.partition(" ")
    if scheme.lower() == "bearer" and value.strip():
        return value.strip()
    return None


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """The authenticated user, or None. Never raises for a missing or bad
    token — used by the auth flows, which must work for anonymous callers but
    behave differently for a signed-in guest.

    Also installs the row-level-security context on `db`, so every query the
    handler runs afterwards is scoped to this user by the database itself.
    """
    token = _token_from(request)
    if token is None:
        return None
    decoded = decode_session_token(token)
    if decoded is None:
        return None
    user_id, session_id = decoded

    # Setting the context *before* the lookup is what lets the users/sessions
    # policies ("your own row") admit these two reads.
    set_rls_user(db, user_id)
    session = db.get(UserSession, session_id)
    now = datetime.now(UTC)
    if session is None or session.user_id != user_id or session.expires_at <= now:
        return None
    user = db.get(User, user_id)
    if user is None:
        return None

    if now - session.last_seen_at > _TOUCH_INTERVAL:
        session.last_seen_at = now
        db.commit()
    request.state.session_id = session_id
    return user


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    """The authenticated user, or 401."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not signed in",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
