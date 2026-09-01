"""Ticker symbol validation.

As of US-4, recognition is delegated to the configured market-data provider
(:func:`is_recognized_symbol`), so any symbol the provider knows is accepted. The bundled
:data:`_KNOWN_SYMBOLS` set remains as an **offline fallback** for when market data is not
configured at all, so adding a holding keeps working (and the test suite needs no network).

Note the asymmetry in :func:`is_recognized_symbol`: a provider that answers "no" is
believed, but a provider that cannot answer is not treated as a "no".
"""

from __future__ import annotations

from app.data.provider import MarketDataError, MarketDataProvider

# A pragmatic set of common US equities and ETFs so demos work; not exhaustive by design.
_KNOWN_SYMBOLS: frozenset[str] = frozenset(
    {
        # Mega-cap / popular equities
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "GOOGL",
        "GOOG",
        "META",
        "TSLA",
        "AVGO",
        "BRK.B",
        "JPM",
        "V",
        "MA",
        "UNH",
        "HD",
        "PG",
        "JNJ",
        "XOM",
        "CVX",
        "LLY",
        "ABBV",
        "MRK",
        "KO",
        "PEP",
        "COST",
        "WMT",
        "BAC",
        "WFC",
        "DIS",
        "NFLX",
        "CRM",
        "ADBE",
        "AMD",
        "INTC",
        "CSCO",
        "ORCL",
        "QCOM",
        "TXN",
        "IBM",
        "GE",
        "BA",
        "CAT",
        "PFE",
        "T",
        "VZ",
        "NKE",
        "MCD",
        "SBUX",
        "PYPL",
        "UBER",
        "PLTR",
        "COIN",
        "SHOP",
        "F",
        "GM",
        # Major ETFs
        "SPY",
        "VOO",
        "IVV",
        "VTI",
        "QQQ",
        "VEA",
        "VWO",
        "VUG",
        "VTV",
        "SCHD",
        "DIA",
        "IWM",
        "AGG",
        "BND",
        "TLT",
        "IEF",
        "LQD",
        "HYG",
        "GLD",
        "SLV",
        "ARKK",
        "XLK",
        "XLF",
        "XLE",
        "XLV",
        "XLY",
        "XLP",
        "XLI",
        "XLU",
        "XLB",
        "XLRE",
        "SMH",
        "VNQ",
    }
)


def normalize_symbol(ticker: str) -> str:
    """Canonical form used for storage and comparison (trimmed, upper-cased)."""
    return ticker.strip().upper()


def is_known_symbol(ticker: str) -> bool:
    """Offline fallback: is ``ticker`` in the bundled set of common symbols?"""
    return normalize_symbol(ticker) in _KNOWN_SYMBOLS


def is_recognized_symbol(ticker: str, provider: MarketDataProvider | None) -> bool:
    """Return whether ``ticker`` is a real symbol.

    Asks the market-data provider when one is configured. A provider that answers "no" is
    believed; a provider that cannot answer is not treated as a "no" (see below). When no
    provider is configured at all, the bundled set is the only available check.
    """
    if provider is None:
        # Market data is not configured at all, so the bundled set is the only check we have.
        return is_known_symbol(ticker)
    try:
        return provider.symbol_exists(normalize_symbol(ticker))
    except MarketDataError:
        # The provider is configured but unreachable — rate-limited, down, or the key is
        # rejected. We cannot disprove the symbol, so accept it rather than tell the user
        # their real holding does not exist. Falling back to the bundled list here was
        # actively harmful: hitting the hourly rate limit mid-import made a Schwab export
        # lose ten perfectly valid tickers to "Unrecognized ticker", which is both wrong and
        # unactionable. A genuinely bad symbol still surfaces later, when pricing finds
        # nothing for it.
        return True
