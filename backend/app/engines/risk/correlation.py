"""Correlation among holdings (US-6, FR-8).

Correlation answers a different question from volatility. Volatility says how much one
holding swings; correlation says whether holdings swing *together*. That distinction is the
whole point of the story: a portfolio can look diversified by name while being concentrated
in behaviour, because its positions all respond to the same underlying factor.

Method:

* **Pearson correlation of daily simple returns**, the same return series volatility uses
  (ADR 0012), so the two metrics describe the same history and are mutually consistent.
* ``rho_ij = Cov(i, j) / (sigma_i * sigma_j)`` — covariance normalized by both standard
  deviations, which puts every pair on the same -1..+1 scale regardless of how volatile the
  individual holdings are. This is what makes a bond ETF and a growth stock comparable.
* **Correlation is not annualized.** Scaling both the covariance and the two standard
  deviations by the same ``sqrt(252)`` cancels out, so the daily and annualized figures are
  identical. Volatility is annualized; correlation simply is not a time-scaled quantity.
* A **constant series has zero variance**, which makes the denominator zero and the
  correlation undefined rather than zero. We return ``None`` for those pairs instead of
  emitting a misleading 0.0.

Like the rest of the engine this module is pure: sequences in, numbers out.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

#: Correlations at or above this are worth flagging as behaving like one position.
HIGH_CORRELATION = 0.75

#: Correlations at or below this are meaningfully diversifying.
LOW_CORRELATION = 0.30

#: Minimum overlapping observations before a pair's correlation is reported.
MIN_OBSERVATIONS = 20


@dataclass(frozen=True, slots=True)
class Pair:
    """One pair of holdings and how closely they move together."""

    a: str
    b: str
    correlation: float


def correlation_matrix(
    return_series: Sequence[Sequence[float]],
) -> list[list[float | None]] | None:
    """Pearson correlation matrix for aligned return series.

    ``return_series[i]`` must be the same length as every other (the caller aligns them to
    common trading dates). Returns ``None`` when there is not enough data to compute
    anything; individual cells are ``None`` where a series has no variance.
    """
    if len(return_series) < 2:
        return None

    lengths = {len(series) for series in return_series}
    if len(lengths) != 1:
        raise ValueError("Return series must be aligned to the same length.")
    if lengths.pop() < MIN_OBSERVATIONS:
        return None

    matrix = np.asarray(return_series, dtype=float)

    # A zero-variance row makes its correlations undefined (0/0). numpy would emit NaN and a
    # warning; we detect it up front and report those cells as None instead.
    variances = matrix.var(axis=1, ddof=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        raw = np.corrcoef(matrix)

    size = len(return_series)
    result: list[list[float | None]] = []
    for i in range(size):
        row: list[float | None] = []
        for j in range(size):
            if variances[i] == 0 or variances[j] == 0:
                row.append(None)
            elif i == j:
                row.append(1.0)
            else:
                value = float(raw[i][j])
                # Clamp floating-point overshoot so values stay inside [-1, 1].
                row.append(max(-1.0, min(1.0, value)) if np.isfinite(value) else None)
        result.append(row)
    return result


def _pairs(tickers: Sequence[str], matrix: Sequence[Sequence[float | None]]) -> list[Pair]:
    """Every distinct pair with a defined correlation (upper triangle only)."""
    found: list[Pair] = []
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            value = matrix[i][j]
            if value is not None:
                found.append(Pair(tickers[i], tickers[j], value))
    return found


def most_correlated(
    tickers: Sequence[str], matrix: Sequence[Sequence[float | None]], *, limit: int = 3
) -> list[Pair]:
    """Pairs that move together most — the "hidden concentration" the story asks for."""
    return sorted(_pairs(tickers, matrix), key=lambda p: p.correlation, reverse=True)[:limit]


def least_correlated(
    tickers: Sequence[str], matrix: Sequence[Sequence[float | None]], *, limit: int = 3
) -> list[Pair]:
    """Pairs that move together least — where diversification is actually coming from."""
    return sorted(_pairs(tickers, matrix), key=lambda p: p.correlation)[:limit]


def average_correlation(
    tickers: Sequence[str], matrix: Sequence[Sequence[float | None]]
) -> float | None:
    """Mean of all distinct pairwise correlations.

    A single summary of how tightly the portfolio moves as a unit: near 1 means the holdings
    are effectively one bet, near 0 means they are genuinely independent.
    """
    pairs = _pairs(tickers, matrix)
    if not pairs:
        return None
    return float(np.mean([p.correlation for p in pairs]))
