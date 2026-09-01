"""Shared loading and alignment of portfolio return series.

Both the volatility (US-5) and correlation (US-6) endpoints need the same thing: each
holding's adjusted-close history, restricted to the trading dates every holding shares, and
turned into daily returns. Alignment matters — covariance and correlation between two series
are only meaningful when each pair of observations comes from the same day — so it is done
once here rather than reimplemented per endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.data.provider import MarketDataError
from app.data.service import MarketDataService
from app.engines.risk import daily_returns
from app.models import Holding, Portfolio


@dataclass
class PortfolioSeries:
    """Per-holding price history plus the aligned return matrix."""

    holdings: list[Holding] = field(default_factory=list)
    #: ticker -> {date: adjusted close}. Empty dict when the holding could not be priced.
    prices: dict[str, dict[date, Decimal]] = field(default_factory=dict)
    #: Tickers that have price data, in the order of ``matrix``.
    priced_tickers: list[str] = field(default_factory=list)
    #: ``matrix[i]`` is the aligned daily-return series for ``priced_tickers[i]``.
    matrix: list[list[float]] = field(default_factory=list)
    #: Latest market value per priced ticker, used for weighting.
    values: dict[str, Decimal] = field(default_factory=dict)
    #: Number of shared daily returns backing the aligned matrix.
    observations: int = 0

    def value_series(self) -> tuple[list[date], list[Decimal]]:
        """Portfolio market value per shared trading day, at today's share quantities.

        Used by the value sparkline (US-10) and by drawdown (US-8). Only dates every priced
        holding shares are included, so a point is never a partial sum of the portfolio.
        """
        if not self.priced_tickers:
            return [], []

        quantities = {h.ticker: h.quantity for h in self.holdings}
        common: set[date] | None = None
        for ticker in self.priced_tickers:
            dates = set(self.prices[ticker])
            common = dates if common is None else (common & dates)

        ordered = sorted(common or set())
        values = [
            sum(
                (self.prices[t][day] * quantities[t] for t in self.priced_tickers),
                Decimal("0"),
            )
            for day in ordered
        ]
        return ordered, values

    def full_series(self, ticker: str) -> list[Decimal]:
        """One holding's complete price history in date order (not date-aligned)."""
        by_date = self.prices.get(ticker, {})
        return [by_date[d] for d in sorted(by_date)]


def load_portfolio_series(
    session: Session, service: MarketDataService, *, user_id: int, days: int
) -> PortfolioSeries:
    """Load holdings and their price history, and align returns to common trading dates."""
    portfolio = session.scalar(select(Portfolio).where(Portfolio.user_id == user_id))
    holdings: list[Holding] = (
        []
        if portfolio is None
        else list(
            session.scalars(
                select(Holding).where(Holding.portfolio_id == portfolio.id).order_by(Holding.ticker)
            )
        )
    )

    end = datetime.now(UTC).date()
    start = end - timedelta(days=days)

    result = PortfolioSeries(holdings=holdings)
    for holding in holdings:
        try:
            series = service.get_daily_prices(holding.ticker, start, end)
            result.prices[holding.ticker] = {bar.date: bar.adj_close for bar in series.bars}
        except MarketDataError:
            # A holding we cannot price is still reported by callers, just without figures.
            result.prices[holding.ticker] = {}

    priced = [h.ticker for h in holdings if result.prices.get(h.ticker)]
    for ticker in priced:
        ordered = result.full_series(ticker)
        result.values[ticker] = ordered[-1] * next(
            h.quantity for h in holdings if h.ticker == ticker
        )

    if priced:
        common: set[date] | None = None
        for ticker in priced:
            dates = set(result.prices[ticker])
            common = dates if common is None else (common & dates)
        aligned_dates = sorted(common or set())
        result.observations = max(len(aligned_dates) - 1, 0)
        if aligned_dates:
            result.priced_tickers = priced
            result.matrix = [
                daily_returns([result.prices[t][d] for d in aligned_dates]) for t in priced
            ]

    return result
