"""Cache-aware market-data access (US-4: FR-5 retrieve, FR-6 cache).

Reads go through :class:`MarketDataService`, which serves daily bars from the PostgreSQL
cache when they are fresh and only calls the provider otherwise. That satisfies FR-6, keeps
us inside the provider's free tier, and keeps the network off the analysis path.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.data.provider import MarketDataError, MarketDataProvider, PriceBar
from app.data.tiingo import TiingoProvider
from app.models.prices import PriceBarRow

Source = Literal["cache", "provider"]


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

    def _is_fresh(self, rows: list[PriceBarRow]) -> bool:
        if not rows:
            return False
        newest = max(self._as_utc(row.fetched_at) for row in rows)
        return datetime.now(UTC) - newest < self._ttl

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
        self._session.commit()

    def get_daily_prices(self, ticker: str, start: date, end: date) -> PriceSeries:
        """Return daily bars for ``ticker``, from cache when fresh, else from the provider.

        If the provider call fails but stale cached data exists, the cached data is returned
        rather than failing outright — analysis degrades gracefully instead of breaking.
        """
        symbol = ticker.strip().upper()
        cached = self._cached_rows(symbol, start, end)
        if self._is_fresh(cached):
            return PriceSeries(symbol, [self._to_bar(r) for r in cached], "cache")

        try:
            bars = self._provider.get_daily_prices(symbol, start, end)
        except MarketDataError:
            if cached:
                return PriceSeries(symbol, [self._to_bar(r) for r in cached], "cache")
            raise

        self._store(symbol, start, end, bars)
        return PriceSeries(symbol, bars, "provider")
