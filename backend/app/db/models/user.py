import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """An identity. Every visitor gets one silently (a *guest*); attaching an
    email and password turns it into an account that works on other devices.

    `email` is AES-GCM ciphertext and `email_hash` a keyed hash of the
    normalised address (see app/core/crypto.py). Code never queries `email`;
    lookups and the uniqueness constraint go through `email_hash`. Both are
    null for guests, as is `password_hash`.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
