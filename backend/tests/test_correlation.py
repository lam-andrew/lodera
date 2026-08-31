"""Tests for the correlation engine (US-6, FR-8).

Checked against known mathematical properties and an independent numpy computation, not
just "a number came back".
"""

from __future__ import annotations

import numpy as np
import pytest

from app.engines.risk.correlation import (
    MIN_OBSERVATIONS,
    average_correlation,
    correlation_matrix,
    least_correlated,
    most_correlated,
)


def _series(seed: int, n: int = 300, sigma: float = 0.01) -> list[float]:
    return list(np.random.default_rng(seed).normal(0.0, sigma, n))


# --- matrix properties ---------------------------------------------------------


def test_diagonal_is_one_and_matrix_is_symmetric() -> None:
    matrix = correlation_matrix([_series(1), _series(2), _series(3)])
    assert matrix is not None

    for i in range(3):
        assert matrix[i][i] == pytest.approx(1.0)
        for j in range(3):
            assert matrix[i][j] == pytest.approx(matrix[j][i])


def test_identical_series_are_perfectly_correlated() -> None:
    series = _series(4)
    matrix = correlation_matrix([series, series])
    assert matrix is not None
    assert matrix[0][1] == pytest.approx(1.0)


def test_inverted_series_are_perfectly_negatively_correlated() -> None:
    series = _series(5)
    matrix = correlation_matrix([series, [-r for r in series]])
    assert matrix is not None
    assert matrix[0][1] == pytest.approx(-1.0)


def test_independent_series_are_near_zero() -> None:
    matrix = correlation_matrix([_series(6, 2000), _series(7, 2000)])
    assert matrix is not None
    assert abs(matrix[0][1]) < 0.1


def test_matches_numpy_corrcoef() -> None:
    a, b, c = _series(8), _series(9), _series(10)
    expected = np.corrcoef(np.array([a, b, c]))
    matrix = correlation_matrix([a, b, c])
    assert matrix is not None

    for i in range(3):
        for j in range(3):
            assert matrix[i][j] == pytest.approx(float(expected[i][j]))


def test_correlation_is_scale_invariant() -> None:
    """Doubling one holding's volatility must not change its correlations."""
    a, b = _series(11), _series(12)
    base = correlation_matrix([a, b])
    scaled = correlation_matrix([a, [r * 5 for r in b]])
    assert base is not None and scaled is not None
    assert base[0][1] == pytest.approx(scaled[0][1])


def test_values_stay_within_bounds() -> None:
    matrix = correlation_matrix([_series(i) for i in range(13, 18)])
    assert matrix is not None
    for row in matrix:
        for value in row:
            assert value is not None
            assert -1.0 <= value <= 1.0


# --- degenerate input ----------------------------------------------------------


def test_needs_at_least_two_holdings() -> None:
    assert correlation_matrix([]) is None
    assert correlation_matrix([_series(19)]) is None


def test_needs_enough_observations() -> None:
    short = [0.01] * (MIN_OBSERVATIONS - 1)
    assert correlation_matrix([short, short]) is None


def test_misaligned_series_are_rejected() -> None:
    with pytest.raises(ValueError, match="aligned"):
        correlation_matrix([_series(20, 100), _series(21, 90)])


def test_constant_series_yields_none_not_zero() -> None:
    """A flat series has no variance, so correlation is undefined — not 0."""
    matrix = correlation_matrix([_series(22), [0.0] * 300])
    assert matrix is not None
    assert matrix[0][1] is None
    assert matrix[1][0] is None


# --- insights -------------------------------------------------------------------


def test_most_and_least_correlated_pairs_are_ranked() -> None:
    base = _series(23)
    tickers = ["TWIN", "SAME", "OTHER"]
    # TWIN/SAME are identical; OTHER is independent.
    matrix = correlation_matrix([base, base, _series(24)])
    assert matrix is not None

    top = most_correlated(tickers, matrix, limit=1)
    assert {top[0].a, top[0].b} == {"TWIN", "SAME"}
    assert top[0].correlation == pytest.approx(1.0)

    bottom = least_correlated(tickers, matrix, limit=1)
    assert "OTHER" in {bottom[0].a, bottom[0].b}


def test_pairs_exclude_the_diagonal_and_duplicates() -> None:
    tickers = ["A", "B", "C"]
    matrix = correlation_matrix([_series(25), _series(26), _series(27)])
    assert matrix is not None
    # 3 holdings -> 3 distinct pairs, not 9.
    assert len(most_correlated(tickers, matrix, limit=99)) == 3


def test_average_correlation_summarizes_the_portfolio() -> None:
    base = _series(28)
    matrix = correlation_matrix([base, base])
    assert matrix is not None
    assert average_correlation(["A", "B"], matrix) == pytest.approx(1.0)


def test_average_correlation_is_none_without_defined_pairs() -> None:
    matrix = correlation_matrix([[0.0] * 300, [0.0] * 300])
    assert matrix is not None
    assert average_correlation(["A", "B"], matrix) is None
