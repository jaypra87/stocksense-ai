"""Identities and sessions: guests, accounts, sign-in, and the guest→account merge.

Every function here runs with the row-level-security bypass, because these are
the flows that legitimately look across users: a login must find a row before
there is a signed-in user, and merging a guest into an account touches two
users' rows. Nothing else in the service layer gets that privilege.
"""

import uuid
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_email, hash_email, normalize_email
from app.core.security import hash_password, session_expiry, verify_password
from app.db.models.alert import Alert
from app.db.models.backtest import Backtest
from app.db.models.session import UserSession
from app.db.models.user import User
from app.db.models.watchlist import WatchlistItem
from app.db.session import rls_bypass


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    """Compared against when the email doesn't exist, so login takes the same
    time for unknown and known emails (no timing-based user enumeration).

    Computed on first use rather than at import: a bcrypt hash at import time
    lands squarely in container cold start, where it delays the port binding on
    small instances. Cached, so only the first unknown-email login pays for it.
    """
    return hash_password("timing-equalization-dummy")


class EmailTakenError(Exception):
    """A user with this email already exists."""


class InvalidCredentialsError(Exception):
    """Email/password did not match."""


class AlreadyRegisteredError(Exception):
    """The caller already has an account; there is nothing to claim."""


# --- lookups ----------------------------------------------------------------


def find_by_email(db: Session, email: str) -> User | None:
    with rls_bypass(db):
        return db.execute(
            select(User).where(User.email_hash == hash_email(email))
        ).scalar_one_or_none()


# --- identities -------------------------------------------------------------


def create_guest(db: Session) -> User:
    with rls_bypass(db):
        user = User(is_guest=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def signup(db: Session, email: str, password: str, guest: User | None = None) -> User:
    """Create an account. When `guest` is given, that guest *becomes* the
    account, keeping its id and therefore its watchlist, alerts and backtests."""
    email = normalize_email(email)
    with rls_bypass(db):
        if find_by_email(db, email) is not None:
            raise EmailTakenError(email)
        if guest is not None and not guest.is_guest:
            raise AlreadyRegisteredError()

        user = guest if guest is not None else User()
        user.email = encrypt_email(email)
        user.email_hash = hash_email(email)
        user.password_hash = hash_password(password)
        user.is_guest = False
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = find_by_email(db, email)
    if user is None or user.password_hash is None:
        verify_password(password, _dummy_hash())  # burn the same bcrypt time
        raise InvalidCredentialsError()
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    return user


def merge_guest_into(db: Session, guest: User, account: User) -> None:
    """Move a guest's saved data onto the account they just signed in to, then
    delete the guest. The guest's sessions go with it (ON DELETE CASCADE)."""
    if not guest.is_guest or guest.id == account.id:
        return
    with rls_bypass(db):
        rows = db.execute(
            select(WatchlistItem.ticker).where(WatchlistItem.user_id == guest.id)
        ).scalars().all()
        for ticker in rows:
            db.execute(
                pg_insert(WatchlistItem)
                .values(user_id=account.id, ticker=ticker)
                .on_conflict_do_nothing(index_elements=["user_id", "ticker"])
            )
        db.execute(update(Alert).where(Alert.user_id == guest.id).values(user_id=account.id))
        db.execute(
            update(Backtest).where(Backtest.user_id == guest.id).values(user_id=account.id)
        )
        db.execute(delete(User).where(User.id == guest.id))
        db.commit()


# --- sessions ---------------------------------------------------------------


def create_session(db: Session, user: User, user_agent: str | None = None) -> UserSession:
    with rls_bypass(db):
        session = UserSession(
            user_id=user.id,
            expires_at=session_expiry(),
            user_agent=(user_agent or "")[:200] or None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session


def revoke_session(db: Session, user: User, session_id: uuid.UUID) -> None:
    with rls_bypass(db):
        db.execute(
            delete(UserSession).where(
                UserSession.id == session_id, UserSession.user_id == user.id
            )
        )
        db.commit()


def revoke_all_sessions(db: Session, user: User) -> int:
    with rls_bypass(db):
        result = db.execute(delete(UserSession).where(UserSession.user_id == user.id))
        db.commit()
        return result.rowcount or 0


def purge_expired(db: Session) -> dict:
    """Housekeeping: drop expired sessions, then guests with no session left.
    A guest with no live session can never come back (there is no password),
    so its rows are unreachable and only take up space."""
    with rls_bypass(db):
        now = datetime.now(UTC)
        sessions = db.execute(delete(UserSession).where(UserSession.expires_at <= now))
        live = select(UserSession.user_id)
        guests = db.execute(
            delete(User).where(User.is_guest.is_(True), User.id.not_in(live))
        )
        db.commit()
        return {"sessions": sessions.rowcount or 0, "guests": guests.rowcount or 0}
