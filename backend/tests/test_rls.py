"""Row-level security: the database itself refuses other users' rows.

Runs against the real Postgres (migrations applied). The point is to prove the
property *without* going through the service layer, since the service layer is
exactly what RLS is a backstop for.
"""

import uuid

import pytest
from sqlalchemy import select

from app.db.models.alert import Alert
from app.db.models.stock import Stock
from app.db.models.user import User
from app.db.models.watchlist import WatchlistItem
from app.db.session import SessionLocal, rls_bypass, set_rls_user, system_session


@pytest.fixture
def two_users():
    db = system_session()
    a, b = User(is_guest=True), User(is_guest=True)
    db.add_all([a, b])
    db.commit()
    if db.get(Stock, "ZZRLS") is None:
        db.add(Stock(ticker="ZZRLS", company_name="RLS Co"))
    db.add_all([
        WatchlistItem(user_id=a.id, ticker="ZZRLS"),
        Alert(user_id=b.id, ticker="ZZRLS", alert_type="price_above", threshold=1.0),
    ])
    db.commit()
    ids = (a.id, b.id)
    db.close()
    yield ids
    db = system_session()
    db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    db.close()


def test_no_context_sees_nothing(two_users) -> None:
    a, b = two_users
    db = SessionLocal()
    try:
        assert db.execute(select(User).where(User.id.in_([a, b]))).scalars().all() == []
        items = db.execute(select(WatchlistItem).where(WatchlistItem.user_id == a)).scalars().all()
        assert items == []
    finally:
        db.close()


def test_user_context_sees_only_its_own_rows(two_users) -> None:
    a, b = two_users
    db = SessionLocal()
    try:
        set_rls_user(db, a)
        visible = db.execute(select(User.id).where(User.id.in_([a, b]))).scalars().all()
        assert visible == [a]
        assert db.get(WatchlistItem, (a, "ZZRLS")) is not None
        # Asking for B's alert *by primary key* — the IDOR shape — yields nothing.
        b_alert_id = _alert_id_of(b)
        assert db.get(Alert, b_alert_id) is None
    finally:
        db.close()


def test_user_context_cannot_write_rows_for_someone_else(two_users) -> None:
    a, b = two_users
    db = SessionLocal()
    try:
        set_rls_user(db, a)
        db.add(WatchlistItem(user_id=b, ticker="ZZRLS"))
        with pytest.raises(Exception, match="row-level security"):
            db.commit()
    finally:
        db.rollback()
        db.close()


def test_context_survives_a_commit(two_users) -> None:
    """Services commit mid-request; the next transaction must still be scoped."""
    a, _ = two_users
    db = SessionLocal()
    try:
        set_rls_user(db, a)
        assert db.get(User, a) is not None
        db.commit()
        assert db.get(User, a) is not None, "context lost after commit"
    finally:
        db.close()


def test_bypass_is_scoped_to_the_block(two_users) -> None:
    a, b = two_users
    db = SessionLocal()
    try:
        set_rls_user(db, a)
        with rls_bypass(db):
            assert db.get(User, b) is not None
        db.expire_all()
        assert db.get(User, b) is None
    finally:
        db.close()


def _alert_id_of(user_id: uuid.UUID) -> uuid.UUID:
    db = system_session()
    try:
        return db.execute(select(Alert.id).where(Alert.user_id == user_id)).scalar_one()
    finally:
        db.close()
