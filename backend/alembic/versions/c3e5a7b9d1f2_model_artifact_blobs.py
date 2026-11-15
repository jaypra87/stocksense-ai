"""store model bundles in the database

Revision ID: c3e5a7b9d1f2
Revises: b7e2d8f1c3a6
Create Date: 2026-11-15

The trained bundles used to live only on the container's disk. The free
hosting tier replaces that disk on every wake, so each cold start spent
several minutes retraining while the 7d/30d forecasts returned errors.
`blob` keeps the serialized bundle next to its registry row so a fresh
container restores it in seconds instead of retraining.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3e5a7b9d1f2"
down_revision: str | None = "b7e2d8f1c3a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("model_artifacts", sa.Column("blob", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("model_artifacts", "blob")
