"""Cache-aware market-data access (US-4: FR-5 retrieve, FR-6 cache).

Reads go through :class:`MarketDataService`, which serves daily bars from the PostgreSQL
cache when they are fresh and only calls the provider otherwise. That satisfies FR-6, keeps
us inside the provider's free tier, and keeps the network off the analysis path.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.data.provider import MarketDataError, MarketDataProvider, PriceBar
from app.data.tiingo import TiingoProvider
from app.models.prices import PriceBarRow, PriceCoverageRow

Source = Literal["cache", "provider"]

#: One lock per ticker, so concurrent requests for the same symbol fetch it once.
#:
#: The dashboard fires five endpoints at once and each needs prices for every holding. With
#: a cold cache they all missed together, all called the provider, and then collided
#: inserting identical (ticker, date) rows — a unique-constraint violation that surfaced as
#: HTTP 500. Serializing per ticker fixes the collision and cuts provider requests by the
#: number of concurrent callers, which matters against a 50-requests-per-hour free tier.
#:
#: Endpoints are sync, so FastAPI runs them in a threadpool and a threading lock is the right
#: primitive. This is per-process: it does not coordinate across replicas, which is fine
#: because the database constraint remains the real guarantee (see _store).
_fetch_locks: defaultdict[str, threading.Lock] = defaultdict(threading.Lock)
_locks_guard = threading.Lock()


def _lock_for(ticker: str) -> threading.Lock:
    """The lock guarding provider fetches for one symbol."""
    with _locks_guard:
        return _fetch_locks[ticker]


@dataclass(frozen=True, slots=True)
class PriceSeries:
    """Daily bars for one symbol, plus where they came from.

    ``source`` makes caching observable (and testable): the second identical request should
    report ``"cache"``.
    """

    ticker: str
    bars: list[PriceBar]
    source: Source


def build_provider() -> MarketDataProvider:
    """Construct the configured provider (ADR 0011). Raises if it isn't usable."""
    name = settings.market_data_provider.strip().lower()
    if name == "tiingo":
        return TiingoProvider(settings.market_data_api_key)
    raise MarketDataError(f"Unknown market-data provider {name!r}.")


class MarketDataService:
    def __init__(
        self,
        session: Session,
        provider: MarketDataProvider,
        *,
        ttl_hours: int | None = None,
    ) -> None:
        self._session = session
        self._provider = provider
        self._ttl = timedelta(
            hours=settings.market_data_cache_ttl_hours if ttl_hours is None else ttl_hours
        )

    def _cached_rows(self, ticker: str, start: date, end: date) -> list[PriceBarRow]:
        return list(
            self._session.scalars(
                select(PriceBarRow)
                .where(
                    PriceBarRow.ticker == ticker,
                    PriceBarRow.bar_date >= start,
                    PriceBarRow.bar_date <= end,
                )
                .order_by(PriceBarRow.bar_date)
            )
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Normalize to an aware UTC datetime.

        Backends differ: PostgreSQL returns timezone-aware values while SQLite returns naive
        ones, and rows written by the server-side default can differ from ones we set in
        Python. Normalizing every value before comparing avoids mixing the two (which raises).
        """
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    def _coverage(self, ticker: str) -> PriceCoverageRow | None:
        return self._session.get(PriceCoverageRow, ticker)

    def _is_usable(self, ticker: str, start: date, end: date) -> bool:
        """Whether the cache can answer this request.

        Two conditions, both required. **Freshness**: the data was fetched within the TTL.
        **Coverage**: we have previously requested a window at least as wide as this one —
        otherwise a narrow earlier fetch (say 10 days) would silently answer a 365-day
        request with 10 days of data, quietly corrupting anything computed from it.
        """
        coverage = self._coverage(ticker)
        if coverage is None:
            return False
        if coverage.covered_start > start or coverage.covered_end < end:
            return False
        return datetime.now(UTC) - self._as_utc(coverage.fetched_at) < self._ttl

    @staticmethod
    def _to_bar(row: PriceBarRow) -> PriceBar:
        return PriceBar(
            date=row.bar_date,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            adj_close=row.adj_close,
            volume=row.volume,
        )

    def _store(self, ticker: str, start: date, end: date, bars: list[PriceBar]) -> None:
        """Replace the cached window for this ticker with freshly fetched bars."""
        self._session.execute(
            delete(PriceBarRow).where(
                PriceBarRow.ticker == ticker,
                PriceBarRow.bar_date >= start,
                PriceBarRow.bar_date <= end,
            )
        )
        now = datetime.now(UTC)
        # Record the window we asked for, widening any window already recorded.
        coverage = self._coverage(ticker)
        if coverage is None:
            self._session.add(
                PriceCoverageRow(
                    ticker=ticker, covered_start=start, covered_end=end, fetched_at=now
                )
            )
        else:
            coverage.covered_start = min(coverage.covered_start, start)
            coverage.covered_end = max(coverage.covered_end, end)
            coverage.fetched_at = now
        self._session.add_all(
            [
                PriceBarRow(
                    ticker=ticker,
                    bar_date=bar.date,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    adj_close=bar.adj_close,
                    volume=bar.volume,
                    fetched_at=now,
                )
                for bar in bars
            ]
        )
        try:
            self._session.commit()
        except IntegrityError:
            # Another process wrote these bars between our delete and our insert. The rows
            # we wanted are now present, so discard our copy rather than failing the request.
            self._session.rollback()

    def get_daily_prices(self, ticker: str, start: date, end: date) -> PriceSeries:
        """Return daily bars for ``ticker``, from cache when fresh, else from the provider.

        If the provider call fails but stale cached data exists, the cached data is returned
        rather than failing outright — analysis degrades gracefully instead of breaking.
        """
        symbol = ticker.strip().upper()
        if self._is_usable(symbol, start, end):
            cached = self._cached_rows(symbol, start, end)
            return PriceSeries(symbol, [self._to_bar(r) for r in cached], "cache")

        with _lock_for(symbol):
            # Re-check inside the lock: while we waited, a concurrent request for the same
            # symbol may already have fetched and cached exactly this window.
            self._session.expire_all()
            if self._is_usable(symbol, start, end):
                cached = self._cached_rows(symbol, start, end)
                return PriceSeries(symbol, [self._to_bar(r) for r in cached], "cache")

            cached = self._cached_rows(symbol, start, end)
            try:
                bars = self._provider.get_daily_prices(symbol, start, end)
            except MarketDataError:
                if cached:
                    return PriceSeries(symbol, [self._to_bar(r) for r in cached], "cache")
                raise

            self._store(symbol, start, end, bars)
            return PriceSeries(symbol, bars, "provider")
