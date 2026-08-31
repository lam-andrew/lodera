"""Risk routes (US-5 volatility, US-6 correlation).

The API layer orchestrates: it loads holdings, pulls cached prices (US-4), aligns the series
(:mod:`app.api._portfolio_series`), derives weights, and invokes the risk engine. The engine
itself stays pure and is reached only from here, never directly by the frontend (ADR 0004).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api._portfolio_series import load_portfolio_series
from app.api.market_data import ServiceDep
from app.api.schemas import (
    CorrelationPairRead,
    HoldingRiskRead,
    PortfolioCorrelationRead,
    PortfolioRiskRead,
)
from app.core.database import get_session
from app.engines.risk import (
    HIGH_CORRELATION,
    LOW_CORRELATION,
    annualized_volatility,
    average_correlation,
    correlation_matrix,
    daily_returns,
    least_correlated,
    most_correlated,
    portfolio_volatility,
    volatility_band,
)

router = APIRouter(prefix="/portfolio", tags=["risk"])

SessionDep = Annotated[Session, Depends(get_session)]

#: One year of history is the default estimation window.
DEFAULT_WINDOW_DAYS = 365


def _as_pct(value: float | None) -> Decimal | None:
    """Convert a decimal fraction (0.187) to a percentage figure (18.70)."""
    if value is None:
        return None
    return Decimal(str(value * 100)).quantize(Decimal("0.01"))


def _round(value: float | None) -> Decimal | None:
    """Round a correlation to two places for display."""
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"))


@router.get("/risk", response_model=PortfolioRiskRead)
def get_risk(
    session: SessionDep,
    service: ServiceDep,
    days: Annotated[int, Query(ge=30, le=3650)] = DEFAULT_WINDOW_DAYS,
) -> PortfolioRiskRead:
    """Annualized volatility for each holding and for the portfolio as a whole.

    Per-holding volatility uses each holding's full available history in the window. The
    portfolio figure additionally requires the holdings to be aligned to common trading
    dates, so the covariance between them is computed over the same days.
    """
    data = load_portfolio_series(session, service, days=days)

    rows = [
        HoldingRiskRead(
            id=holding.id,
            ticker=holding.ticker,
            volatility_pct=_as_pct(
                vol := annualized_volatility(daily_returns(data.full_series(holding.ticker)))
            ),
            band=volatility_band(vol),
            observations=max(len(data.full_series(holding.ticker)) - 1, 0),
        )
        for holding in data.holdings
    ]

    portfolio_vol: float | None = None
    weighted_avg_vol: float | None = None

    if data.matrix:
        total_value = sum(data.values[t] for t in data.priced_tickers)
        if total_value > 0:
            weights = [float(data.values[t] / total_value) for t in data.priced_tickers]
            portfolio_vol = portfolio_volatility(weights, data.matrix)

            # The same weights applied to standalone volatilities: the "no diversification"
            # comparison that makes the covariance effect visible.
            standalone = [annualized_volatility(series) for series in data.matrix]
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
        observations=data.observations,
    )


@router.get("/correlation", response_model=PortfolioCorrelationRead)
def get_correlation(
    session: SessionDep,
    service: ServiceDep,
    days: Annotated[int, Query(ge=30, le=3650)] = DEFAULT_WINDOW_DAYS,
) -> PortfolioCorrelationRead:
    """Correlation structure among the portfolio's holdings (US-6).

    Alongside the matrix we return the most- and least-correlated pairs, because the raw
    grid answers "what are the numbers" while the pairs answer the question the user
    actually has: where is the hidden concentration, and what is actually diversifying.
    """
    data = load_portfolio_series(session, service, days=days)
    matrix = correlation_matrix(data.matrix) if data.matrix else None

    if matrix is None:
        return PortfolioCorrelationRead(
            tickers=[],
            matrix=[],
            most_correlated=[],
            least_correlated=[],
            average_correlation=None,
            window_days=days,
            observations=data.observations,
            high_threshold=_round(HIGH_CORRELATION),
            low_threshold=_round(LOW_CORRELATION),
        )

    tickers = data.priced_tickers
    return PortfolioCorrelationRead(
        tickers=tickers,
        matrix=[[_round(value) for value in row] for row in matrix],
        most_correlated=[
            CorrelationPairRead(a=p.a, b=p.b, correlation=_round(p.correlation) or Decimal(0))
            for p in most_correlated(tickers, matrix)
        ],
        least_correlated=[
            CorrelationPairRead(a=p.a, b=p.b, correlation=_round(p.correlation) or Decimal(0))
            for p in least_correlated(tickers, matrix)
        ],
        average_correlation=_round(average_correlation(tickers, matrix)),
        window_days=days,
        observations=data.observations,
        high_threshold=_round(HIGH_CORRELATION),
        low_threshold=_round(LOW_CORRELATION),
    )
