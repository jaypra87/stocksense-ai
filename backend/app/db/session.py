"""Database engine, session factory, and the row-level-security context.

Postgres enforces ownership itself (see the `row_level_security` migration):
every user-owned table has a policy comparing `user_id` to the connection
setting `app.user_id`. A query with no user set sees no rows. That makes the
service-layer ownership checks a first line, not the only line — an IDOR bug
in a handler can no longer return another user's data, because the database
would not hand it over.

The setting is applied with `set_config(..., is_local => true)`, so it lives
and dies with the transaction. SQLAlchemy opens a new transaction after every
commit, and the `after_begin` hook below re-applies the context each time, so
services may commit freely. Transaction-local settings are also what makes
this safe behind a transaction-pooling proxy (Neon's pooler), where a
connection is shared between requests at transaction boundaries.

Two contexts exist:

- `db.info["rls_user_id"]`: the authenticated user; set by `get_current_user`.
- `db.info["rls_bypass"]`:  trusted server-side code that must see across
  users — the auth flows (login looks a user up before there *is* a user), the
  guest→account merge, the alert worker, and the bootstrap/seed scripts. Use
  `system_session()` or the `rls_bypass()` context manager, never set it in
  a request handler to make a query work.
"""

import uuid
from collections.abc import Generator, Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

_SET_USER = text("SELECT set_config('app.user_id', :uid, true)")
_SET_BYPASS = text("SELECT set_config('app.bypass_rls', :on, true)")


def _apply_context(session: Session, connection) -> None:
    """Push the session's RLS context onto the current transaction."""
    user_id = session.info.get("rls_user_id")
    bypass = session.info.get("rls_bypass", False)
    if user_id is not None:
        connection.execute(_SET_USER, {"uid": str(user_id)})
    if bypass:
        connection.execute(_SET_BYPASS, {"on": "on"})


@event.listens_for(SessionLocal, "after_begin")
def _on_begin(session: Session, transaction, connection) -> None:  # noqa: ANN001
    _apply_context(session, connection)


def set_rls_user(session: Session, user_id: uuid.UUID) -> None:
    """Scope every query on this session to one user, for the rest of the
    request. Applied immediately if a transaction is already open."""
    session.info["rls_user_id"] = user_id
    if session.in_transaction():
        session.execute(_SET_USER, {"uid": str(user_id)})


@contextmanager
def rls_bypass(session: Session) -> Iterator[Session]:
    """Temporarily see across users. For trusted server-side flows only."""
    previous = session.info.get("rls_bypass", False)
    session.info["rls_bypass"] = True
    if session.in_transaction():
        session.execute(_SET_BYPASS, {"on": "on"})
    try:
        yield session
    finally:
        session.info["rls_bypass"] = previous
        if not previous and session.in_transaction():
            session.execute(_SET_BYPASS, {"on": "off"})


def system_session() -> Session:
    """A session for code that runs outside any request: workers and scripts."""
    db = SessionLocal()
    db.info["rls_bypass"] = True
    return db


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
