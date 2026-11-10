"""row level security on user-owned tables

Revision ID: b7e2d8f1c3a6
Revises: a1f3c9d2e4b5
Create Date: 2026-11-10

The app connects as the table owner, and Postgres lets owners through RLS by
default, so every table also gets FORCE ROW LEVEL SECURITY. After this the
service layer's `user_id == current user` checks are backed by the database:
a session with no `app.user_id` set sees nothing, and one set to user A cannot
read or write user B's rows even if a handler asks for them by primary key.

`app.bypass_rls = 'on'` is the escape hatch for trusted server-side code (the
auth flows, the alert worker, the scripts). It is a connection setting, not a
role, because the application is the only principal that holds the database
credentials — a separate role would add ceremony, not a trust boundary. See
app/db/session.py for how both settings are applied per transaction.
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7e2d8f1c3a6"
down_revision: str | None = "a1f3c9d2e4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# table -> SQL predicate identifying "the current user's rows"
OWNED = {
    "users": "id = app_current_user_id()",
    "sessions": "user_id = app_current_user_id()",
    "watchlists": "user_id = app_current_user_id()",
    "alerts": "user_id = app_current_user_id()",
    "backtests": "user_id = app_current_user_id()",
    # No user_id of its own; ownership flows through the parent alert.
    "alert_events": (
        "EXISTS (SELECT 1 FROM alerts a "
        "WHERE a.id = alert_events.alert_id AND a.user_id = app_current_user_id())"
    ),
}


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_current_user_id() RETURNS uuid
        LANGUAGE sql STABLE AS $$
            SELECT NULLIF(current_setting('app.user_id', true), '')::uuid
        $$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_rls_bypass() RETURNS boolean
        LANGUAGE sql STABLE AS $$
            SELECT COALESCE(current_setting('app.bypass_rls', true), '') = 'on'
        $$
        """
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
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute("DROP FUNCTION IF EXISTS app_rls_bypass()")
    op.execute("DROP FUNCTION IF EXISTS app_current_user_id()")
