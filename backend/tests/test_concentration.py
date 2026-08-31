"""Tests for the concentration engine (US-7, FR-9)."""

from __future__ import annotations

import pytest

from app.engines.risk.concentration import (
    Position,
    effective_holdings,
    herfindahl_index,
    overlapping_exposure,
    overweight_positions,
    top_n_weight,
)

# --- HHI and effective holdings -------------------------------------------------


def test_equal_weights_give_hhi_of_one_over_n() -> None:
    assert herfindahl_index([0.25] * 4) == pytest.approx(0.25)
    assert herfindahl_index([0.1] * 10) == pytest.approx(0.1)


def test_a_single_holding_is_maximally_concentrated() -> None:
    assert herfindahl_index([1.0]) == pytest.approx(1.0)


def test_hhi_normalizes_weights_that_do_not_sum_to_one() -> None:
    """Raw market values must give the same answer as fractions."""
    assert herfindahl_index([50, 50]) == pytest.approx(herfindahl_index([0.5, 0.5]))
    assert herfindahl_index([1000, 3000]) == pytest.approx(herfindahl_index([0.25, 0.75]))


def test_effective_holdings_equals_count_when_equally_weighted() -> None:
    assert effective_holdings([0.2] * 5) == pytest.approx(5.0)


def test_effective_holdings_falls_when_one_position_dominates() -> None:
    """Four holdings, but one is 90% — it should behave like barely more than one."""
    effective = effective_holdings([0.9, 0.04, 0.03, 0.03])
    assert effective is not None
    assert 1.0 < effective < 1.5


def test_concentrating_weight_always_reduces_effective_holdings() -> None:
    spread = effective_holdings([0.25, 0.25, 0.25, 0.25])
    skewed = effective_holdings([0.7, 0.1, 0.1, 0.1])
    assert spread is not None and skewed is not None
    assert skewed < spread


def test_degenerate_weights_return_none() -> None:
    assert herfindahl_index([]) is None
    assert herfindahl_index([0.0, 0.0]) is None
    assert effective_holdings([]) is None


# --- top-N ----------------------------------------------------------------------


def test_top_n_weight_sums_the_largest_positions() -> None:
    weights = [0.5, 0.2, 0.15, 0.1, 0.05]
    assert top_n_weight(weights, 1) == pytest.approx(0.5)
    assert top_n_weight(weights, 3) == pytest.approx(0.85)
    assert top_n_weight(weights, 99) == pytest.approx(1.0)


def test_top_n_weight_is_order_independent() -> None:
    assert top_n_weight([0.1, 0.6, 0.3], 2) == pytest.approx(0.9)


# --- overweight -----------------------------------------------------------------


def test_overweight_uses_an_equal_weight_baseline() -> None:
    """With 4 holdings, equal weight is 25% and the 2x threshold is 50%."""
    positions = [
        Position("BIG", 0.55),
        Position("MID", 0.25),
        Position("A", 0.1),
        Position("B", 0.1),
    ]
    assert [p.ticker for p in overweight_positions(positions)] == ["BIG"]


def test_overweight_threshold_scales_with_portfolio_size() -> None:
    """8% is fine in a 4-holding portfolio and overweight in a 50-holding one."""
    small = [Position("X", 0.08), *[Position(f"P{i}", 0.92 / 3) for i in range(3)]]
    assert "X" not in [p.ticker for p in overweight_positions(small)]

    large = [Position("X", 0.08), *[Position(f"P{i}", 0.92 / 49) for i in range(49)]]
    assert "X" in [p.ticker for p in overweight_positions(large)]


def test_equally_weighted_portfolio_has_no_overweight_positions() -> None:
    assert overweight_positions([Position(f"P{i}", 0.2) for i in range(5)]) == []


def test_a_single_holding_is_not_flagged_as_overweight() -> None:
    """One holding is 100% by definition; calling it overweight says nothing."""
    assert overweight_positions([Position("ONLY", 1.0)]) == []


# --- overlapping exposure --------------------------------------------------------

TICKERS = ["VOO", "VTI", "QQQ", "BND"]
# VOO/VTI/QQQ move together; BND does not.
MATRIX: list[list[float | None]] = [
    [1.00, 1.00, 0.93, 0.36],
    [1.00, 1.00, 0.92, 0.38],
    [0.93, 0.92, 1.00, 0.31],
    [0.36, 0.38, 0.31, 1.00],
]


def test_overlapping_holdings_are_grouped_with_a_combined_weight() -> None:
    positions = [
        Position("VOO", 0.30),
        Position("VTI", 0.25),
        Position("QQQ", 0.25),
        Position("BND", 0.20),
    ]
    groups = overlapping_exposure(positions, TICKERS, MATRIX)

    assert len(groups) == 1
    assert groups[0].tickers == ["QQQ", "VOO", "VTI"]
    # The three behave like one 80% position.
    assert groups[0].combined_weight == pytest.approx(0.80)
    assert groups[0].min_correlation == pytest.approx(0.92)


def test_uncorrelated_holdings_form_no_group() -> None:
    tickers = ["A", "B"]
    matrix: list[list[float | None]] = [[1.0, 0.1], [0.1, 1.0]]
    positions = [Position("A", 0.5), Position("B", 0.5)]
    assert overlapping_exposure(positions, tickers, matrix) == []


def test_group_members_must_correlate_with_every_member_not_just_one() -> None:
    """A chain A-B-C where A and C are unrelated must not be reported as one cluster."""
    tickers = ["A", "B", "C"]
    matrix: list[list[float | None]] = [
        [1.0, 0.90, 0.10],
        [0.90, 1.0, 0.90],
        [0.10, 0.90, 1.0],
    ]
    positions = [Position("A", 0.4), Position("B", 0.35), Position("C", 0.25)]
    groups = overlapping_exposure(positions, tickers, matrix)

    assert len(groups) == 1
    assert groups[0].tickers == ["A", "B"]  # C excluded: it does not match A


def test_groups_are_ordered_by_combined_weight() -> None:
    tickers = ["A", "B", "C", "D"]
    matrix: list[list[float | None]] = [
        [1.0, 0.9, 0.1, 0.1],
        [0.9, 1.0, 0.1, 0.1],
        [0.1, 0.1, 1.0, 0.95],
        [0.1, 0.1, 0.95, 1.0],
    ]
    positions = [Position("A", 0.1), Position("B", 0.1), Position("C", 0.4), Position("D", 0.4)]
    groups = overlapping_exposure(positions, tickers, matrix)

    assert [g.tickers for g in groups] == [["C", "D"], ["A", "B"]]


def test_undefined_correlations_never_form_a_group() -> None:
    tickers = ["A", "B"]
    matrix: list[list[float | None]] = [[1.0, None], [None, 1.0]]
    positions = [Position("A", 0.5), Position("B", 0.5)]
    assert overlapping_exposure(positions, tickers, matrix) == []
