"""create price_coverage

Tracks the date range actually requested per symbol so cache completeness can be judged
(see app/models/prices.py::PriceCoverageRow).

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_coverage",
        sa.Column("ticker", sa.String(length=12), primary_key=True),
        sa.Column("covered_start", sa.Date(), nullable=False),
        sa.Column("covered_end", sa.Date(), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("price_coverage")
