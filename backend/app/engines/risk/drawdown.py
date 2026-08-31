"""Drawdown (US-8, FR-10).

Volatility describes typical movement in both directions. Drawdown describes the part
investors actually feel: how far the portfolio fell from a high, how long it stayed down,
and whether it came back.

The measure is the decline from the **running maximum** — the highest value reached so far,
not the highest value overall. That distinction matters: measuring against a future peak
would report a "loss" at a moment when the portfolio had never been worth more.

    drawdown(t) = value(t) / running_peak(t) - 1

The result is always ≤ 0, expressed as a fraction (-0.142 = 14.2% below the prior high).
Unlike volatility, drawdown is **not annualized** — it is a realized historical fact about a
specific period, not a rate that scales with time.

This module is pure: values in, numbers out.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

#: Episodes shallower than this are noise rather than a decline worth reporting.
MIN_EPISODE_DEPTH = 0.02


@dataclass(frozen=True, slots=True)
class Episode:
    """One peak-to-trough decline, and whether it recovered."""

    #: Depth as a negative fraction (-0.142 == -14.2%).
    depth: float
    peak_date: date
    trough_date: date
    #: Date the prior peak was regained, or ``None`` if still below it.
    recovery_date: date | None
    #: Trading days from peak to trough.
    decline_days: int
    #: Trading days from trough back to the peak, or ``None`` if not yet recovered.
    recovery_days: int | None

    @property
    def recovered(self) -> bool:
        return self.recovery_date is not None


def drawdown_series(values: Sequence[float]) -> list[float]:
    """Decline from the running peak at each point, as negative fractions."""
    series: list[float] = []
    peak = float("-inf")
    for value in values:
        peak = max(peak, value)
        series.append(0.0 if peak <= 0 else value / peak - 1.0)
    return series


def max_drawdown(values: Sequence[float]) -> float | None:
    """The deepest decline in the series, as a negative fraction."""
    series = drawdown_series(values)
    return min(series) if series else None


def current_drawdown(values: Sequence[float]) -> float | None:
    """How far the final value sits below the highest value reached."""
    series = drawdown_series(values)
    return series[-1] if series else None


def drawdown_episodes(
    dates: Sequence[date],
    values: Sequence[float],
    *,
    limit: int = 5,
    min_depth: float = MIN_EPISODE_DEPTH,
) -> list[Episode]:
    """Distinct peak-to-trough declines, deepest first.

    An episode opens when the value falls below its running peak and closes when that peak
    is regained. A decline still underwater at the end of the series is reported as an
    unrecovered episode rather than dropped — an ongoing drawdown is exactly the one a user
    most needs to see.
    """
    if len(values) != len(dates):
        raise ValueError("dates and values must be the same length.")
    if not values:
        return []

    episodes: list[Episode] = []
    peak_index = 0
    trough_index = 0
    in_episode = False

    for i, value in enumerate(values):
        if value >= values[peak_index]:
            # New high: close any open episode here, since the peak has been regained.
            if in_episode:
                depth = values[trough_index] / values[peak_index] - 1.0
                if depth <= -min_depth:
                    episodes.append(
                        Episode(
                            depth=depth,
                            peak_date=dates[peak_index],
                            trough_date=dates[trough_index],
                            recovery_date=dates[i],
                            decline_days=trough_index - peak_index,
                            recovery_days=i - trough_index,
                        )
                    )
                in_episode = False
            peak_index = i
            trough_index = i
        else:
            in_episode = True
            if value < values[trough_index] or trough_index == peak_index:
                trough_index = i

    # A decline that never recovered before the series ended.
    if in_episode:
        depth = values[trough_index] / values[peak_index] - 1.0
        if depth <= -min_depth:
            episodes.append(
                Episode(
                    depth=depth,
                    peak_date=dates[peak_index],
                    trough_date=dates[trough_index],
                    recovery_date=None,
                    decline_days=trough_index - peak_index,
                    recovery_days=None,
                )
            )

    return sorted(episodes, key=lambda e: e.depth)[:limit]
