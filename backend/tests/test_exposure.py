"""API tests for concentration (US-7) and drawdown (US-8)."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from tests.fakes import FakeProvider


def _add(client: TestClient, ticker: str, quantity: str) -> None:
    assert (
        client.post("/holdings", json={"ticker": ticker, "quantity": quantity}).status_code == 201
    )


# --- US-7: concentration ---------------------------------------------------------


def test_concentration_reports_hhi_and_effective_holdings(client: TestClient) -> None:
    _add(client, "AAPL", "10")
    _add(client, "MSFT", "10")
    _add(client, "VTI", "10")

    body = client.get("/portfolio/concentration").json()

    assert body["holdings_count"] == 3
    assert Decimal(body["hhi"]) > 0
    effective = Decimal(body["effective_holdings"])
    # Effective holdings can never exceed the real count.
    assert 1 <= effective <= 3
    assert Decimal(body["top_1_pct"]) <= Decimal(body["top_3_pct"])
    assert Decimal(body["top_3_pct"]) == Decimal("100.00")  # only 3 holdings


def test_a_dominant_position_drives_effective_holdings_toward_one(client: TestClient) -> None:
    """US-7 acceptance: overweight positions are highlighted."""
    _add(client, "AAPL", "10000")  # overwhelmingly the largest
    _add(client, "MSFT", "1")
    _add(client, "VTI", "1")

    body = client.get("/portfolio/concentration").json()

    assert Decimal(body["effective_holdings"]) < Decimal("1.5")
    assert Decimal(body["top_1_pct"]) > Decimal("90")
    assert [p["ticker"] for p in body["overweight"]] == ["AAPL"]
    assert Decimal(body["overweight"][0]["times_equal_weight"]) > Decimal("2")


def test_a_balanced_portfolio_flags_nothing_as_overweight(client: TestClient) -> None:
    # FakeProvider prices all symbols near 100, so equal share counts are near equal weights.
    _add(client, "AAPL", "10")
    _add(client, "MSFT", "10")
    _add(client, "NVDA", "10")
    _add(client, "VTI", "10")

    body = client.get("/portfolio/concentration").json()
    assert body["overweight"] == []


def test_concentration_exposes_its_thresholds(client: TestClient) -> None:
    body = client.get("/portfolio/concentration").json()
    assert Decimal(body["overweight_multiple"]) == Decimal("2")
    assert Decimal(body["overlap_threshold"]) == Decimal("0.75")


def test_concentration_of_an_empty_portfolio_does_not_fail(client: TestClient) -> None:
    body = client.get("/portfolio/concentration").json()
    assert body["holdings_count"] == 0
    assert body["hhi"] is None
    assert body["overweight"] == []
    assert body["overlaps"] == []


def test_overlaps_have_a_combined_weight_and_a_floor_correlation(client: TestClient) -> None:
    """Whatever groups form, their shape must be internally consistent."""
    for ticker in ("AAPL", "MSFT", "NVDA", "VTI"):
        _add(client, ticker, "10")

    body = client.get("/portfolio/concentration").json()
    threshold = Decimal(body["overlap_threshold"])

    for group in body["overlaps"]:
        assert len(group["tickers"]) >= 2
        assert group["tickers"] == sorted(group["tickers"])
        assert Decimal(group["min_correlation"]) >= threshold
        assert Decimal("0") < Decimal(group["combined_weight_pct"]) <= Decimal("100.01")


def test_concentration_window_is_validated(client: TestClient) -> None:
    assert client.get("/portfolio/concentration?days=10").status_code == 422


# --- US-8: drawdown ---------------------------------------------------------------


def test_drawdown_reports_max_current_and_a_series(client: TestClient) -> None:
    """US-8 acceptance: the largest peak-to-trough declines over the period."""
    _add(client, "AAPL", "10")
    _add(client, "NVDA", "5")

    body = client.get("/portfolio/drawdown").json()

    assert Decimal(body["max_drawdown_pct"]) < 0
    assert Decimal(body["current_drawdown_pct"]) <= 0
    assert len(body["series"]) > 100
    assert body["observations"] > 0

    # Every point is a non-positive percentage.
    assert all(Decimal(p["drawdown_pct"]) <= 0 for p in body["series"])
    dates = [p["date"] for p in body["series"]]
    assert dates == sorted(dates)


def test_drawdown_episodes_are_ordered_deepest_first(client: TestClient) -> None:
    _add(client, "AAPL", "10")
    _add(client, "NVDA", "5")

    episodes = client.get("/portfolio/drawdown").json()["episodes"]
    assert len(episodes) > 0

    depths = [Decimal(e["depth_pct"]) for e in episodes]
    assert depths == sorted(depths)  # most negative first


def test_each_episode_is_internally_consistent(client: TestClient) -> None:
    _add(client, "AAPL", "10")
    _add(client, "NVDA", "5")

    for episode in client.get("/portfolio/drawdown").json()["episodes"]:
        assert episode["peak_date"] <= episode["trough_date"]
        assert Decimal(episode["depth_pct"]) < 0
        assert episode["decline_days"] >= 0
        if episode["recovered"]:
            assert episode["recovery_date"] >= episode["trough_date"]
            assert episode["recovery_days"] is not None
        else:
            assert episode["recovery_date"] is None
            assert episode["recovery_days"] is None


def test_max_drawdown_matches_the_deepest_episode(client: TestClient) -> None:
    _add(client, "AAPL", "10")
    _add(client, "NVDA", "5")

    body = client.get("/portfolio/drawdown").json()
    assert Decimal(body["episodes"][0]["depth_pct"]) == Decimal(body["max_drawdown_pct"])


def test_max_drawdown_matches_the_worst_point_of_the_series(client: TestClient) -> None:
    _add(client, "AAPL", "10")

    body = client.get("/portfolio/drawdown").json()
    worst = min(Decimal(p["drawdown_pct"]) for p in body["series"])
    assert worst == Decimal(body["max_drawdown_pct"])


def test_drawdown_of_an_empty_portfolio_does_not_fail(client: TestClient) -> None:
    body = client.get("/portfolio/drawdown").json()
    assert body["series"] == []
    assert body["episodes"] == []
    assert body["max_drawdown_pct"] is None


def test_drawdown_ignores_unpriceable_holdings(client: TestClient, provider: FakeProvider) -> None:
    _add(client, "AAPL", "10")
    _add(client, "MSFT", "5")
    provider.known = {"AAPL"}

    body = client.get("/portfolio/drawdown").json()
    assert len(body["series"]) > 100  # still computed from what can be priced


def test_drawdown_window_is_validated(client: TestClient) -> None:
    assert client.get("/portfolio/drawdown?days=10").status_code == 422
    assert client.get("/portfolio/drawdown?days=180").json()["window_days"] == 180
