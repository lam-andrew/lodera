"""Risk routes (US-5: volatility per holding and for the portfolio).

The API layer orchestrates: it loads holdings, pulls cached prices (US-4), aligns the
series, derives weights, and invokes the risk engine. The engine itself stays pure and is
reached only from here, never directly by the frontend (ADR 0004).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.holdings import DEFAULT_PORTFOLIO_NAME
from app.api.market_data import ServiceDep
from app.api.schemas import HoldingRiskRead, PortfolioRiskRead
from app.core.database import get_session
from app.data.provider import MarketDataError
from app.engines.risk import (
    annualized_volatility,
    daily_returns,
    portfolio_volatility,
    volatility_band,
)
from app.models import Holding, Portfolio

router = APIRouter(prefix="/portfolio", tags=["risk"])

SessionDep = Annotated[Session, Depends(get_session)]

#: One year of history is the default estimation window for volatility.
DEFAULT_WINDOW_DAYS = 365


def _as_pct(value: float | None) -> Decimal | None:
    """Convert a decimal fraction (0.187) to a percentage figure (18.70)."""
    if value is None:
        return None
    return Decimal(str(value * 100)).quantize(Decimal("0.01"))


@router.get("/risk", response_model=PortfolioRiskRead)
def get_risk(
    session: SessionDep,
    service: ServiceDep,
    days: Annotated[int, Query(ge=30, le=3650)] = DEFAULT_WINDOW_DAYS,
) -> PortfolioRiskRead:
    """Annualized volatility for each holding and for the portfolio as a whole.

    Per-holding volatility uses each holding's full available history in the window. The
    portfolio figure additionally requires the holdings to be aligned to common trading
    dates, so that the covariance between them is computed over the same days.
    """
    portfolio = session.scalar(select(Portfolio).where(Portfolio.name == DEFAULT_PORTFOLIO_NAME))
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

    # Pull each holding's adjusted-close series (cached where possible).
    series_by_ticker: dict[str, dict[date, Decimal]] = {}
    for holding in holdings:
        try:
            result = service.get_daily_prices(holding.ticker, start, end)
            series_by_ticker[holding.ticker] = {bar.date: bar.adj_close for bar in result.bars}
        except MarketDataError:
            series_by_ticker[holding.ticker] = {}

    # Per-holding volatility and market value.
    rows: list[HoldingRiskRead] = []
    values: dict[str, Decimal] = {}
    for holding in holdings:
        prices_by_date = series_by_ticker[holding.ticker]
        ordered = [prices_by_date[d] for d in sorted(prices_by_date)]
        vol = annualized_volatility(daily_returns(ordered))

        if ordered:
            values[holding.ticker] = ordered[-1] * holding.quantity

        rows.append(
            HoldingRiskRead(
                id=holding.id,
                ticker=holding.ticker,
                volatility_pct=_as_pct(vol),
                band=volatility_band(vol),
                observations=max(len(ordered) - 1, 0),
            )
        )

    # Portfolio volatility over the dates every priced holding shares.
    priced = [t for t in values if series_by_ticker[t]]
    portfolio_vol: float | None = None
    weighted_avg_vol: float | None = None
    common_days = 0

    if priced:
        common: set[date] | None = None
        for ticker in priced:
            dates = set(series_by_ticker[ticker])
            common = dates if common is None else (common & dates)
        aligned_dates = sorted(common or set())
        common_days = max(len(aligned_dates) - 1, 0)

        total_value = sum(values[t] for t in priced)
        if aligned_dates and total_value > 0:
            weights = [float(values[t] / total_value) for t in priced]
            matrix = [
                daily_returns([series_by_ticker[t][d] for d in aligned_dates]) for t in priced
            ]
            portfolio_vol = portfolio_volatility(weights, matrix)

            # The same weights applied to standalone volatilities: the "no diversification"
            # comparison that makes the covariance effect visible. Only meaningful if every
            # holding has enough history to have its own estimate.
            standalone = [annualized_volatility(series) for series in matrix]
            if all(v is not None for v in standalone):
                weighted_avg_vol = sum(
                    weight * vol
                    for weight, vol in zip(weights, standalone, strict=True)
                    if vol is not None
                )

    diversification = None
    if portfolio_vol is not None and weighted_avg_vol is not None:
        diversification = _as_pct(max(weighted_avg_vol - portfolio_vol, 0.0))

    return PortfolioRiskRead(
        holdings=rows,
        portfolio_volatility_pct=_as_pct(portfolio_vol),
        portfolio_band=volatility_band(portfolio_vol),
        undiversified_volatility_pct=_as_pct(weighted_avg_vol),
        diversification_benefit_pct=diversification,
        window_days=days,
        observations=common_days,
    )
