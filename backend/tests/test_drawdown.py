"""Tests for the drawdown engine (US-8, FR-10).

Values are chosen so every expected figure can be checked by hand.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.engines.risk.drawdown import (
    current_drawdown,
    drawdown_episodes,
    drawdown_series,
    max_drawdown,
)


def days(n: int) -> list[date]:
    start = date(2026, 1, 1)
    return [start + timedelta(days=i) for i in range(n)]


# --- the series -----------------------------------------------------------------


def test_a_rising_series_is_never_underwater() -> None:
    assert drawdown_series([100, 110, 120, 130]) == [0.0, 0.0, 0.0, 0.0]


def test_decline_is_measured_from_the_running_peak() -> None:
    # peak 100 -> 90 is -10%; peak stays 100 until it is exceeded.
    series = drawdown_series([100, 90, 95, 100, 120, 60])
    assert series == pytest.approx([0.0, -0.10, -0.05, 0.0, 0.0, -0.5])


def test_the_peak_is_the_running_maximum_not_the_global_one() -> None:
    """At index 1 the portfolio had never been worth more, so it is not 'down'."""
    series = drawdown_series([100, 150, 120])
    assert series[1] == 0.0
    assert series[2] == pytest.approx(-0.2)  # 120/150 - 1


def test_drawdowns_are_never_positive() -> None:
    assert all(d <= 0 for d in drawdown_series([100, 130, 90, 200, 150, 210]))


def test_empty_and_single_value_series() -> None:
    assert drawdown_series([]) == []
    assert drawdown_series([100]) == [0.0]
    assert max_drawdown([]) is None


# --- headline figures -------------------------------------------------------------


def test_max_drawdown_finds_the_deepest_decline() -> None:
    # Two declines: 100->80 (-20%) and 120->72 (-40%). The deeper one wins.
    assert max_drawdown([100, 80, 100, 120, 72, 130]) == pytest.approx(-0.4)


def test_current_drawdown_reports_the_final_point() -> None:
    assert current_drawdown([100, 120, 108]) == pytest.approx(-0.1)
    assert current_drawdown([100, 90, 130]) == pytest.approx(0.0)  # at a new high


# --- episodes ----------------------------------------------------------------------


def test_a_recovered_episode_records_peak_trough_and_recovery() -> None:
    values = [100, 90, 80, 90, 100, 105]
    episodes = drawdown_episodes(days(len(values)), values)

    assert len(episodes) == 1
    episode = episodes[0]
    assert episode.depth == pytest.approx(-0.2)
    assert episode.peak_date == days(6)[0]
    assert episode.trough_date == days(6)[2]
    assert episode.recovery_date == days(6)[4]  # first day back at 100
    assert episode.decline_days == 2
    assert episode.recovery_days == 2
    assert episode.recovered is True


def test_an_ongoing_decline_is_reported_as_unrecovered() -> None:
    """A drawdown still underwater at the end is the one users most need to see."""
    values = [100, 120, 90]
    episodes = drawdown_episodes(days(len(values)), values)

    assert len(episodes) == 1
    assert episodes[0].recovered is False
    assert episodes[0].recovery_date is None
    assert episodes[0].recovery_days is None
    assert episodes[0].depth == pytest.approx(-0.25)  # 90/120 - 1


def test_separate_declines_are_separate_episodes() -> None:
    values = [100, 80, 100, 120, 84, 120]
    episodes = drawdown_episodes(days(len(values)), values)

    assert len(episodes) == 2
    # Ordered deepest first: -30% then -20%.
    assert episodes[0].depth == pytest.approx(-0.3)
    assert episodes[1].depth == pytest.approx(-0.2)


def test_shallow_wobbles_are_not_reported_as_episodes() -> None:
    values = [100, 99.5, 100, 99.6, 101]
    assert drawdown_episodes(days(len(values)), values) == []


def test_episode_limit_is_respected() -> None:
    values = [100, 80, 100, 90, 100, 85, 100, 70, 100]
    assert len(drawdown_episodes(days(len(values)), values, limit=2)) == 2


def test_the_deepest_episode_matches_max_drawdown() -> None:
    values = [100, 92, 105, 70, 110, 95, 130]
    episodes = drawdown_episodes(days(len(values)), values)
    assert episodes[0].depth == pytest.approx(max_drawdown(values))


def test_mismatched_dates_and_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="same length"):
        drawdown_episodes(days(3), [100, 90])


def test_a_flat_series_has_no_episodes() -> None:
    assert drawdown_episodes(days(5), [100] * 5) == []
