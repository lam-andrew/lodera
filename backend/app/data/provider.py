"""The market-data provider boundary (US-4, ADR 0011).

Everything above this module speaks in :class:`PriceBar` — a provider-neutral daily bar.
Concrete providers (Tiingo today, something else tomorrow) implement
:class:`MarketDataProvider`; no provider-specific shapes leak past this layer, so swapping
providers is a config change rather than a rewrite.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PriceBar:
    """One trading day of prices for a symbol.

    ``adj_close`` is adjusted for splits and dividends and is the series risk math should
    use — raw ``close`` jumps discontinuously across a split, which would show up as
    spurious volatility.
    """

    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adj_close: Decimal
    volume: int


class MarketDataError(RuntimeError):
    """A provider call failed (network, auth, rate limit, or bad response)."""


class UnknownSymbolError(MarketDataError):
    """The provider does not recognize the requested symbol."""


class RateLimitedError(MarketDataError):
    """The provider rejected the call because we exceeded the plan's rate limit."""


@runtime_checkable
class MarketDataProvider(Protocol):
    """What the rest of the system needs from a market-data source."""

    def get_daily_prices(self, ticker: str, start: date, end: date) -> list[PriceBar]:
        """Return daily bars for ``ticker`` between ``start`` and ``end`` (inclusive),
        oldest first. Raises :class:`UnknownSymbolError` if the symbol is not recognized."""
        ...

    def symbol_exists(self, ticker: str) -> bool:
        """Return whether the provider recognizes ``ticker``."""
        ...
