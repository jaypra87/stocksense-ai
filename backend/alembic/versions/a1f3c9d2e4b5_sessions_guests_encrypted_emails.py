"""sessions, guest identities, encrypted emails

Revision ID: a1f3c9d2e4b5
Revises: dd8486bdd6c1
Create Date: 2026-11-10

Three changes that together replace the login wall:

1. `sessions` — a row per sign-in, so a session can be revoked.
2. Guests — `users.email` / `password_hash` become nullable and `is_guest`
   is added, so an identity can exist before (or without) an account.
3. Encrypted emails — `email` now holds AES-GCM ciphertext and the new
   `email_hash` carries the unique index. Existing addresses are re-written
   in place; the migration therefore needs EMAIL_ENCRYPTION_KEY to be the
   key the running app will use.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.core.crypto import encrypt_email, hash_email, is_encrypted

# revision identifiers, used by Alembic.
revision: str = "a1f3c9d2e4b5"
down_revision: str | None = "dd8486bdd6c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"])
    op.create_index(op.f("ix_sessions_expires_at"), "sessions", ["expires_at"])

    op.add_column(
        "users",
        sa.Column("is_guest", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column("users", sa.Column("email_hash", sa.String(length=64), nullable=True))
    op.alter_column("users", "email", type_=sa.String(length=512), nullable=True)
    op.alter_column("users", "password_hash", nullable=True)

    # Re-write every existing address as ciphertext + keyed hash.
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, email FROM users WHERE email IS NOT NULL")).all()
    for user_id, email in rows:
        if is_encrypted(email):
            continue
        conn.execute(
            sa.text("UPDATE users SET email = :enc, email_hash = :h WHERE id = :id"),
            {"enc": encrypt_email(email), "h": hash_email(email), "id": user_id},
        )

    op.drop_index("ix_users_email", table_name="users")
    op.create_index(op.f("ix_users_email_hash"), "users", ["email_hash"], unique=True)


def downgrade() -> None:
    # Decrypting back to plaintext is deliberate on downgrade: the old schema
    # requires it, and a downgrade is an operator's explicit choice.
    from app.core.crypto import decrypt_email

    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM users WHERE is_guest"))
    rows = conn.execute(sa.text("SELECT id, email FROM users WHERE email IS NOT NULL")).all()
    for user_id, email in rows:
        if is_encrypted(email):
            conn.execute(
                sa.text("UPDATE users SET email = :plain WHERE id = :id"),
                {"plain": decrypt_email(email), "id": user_id},
            )
    op.drop_index(op.f("ix_users_email_hash"), table_name="users")
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.alter_column("users", "password_hash", nullable=False)
    op.alter_column("users", "email", type_=sa.String(length=255), nullable=False)
    op.drop_column("users", "email_hash")
    op.drop_column("users", "is_guest")
    op.drop_index(op.f("ix_sessions_expires_at"), table_name="sessions")
    op.drop_index(op.f("ix_sessions_user_id"), table_name="sessions")
    op.drop_table("sessions")
