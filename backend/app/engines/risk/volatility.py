"""Volatility (US-5, FR-7).

Volatility here means the **annualized standard deviation of daily returns** — the standard
measure of how much a position swings. It describes historical dispersion; it is not a
forecast and not advice.

Method, and why:

* **Simple (arithmetic) returns**, ``r_t = P_t / P_{t-1} - 1``, rather than log returns.
  A portfolio's simple return is exactly the weighted sum of its holdings' simple returns,
  which is what makes the portfolio covariance math below correct. That identity only holds
  approximately for log returns.
* **Adjusted close** must be the input series. Raw close jumps discontinuously across splits
  and dividends, which would register as large fake returns.
* **Sample** standard deviation (``ddof=1``): we hold a sample of history, not the whole
  population.
* **Annualized** by ``sqrt(252)`` — variance scales with time, so standard deviation scales
  with its square root, and 252 is the conventional count of US trading days per year.
* **Portfolio volatility uses the full covariance matrix**, ``sigma_p = sqrt(wT @ Sigma @ w)``,
  not a weighted average of individual volatilities. The weighted average would ignore
  diversification and overstate risk whenever holdings are less than perfectly correlated.

Prices arrive as ``Decimal`` (exact money) and are converted to ``float`` here: these are
statistical estimates, where float precision is appropriate and Decimal would be misleading
about how exact the answer is.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from itertools import pairwise

import numpy as np

#: Conventional number of US trading days in a year, used to annualize daily figures.
TRADING_DAYS_PER_YEAR = 252

#: Below this many returns, a volatility estimate is too noisy to report.
MIN_RETURNS_FOR_VOLATILITY = 20


def daily_returns(prices: Sequence[Decimal | float]) -> list[float]:
    """Simple daily returns from a chronological price series.

    Non-positive prices are impossible for a tradable security and would make the return
    undefined, so any such pair is skipped rather than producing an infinity.
    """
    values = [float(p) for p in prices]
    returns: list[float] = []
    for previous, current in pairwise(values):
        if previous <= 0:
            continue
        returns.append(current / previous - 1.0)
    return returns


def annualized_volatility(
    returns: Sequence[float], *, periods_per_year: int = TRADING_DAYS_PER_YEAR
) -> float | None:
    """Annualized sample standard deviation of ``returns``.

    Returns ``None`` when there is too little history to say anything meaningful, rather
    than reporting a falsely precise number from a handful of observations.
    """
    if len(returns) < MIN_RETURNS_FOR_VOLATILITY:
        return None
    daily = float(np.std(np.asarray(returns, dtype=float), ddof=1))
    return daily * float(np.sqrt(periods_per_year))


def portfolio_volatility(
    weights: Sequence[float],
    return_series: Sequence[Sequence[float]],
    *,
    periods_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float | None:
    """Annualized volatility of a weighted portfolio.

    ``return_series[i]`` is the return series for the holding with ``weights[i]``; every
    series must be the same length and aligned to the same dates (the caller is responsible
    for that alignment). Computed as ``sqrt(wT @ Sigma @ w)`` so that correlations between
    holdings — the diversification effect — are captured.
    """
    if not weights or len(weights) != len(return_series):
        return None

    lengths = {len(series) for series in return_series}
    if len(lengths) != 1:
        raise ValueError("Return series must be aligned to the same length.")
    if lengths.pop() < MIN_RETURNS_FOR_VOLATILITY:
        return None

    matrix = np.asarray(return_series, dtype=float)
    w = np.asarray(weights, dtype=float)

    total = w.sum()
    if total <= 0:
        return None
    w = w / total  # normalize so weights sum to 1

    # rowvar=True: each row of `matrix` is one holding's series.
    covariance = np.cov(matrix, ddof=1) if matrix.shape[0] > 1 else np.var(matrix, ddof=1)
    variance = float(w @ np.atleast_2d(covariance) @ w.T)
    if variance < 0:  # numerical noise around zero
        variance = 0.0
    return float(np.sqrt(variance) * np.sqrt(periods_per_year))


#: Descriptive bands for annualized volatility, as decimals (0.15 == 15%).
#:
#: These are conventional reference points for framing a number, not thresholds with any
#: regulatory meaning and not a recommendation: a broad equity index has historically sat
#: near 15-20% annualized, so "moderate" is centred there. They exist so the UI can say
#: "elevated" alongside "31.4%" rather than leaving a bare number to interpret.
VOLATILITY_BAND_LOW = 0.15
VOLATILITY_BAND_MODERATE = 0.25


def volatility_band(volatility: float | None) -> str | None:
    """Classify annualized ``volatility`` as ``"low"``, ``"moderate"`` or ``"high"``."""
    if volatility is None:
        return None
    if volatility < VOLATILITY_BAND_LOW:
        return "low"
    if volatility < VOLATILITY_BAND_MODERATE:
        return "moderate"
    return "high"
