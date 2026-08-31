"""Ticker symbol validation.

**Stopgap for US-1.** US-1's acceptance criteria require rejecting an unrecognized ticker,
but real symbol validation needs market data (US-4). Until then, "recognized" means "in this
bundled set of common US stocks and ETFs." US-4 replaces :func:`is_known_symbol` with a
market-data lookup (plus local caching), leaving the rest of the app unchanged.
"""

from __future__ import annotations

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
    """Return whether ``ticker`` is a recognized symbol (see module note)."""
    return normalize_symbol(ticker) in _KNOWN_SYMBOLS
