"""A fake market-data provider for tests.

Implements the same :class:`~app.data.provider.MarketDataProvider` interface as Tiingo, so
the suite exercises the real caching/service/route code with no network and no API key.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from app.data.provider import PriceBar, UnknownSymbolError


class FakeProvider:
    """Deterministic bars, plus counters so tests can assert on cache behaviour."""

    def __init__(self, known: set[str] | None = None) -> None:
        self.known = known if known is not None else {"AAPL", "MSFT", "NVDA", "VTI"}
        self.price_calls = 0
        self.symbol_calls = 0

    def get_daily_prices(self, ticker: str, start: date, end: date) -> list[PriceBar]:
        self.price_calls += 1
        if ticker.upper() not in self.known:
            raise UnknownSymbolError(ticker)

        bars: list[PriceBar] = []
        current = start
        price = Decimal("100")
        while current <= end:
            if current.weekday() < 5:  # weekdays only, like a real exchange calendar
                bars.append(
                    PriceBar(
                        date=current,
                        open=price,
                        high=price + Decimal("2"),
                        low=price - Decimal("2"),
                        close=price + Decimal("1"),
                        adj_close=price + Decimal("1"),
                        volume=1_000_000,
                    )
                )
                price += Decimal("0.5")
            current += timedelta(days=1)
        return bars

    def symbol_exists(self, ticker: str) -> bool:
        self.symbol_calls += 1
        return ticker.upper() in self.known
