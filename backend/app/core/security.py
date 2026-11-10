"""Password hashing (bcrypt) and session tokens (JWT).

Kept dependency-light: bcrypt directly (no passlib), PyJWT for tokens.

A session token names a row in the `sessions` table (`sid`) as well as the user
(`sub`). The signature proves the server issued it; the row is what makes it
revocable — logging out deletes the row, and a signed token for a missing row
is rejected. The JWT's own expiry is only the outer bound.
"""

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()


def hash_password(plain: str) -> str:
    """Hash at the configured work factor (see Settings.bcrypt_rounds)."""
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    return bcrypt.hashpw(plain.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False


def create_session_token(user_id: uuid.UUID, session_id: uuid.UUID, expires_at: datetime) -> str:
    payload = {
        "sub": str(user_id),
        "sid": str(session_id),
        "iat": datetime.now(UTC),
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_session_token(token: str) -> tuple[uuid.UUID, uuid.UUID] | None:
    """Return (user_id, session_id) if the token is validly signed and unexpired."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return uuid.UUID(payload["sub"]), uuid.UUID(payload["sid"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None


def session_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.session_ttl_days)


# --- backwards-compatible names used by older tests/scripts ---------------


def create_access_token(subject: str) -> str:
    """Bare user-token without a session row. Kept for scripts that only need a
    signed subject; the API itself only honours session tokens."""
    now = datetime.now(UTC)
    payload = {"sub": subject, "iat": now, "exp": now + timedelta(hours=1)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    return payload.get("sub")
