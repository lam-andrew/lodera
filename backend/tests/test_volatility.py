"""Tests for the risk engine's volatility math (US-5, FR-7).

These exercise the engine directly — no DB, no HTTP — and check the numbers against
independently computed values rather than just asserting "something came back".
"""

from __future__ import annotations

import math
from decimal import Decimal

import numpy as np
import pytest

from app.engines.risk.volatility import (
    MIN_RETURNS_FOR_VOLATILITY,
    TRADING_DAYS_PER_YEAR,
    annualized_volatility,
    daily_returns,
    portfolio_volatility,
    volatility_band,
)

# --- daily_returns ------------------------------------------------------------


def test_daily_returns_are_simple_returns() -> None:
    assert daily_returns([Decimal("100"), Decimal("110"), Decimal("99")]) == pytest.approx(
        [0.10, -0.10]
    )


def test_daily_returns_needs_two_prices() -> None:
    assert daily_returns([]) == []
    assert daily_returns([Decimal("100")]) == []


def test_flat_prices_produce_zero_returns() -> None:
    assert daily_returns([Decimal("50")] * 5) == [0.0, 0.0, 0.0, 0.0]


def test_non_positive_prices_are_skipped_not_infinite() -> None:
    returns = daily_returns([Decimal("100"), Decimal("0"), Decimal("50")])
    assert all(math.isfinite(r) for r in returns)


# --- annualized_volatility ----------------------------------------------------


def test_volatility_matches_an_independent_computation() -> None:
    rng = np.random.default_rng(42)
    returns = list(rng.normal(0.0, 0.01, size=300))

    expected = float(np.std(returns, ddof=1)) * math.sqrt(TRADING_DAYS_PER_YEAR)
    assert annualized_volatility(returns) == pytest.approx(expected)


def test_constant_returns_have_zero_volatility() -> None:
    assert annualized_volatility([0.001] * 100) == pytest.approx(0.0)


def test_volatility_annualizes_by_sqrt_of_trading_days() -> None:
    """A daily sigma of 1% should annualize to ~15.9% (0.01 * sqrt(252))."""
    rng = np.random.default_rng(7)
    returns = list(rng.normal(0.0, 0.01, size=5000))
    annual = annualized_volatility(returns)
    assert annual is not None
    assert annual == pytest.approx(0.01 * math.sqrt(252), rel=0.05)


def test_too_little_history_returns_none_rather_than_a_noisy_number() -> None:
    assert annualized_volatility([0.01] * (MIN_RETURNS_FOR_VOLATILITY - 1)) is None
    assert annualized_volatility([]) is None


def test_a_more_volatile_series_scores_higher() -> None:
    rng = np.random.default_rng(1)
    calm = annualized_volatility(list(rng.normal(0, 0.005, 300)))
    wild = annualized_volatility(list(rng.normal(0, 0.02, 300)))
    assert calm is not None and wild is not None
    assert wild > calm


# --- portfolio_volatility -----------------------------------------------------


def test_single_holding_portfolio_equals_that_holding_volatility() -> None:
    rng = np.random.default_rng(3)
    series = list(rng.normal(0, 0.01, 300))
    solo = annualized_volatility(series)
    assert portfolio_volatility([1.0], [series]) == pytest.approx(solo)


def test_perfectly_correlated_holdings_get_no_diversification_benefit() -> None:
    """Identical series => portfolio vol equals the weighted average (no benefit)."""
    rng = np.random.default_rng(5)
    series = list(rng.normal(0, 0.01, 300))
    combined = portfolio_volatility([0.5, 0.5], [series, series])
    assert combined == pytest.approx(annualized_volatility(series))


def test_uncorrelated_holdings_reduce_portfolio_volatility() -> None:
    """The core diversification property: the whole is less volatile than its parts."""
    rng = np.random.default_rng(11)
    a = list(rng.normal(0, 0.01, 1000))
    b = list(rng.normal(0, 0.01, 1000))

    portfolio = portfolio_volatility([0.5, 0.5], [a, b])
    weighted_average = 0.5 * annualized_volatility(a) + 0.5 * annualized_volatility(b)  # type: ignore[operator]

    assert portfolio is not None
    assert portfolio < weighted_average
    # Two equal, uncorrelated assets: sigma_p ~= sigma / sqrt(2).
    assert portfolio == pytest.approx(weighted_average / math.sqrt(2), rel=0.15)


def test_negatively_correlated_holdings_reduce_volatility_the_most() -> None:
    rng = np.random.default_rng(13)
    a = list(rng.normal(0, 0.01, 500))
    inverse = [-r for r in a]

    hedged = portfolio_volatility([0.5, 0.5], [a, inverse])
    assert hedged is not None
    assert hedged == pytest.approx(0.0, abs=1e-9)


def test_portfolio_volatility_matches_the_covariance_formula() -> None:
    rng = np.random.default_rng(17)
    a = list(rng.normal(0, 0.012, 400))
    b = list(rng.normal(0, 0.008, 400))
    weights = np.array([0.7, 0.3])

    covariance = np.cov(np.array([a, b]), ddof=1)
    expected = math.sqrt(float(weights @ covariance @ weights.T)) * math.sqrt(252)

    assert portfolio_volatility([0.7, 0.3], [a, b]) == pytest.approx(expected)


def test_weights_are_normalized() -> None:
    """Weights that don't sum to 1 are normalized, not taken literally."""
    rng = np.random.default_rng(19)
    a = list(rng.normal(0, 0.01, 300))
    b = list(rng.normal(0, 0.02, 300))
    assert portfolio_volatility([70, 30], [a, b]) == pytest.approx(
        portfolio_volatility([0.7, 0.3], [a, b])
    )


def test_misaligned_series_are_rejected() -> None:
    with pytest.raises(ValueError, match="aligned"):
        portfolio_volatility([0.5, 0.5], [[0.01] * 50, [0.01] * 40])


def test_portfolio_volatility_handles_degenerate_input() -> None:
    assert portfolio_volatility([], []) is None
    assert portfolio_volatility([1.0], [[0.01] * 5]) is None  # too little history
    assert portfolio_volatility([0.0], [[0.01] * 50]) is None  # zero total weight


# --- banding ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("volatility", "expected"),
    [
        (0.05, "low"),
        (0.149, "low"),
        (0.15, "moderate"),
        (0.24, "moderate"),
        (0.25, "high"),
        (0.80, "high"),
        (None, None),
    ],
)
def test_volatility_bands(volatility: float | None, expected: str | None) -> None:
    assert volatility_band(volatility) == expected
