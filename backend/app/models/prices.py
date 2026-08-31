"""Cached market-data prices (FR-6).

Daily bars retrieved from the market-data provider are stored here so repeated analysis
reads from PostgreSQL instead of re-fetching. This respects the provider's free-tier rate
limits and keeps the network off the analysis path, which makes demos fast and repeatable.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PriceBarRow(Base):
    """One cached daily bar for one symbol."""

    __tablename__ = "price_bars"
    __table_args__ = (
        UniqueConstraint("ticker", "bar_date", name="uq_price_bar_ticker_date"),
        Index("ix_price_bars_ticker_date", "ticker", "bar_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(12), nullable=False)
    bar_date: Mapped[date] = mapped_column(Date, nullable=False)

    open: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    # Split/dividend adjusted close — the series risk math uses.
    adj_close: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    volume: Mapped[int] = mapped_column(nullable=False, default=0)

    # When this row was retrieved; drives cache freshness (TTL).
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
