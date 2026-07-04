"""User signup and authentication."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db.models.user import User

# Compared against when the email doesn't exist, so login takes the same time
# for unknown and known emails (no timing-based user enumeration).
_DUMMY_HASH = hash_password("timing-equalization-dummy")


class EmailTakenError(Exception):
    """A user with this email already exists."""


class InvalidCredentialsError(Exception):
    """Email/password did not match."""


def signup(db: Session, email: str, password: str) -> User:
    email = email.strip().lower()
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        raise EmailTakenError(email)

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    email = email.strip().lower()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None:
        verify_password(password, _DUMMY_HASH)  # burn the same bcrypt time
        raise InvalidCredentialsError()
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    return user
