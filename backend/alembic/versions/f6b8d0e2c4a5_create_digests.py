"""daily portfolio digests

Revision ID: f6b8d0e2c4a5
Revises: e5a7c9d1b3f4
Create Date: 2026-11-17

One row per user per day. Written on demand by the first dashboard visit of
the day, because the public deployment has no scheduler; the unique key is
what makes "once a day" hold under concurrent visits.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6b8d0e2c4a5"
down_revision: str | None = "e5a7c9d1b3f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "digests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("for_date", sa.Date(), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("grounding", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("model", sa.String(length=60), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "for_date", name="uq_digests_day"),
    )
    op.create_index(op.f("ix_digests_user_id"), "digests", ["user_id"])
    op.execute("ALTER TABLE digests ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE digests FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY digests_owner ON digests "
        "USING (app_rls_bypass() OR (user_id = app_current_user_id())) "
        "WITH CHECK (app_rls_bypass() OR (user_id = app_current_user_id()))"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS digests_owner ON digests")
    op.drop_table("digests")
