"""Market-data routes (US-4: retrieve + cache historical prices).

Part of the public API contract. Prices are served through
:class:`~app.data.service.MarketDataService`, so responses come from the local cache when
fresh and only hit the provider otherwise (FR-5, FR-6).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.api.schemas import PriceBarRead, PriceSeriesRead
from app.core.config import settings
from app.core.database import get_session
from app.data.provider import MarketDataError, RateLimitedError, UnknownSymbolError
from app.data.service import MarketDataService, build_provider

router = APIRouter(prefix="/market-data", tags=["market-data"])

SessionDep = Annotated[Session, Depends(get_session)]

# A year of daily bars is a sensible default window for volatility/correlation work.
DEFAULT_LOOKBACK_DAYS = 365


def get_market_data_service(session: SessionDep) -> MarketDataService:
    """Build the cache-aware service, or fail clearly if market data isn't configured."""
    if not settings.market_data_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Market data is not configured. Set APP_MARKET_DATA_API_KEY in .env "
                "(see docs/adr/0011-market-data-provider.md)."
            ),
        )
    return MarketDataService(session, build_provider())


ServiceDep = Annotated[MarketDataService, Depends(get_market_data_service)]


@router.get("/{ticker}/prices", response_model=PriceSeriesRead)
def get_prices(
    ticker: str,
    service: ServiceDep,
    user: CurrentUser,
    days: Annotated[int, Query(ge=1, le=3650)] = DEFAULT_LOOKBACK_DAYS,
) -> PriceSeriesRead:
    """Return daily prices for ``ticker`` over the trailing ``days`` window.

    The first call fetches from the provider and caches the result; subsequent calls within
    the cache TTL are served from PostgreSQL (reported via ``source``).
    """
    end = datetime.now(UTC).date()
    start = end - timedelta(days=days)

    try:
        series = service.get_daily_prices(ticker, start, end)
    except UnknownSymbolError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Unrecognized ticker '{ticker.upper()}'. Check the symbol and try again.",
        ) from exc
    except RateLimitedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Market-data rate limit reached. Please try again shortly.",
        ) from exc
    except MarketDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not retrieve market data: {exc}",
        ) from exc

    dates: list[date] = [bar.date for bar in series.bars]
    return PriceSeriesRead(
        ticker=series.ticker,
        source=series.source,
        count=len(series.bars),
        start=min(dates) if dates else None,
        end=max(dates) if dates else None,
        bars=[
            PriceBarRead(
                date=bar.date,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                adj_close=bar.adj_close,
                volume=bar.volume,
            )
            for bar in series.bars
        ],
    )
