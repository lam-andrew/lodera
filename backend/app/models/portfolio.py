"""Portfolio and holding models.

A ``Portfolio`` owns many ``Holding`` rows (ticker + share quantity). For the MVP there is
a single default portfolio (no auth yet; user scoping arrives with US-13). The unique
constraint keeps one row per ticker per portfolio, so adding a ticker that already exists is
rejected (edit it instead — US-3).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    holdings: Mapped[list[Holding]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
        order_by="Holding.ticker",
    )


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "ticker", name="uq_holding_portfolio_ticker"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"), index=True, nullable=False
    )
    ticker: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    # Numeric keeps exact precision and supports fractional shares.
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    portfolio: Mapped[Portfolio] = relationship(back_populates="holdings")
