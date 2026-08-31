"""Risk & Exposure engine — the core analytical component (ADR 0005).

Pure computation: these modules know nothing about the database, HTTP, or the rest of the
app. They take plain sequences and return plain numbers, so the math can be unit-tested in
isolation and callers reach it only through the API layer (ADR 0004).
"""

from app.engines.risk.volatility import (
    TRADING_DAYS_PER_YEAR,
    annualized_volatility,
    daily_returns,
    portfolio_volatility,
    volatility_band,
)

__all__ = [
    "TRADING_DAYS_PER_YEAR",
    "annualized_volatility",
    "daily_returns",
    "portfolio_volatility",
    "volatility_band",
]
