"""Portfolio summary routes.

Joins holdings (US-1/US-3) with cached market data (US-4) to report each position's latest
price and market value, plus the portfolio total. This is the first place the two halves
meet; risk metrics land here as their stories arrive (US-5 onward).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api._portfolio_series import load_portfolio_series
from app.api.holdings import DEFAULT_PORTFOLIO_NAME
from app.api.market_data import ServiceDep
from app.api.schemas import (
    PortfolioHistoryRead,
    PortfolioSummaryRead,
    PortfolioValuePointRead,
    PositionRead,
)
from app.core.database import get_session
from app.data.provider import MarketDataError
from app.models import Holding, Portfolio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

SessionDep = Annotated[Session, Depends(get_session)]

# Enough trailing days to land on a recent trading day across weekends and holidays.
_PRICE_LOOKBACK_DAYS = 10


@router.get("/summary", response_model=PortfolioSummaryRead)
def get_summary(session: SessionDep, service: ServiceDep) -> PortfolioSummaryRead:
    """Return each holding with its latest close and market value, plus the total.

    A position whose price cannot be retrieved is still listed, with nulls, so one bad
    symbol or a provider hiccup never hides the rest of the portfolio.
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
    start = end - timedelta(days=_PRICE_LOOKBACK_DAYS)

    positions: list[PositionRead] = []
    total = Decimal("0")
    priced_any = False

    for holding in holdings:
        latest_price: Decimal | None = None
        as_of = None
        try:
            series = service.get_daily_prices(holding.ticker, start, end)
            if series.bars:
                latest = series.bars[-1]
                latest_price = latest.adj_close
                as_of = latest.date
        except MarketDataError:
            latest_price = None  # listed without a price rather than failing the request

        market_value = None
        if latest_price is not None:
            market_value = (latest_price * holding.quantity).quantize(Decimal("0.01"))
            total += market_value
            priced_any = True

        positions.append(
            PositionRead(
                id=holding.id,
                ticker=holding.ticker,
                quantity=holding.quantity,
                latest_price=latest_price,
                market_value=market_value,
                price_as_of=as_of,
            )
        )

    # Weights are only meaningful once something is priced.
    if priced_any and total > 0:
        for position in positions:
            if position.market_value is not None:
                position.weight_pct = (position.market_value / total * 100).quantize(
                    Decimal("0.01")
                )

    return PortfolioSummaryRead(
        positions=positions,
        total_value=total.quantize(Decimal("0.01")) if priced_any else None,
        priced=priced_any,
    )


@router.get("/history", response_model=PortfolioHistoryRead)
def get_history(
    session: SessionDep,
    service: ServiceDep,
    days: Annotated[int, Query(ge=30, le=3650)] = 365,
) -> PortfolioHistoryRead:
    """Portfolio market value over time, at today's share quantities.

    Each point is ``sum(adjusted_close * quantity)`` across holdings on a shared trading
    day. Holding quantities are held constant at their current values, so the series shows
    how *this* portfolio would have moved — it is not a record of past trading activity.
    """
    data = load_portfolio_series(session, service, days=days)

    if not data.priced_tickers:
        return PortfolioHistoryRead(points=[], start=None, end=None)

    quantities = {h.ticker: h.quantity for h in data.holdings}

    # Only dates every priced holding shares, so the total is never a partial sum.
    common: set[date] | None = None
    for ticker in data.priced_tickers:
        dates = set(data.prices[ticker])
        common = dates if common is None else (common & dates)

    points = [
        PortfolioValuePointRead(
            date=day,
            # Decimal start value: sum() returns int 0 on an empty iterable.
            value=sum(
                (data.prices[t][day] * quantities[t] for t in data.priced_tickers),
                Decimal("0"),
            ).quantize(Decimal("0.01")),
        )
        for day in sorted(common or set())
    ]

    return PortfolioHistoryRead(
        points=points,
        start=points[0].date if points else None,
        end=points[-1].date if points else None,
    )
