"""Stock-man conversations

Revision ID: e5a7c9d1b3f4
Revises: d4f6a8b0c2e1
Create Date: 2026-11-17

Chat threads and their turns. Turns keep the model API's content blocks
as-is so a thread replays verbatim; ownership reaches the turns through the
conversation, like positions through the portfolio.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5a7c9d1b3f4"
down_revision: str | None = "d4f6a8b0c2e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = sa.text("now()")

OWNED = {
    "conversations": "user_id = app_current_user_id()",
    "conversation_messages": (
        "EXISTS (SELECT 1 FROM conversations c "
        "WHERE c.id = conversation_messages.conversation_id "
        "AND c.user_id = app_current_user_id())"
    ),
}


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"])

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("seq", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_conversation_messages_conversation_id"),
        "conversation_messages",
        ["conversation_id"],
    )
    op.create_index(
        op.f("ix_conversation_messages_seq"), "conversation_messages", ["seq"]
    )

    for table, predicate in OWNED.items():
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_owner ON {table} "
            f"USING (app_rls_bypass() OR ({predicate})) "
            f"WITH CHECK (app_rls_bypass() OR ({predicate}))"
        )


def downgrade() -> None:
    for table in OWNED:
        op.execute(f"DROP POLICY IF EXISTS {table}_owner ON {table}")
    op.drop_table("conversation_messages")
    op.drop_table("conversations")
