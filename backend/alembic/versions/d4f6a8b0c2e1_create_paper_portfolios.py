"""paper portfolios, positions and the trade ledger

Revision ID: d4f6a8b0c2e1
Revises: c3e5a7b9d1f2
Create Date: 2026-11-17

One portfolio per user, holding cash. Positions and trades belong to the
portfolio rather than the user directly, so their row-level-security policy
reaches ownership through the parent, the same shape as alert_events.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4f6a8b0c2e1"
down_revision: str | None = "c3e5a7b9d1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOW = sa.text("now()")
_MONEY = sa.Numeric(18, 4)
_SHARES = sa.Numeric(20, 6)

_VIA_PORTFOLIO = (
    "EXISTS (SELECT 1 FROM portfolios p "
    "WHERE p.id = {table}.portfolio_id AND p.user_id = app_current_user_id())"
)

OWNED = {
    "portfolios": "user_id = app_current_user_id()",
    "positions": _VIA_PORTFOLIO.format(table="positions"),
    "trades": _VIA_PORTFOLIO.format(table="trades"),
}


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("cash", _MONEY, nullable=False),
        sa.Column("starting_cash", _MONEY, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "positions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("quantity", _SHARES, nullable=False),
        sa.Column("avg_cost", _MONEY, nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ticker"], ["stocks.ticker"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portfolio_id", "ticker", name="uq_positions_ticker"),
    )
    op.create_index(op.f("ix_positions_portfolio_id"), "positions", ["portfolio_id"])

    op.create_table(
        "trades",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("side", sa.String(length=4), nullable=False),
        sa.Column("quantity", _SHARES, nullable=False),
        sa.Column("price", _MONEY, nullable=False),
        sa.Column("realized_pnl", _MONEY, nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=_NOW, nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trades_portfolio_id"), "trades", ["portfolio_id"])
    op.create_index(op.f("ix_trades_ticker"), "trades", ["ticker"])
    op.create_index(op.f("ix_trades_executed_at"), "trades", ["executed_at"])

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
    op.drop_table("trades")
    op.drop_table("positions")
    op.drop_table("portfolios")
