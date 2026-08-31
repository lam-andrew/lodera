"""create price_bars cache

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-30
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_bars",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=12), nullable=False),
        sa.Column("bar_date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("high", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("low", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("close", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("adj_close", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("ticker", "bar_date", name="uq_price_bar_ticker_date"),
    )
    op.create_index("ix_price_bars_ticker_date", "price_bars", ["ticker", "bar_date"])


def downgrade() -> None:
    op.drop_index("ix_price_bars_ticker_date", table_name="price_bars")
    op.drop_table("price_bars")
