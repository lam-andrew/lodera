"""Risk & Exposure engine — the core analytical component (ADR 0005).

Pure computation: these modules know nothing about the database, HTTP, or the rest of the
app. They take plain sequences and return plain numbers, so the math can be unit-tested in
isolation and callers reach it only through the API layer (ADR 0004).
"""

from app.engines.risk.concentration import (
    OVERLAP_CORRELATION,
    OVERWEIGHT_MULTIPLE,
    OverlapGroup,
    Position,
    effective_holdings,
    herfindahl_index,
    overlapping_exposure,
    overweight_positions,
    top_n_weight,
)
from app.engines.risk.correlation import (
    HIGH_CORRELATION,
    LOW_CORRELATION,
    Pair,
    average_correlation,
    correlation_matrix,
    least_correlated,
    most_correlated,
)
from app.engines.risk.drawdown import (
    Episode,
    current_drawdown,
    drawdown_episodes,
    drawdown_series,
    max_drawdown,
)
from app.engines.risk.volatility import (
    TRADING_DAYS_PER_YEAR,
    annualized_volatility,
    daily_returns,
    portfolio_volatility,
    volatility_band,
)

__all__ = [
    "HIGH_CORRELATION",
    "LOW_CORRELATION",
    "OVERLAP_CORRELATION",
    "OVERWEIGHT_MULTIPLE",
    "TRADING_DAYS_PER_YEAR",
    "Episode",
    "OverlapGroup",
    "Pair",
    "Position",
    "annualized_volatility",
    "average_correlation",
    "correlation_matrix",
    "current_drawdown",
    "daily_returns",
    "drawdown_episodes",
    "drawdown_series",
    "effective_holdings",
    "herfindahl_index",
    "least_correlated",
    "max_drawdown",
    "most_correlated",
    "overlapping_exposure",
    "overweight_positions",
    "portfolio_volatility",
    "top_n_weight",
    "volatility_band",
]
