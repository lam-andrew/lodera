"""A fake market-data provider for tests.

Implements the same :class:`~app.data.provider.MarketDataProvider` interface as Tiingo, so
the suite exercises the real caching/service/route code with no network and no API key.

Each ticker gets its own deterministic pseudo-random walk (seeded by the symbol), so
different holdings have genuinely different volatilities and are not perfectly correlated —
which is what makes portfolio-level risk assertions meaningful.
"""

from __future__ import annotations

import zlib
from datetime import date, timedelta
from decimal import Decimal

import numpy as np

from app.data.provider import PriceBar, UnknownSymbolError

#: Daily volatility per symbol, so tests can reason about relative riskiness.
_DAILY_SIGMA: dict[str, float] = {
    "AAPL": 0.012,
    "MSFT": 0.010,
    "NVDA": 0.030,  # deliberately the most volatile
    "VTI": 0.006,  # deliberately the calmest
}
_DEFAULT_SIGMA = 0.015


class FakeProvider:
    """Deterministic bars, plus counters so tests can assert on cache behaviour."""

    def __init__(self, known: set[str] | None = None) -> None:
        self.known = known if known is not None else {"AAPL", "MSFT", "NVDA", "VTI"}
        self.price_calls = 0
        self.symbol_calls = 0

    def get_daily_prices(self, ticker: str, start: date, end: date) -> list[PriceBar]:
        self.price_calls += 1
        symbol = ticker.upper()
        if symbol not in self.known:
            raise UnknownSymbolError(ticker)

        trading_days = [
            start + timedelta(days=offset)
            for offset in range((end - start).days + 1)
            if (start + timedelta(days=offset)).weekday() < 5
        ]

        # Seed from the symbol so a ticker's series is stable across calls AND processes.
        # Python's built-in hash() is randomized per interpreter (PYTHONHASHSEED), which
        # would make these tests pass or fail depending on the run; crc32 is stable.
        seed = zlib.crc32(symbol.encode())
        rng = np.random.default_rng(seed)
        sigma = _DAILY_SIGMA.get(symbol, _DEFAULT_SIGMA)

        bars: list[PriceBar] = []
        price = 100.0
        for day in trading_days:
            price = max(price * (1.0 + float(rng.normal(0.0, sigma))), 1.0)
            close = Decimal(str(round(price, 4)))
            bars.append(
                PriceBar(
                    date=day,
                    open=close,
                    high=close + Decimal("1"),
                    low=close - Decimal("1"),
                    close=close,
                    adj_close=close,
                    volume=1_000_000,
                )
            )
        return bars

    def symbol_exists(self, ticker: str) -> bool:
        self.symbol_calls += 1
        return ticker.upper() in self.known
