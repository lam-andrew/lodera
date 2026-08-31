"""Tests for the risk API (US-5: volatility per holding and for the portfolio)."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from tests.fakes import FakeProvider


def _add(client: TestClient, ticker: str, quantity: str) -> None:
    assert (
        client.post("/holdings", json={"ticker": ticker, "quantity": quantity}).status_code == 201
    )


def test_risk_reports_volatility_for_each_holding_and_the_portfolio(
    client: TestClient,
) -> None:
    """US-5 acceptance: volatility for each holding AND for the portfolio."""
    _add(client, "AAPL", "10")
    _add(client, "NVDA", "5")

    body = client.get("/portfolio/risk").json()

    assert [h["ticker"] for h in body["holdings"]] == ["AAPL", "NVDA"]
    for holding in body["holdings"]:
        assert holding["volatility_pct"] is not None
        assert holding["band"] in {"low", "moderate", "high"}
        assert holding["observations"] > 0

    assert body["portfolio_volatility_pct"] is not None
    assert body["portfolio_band"] in {"low", "moderate", "high"}
    assert body["observations"] > 0


def test_a_more_volatile_holding_reports_higher_volatility(client: TestClient) -> None:
    """NVDA is seeded as the most volatile symbol and VTI the calmest."""
    _add(client, "NVDA", "1")
    _add(client, "VTI", "1")

    by_ticker = {h["ticker"]: h for h in client.get("/portfolio/risk").json()["holdings"]}
    assert Decimal(by_ticker["NVDA"]["volatility_pct"]) > Decimal(
        by_ticker["VTI"]["volatility_pct"]
    )


def test_portfolio_volatility_is_below_the_undiversified_figure(client: TestClient) -> None:
    """Diversification: the whole is less volatile than the weighted sum of its parts."""
    _add(client, "AAPL", "10")
    _add(client, "MSFT", "10")
    _add(client, "VTI", "10")

    body = client.get("/portfolio/risk").json()
    portfolio = Decimal(body["portfolio_volatility_pct"])
    undiversified = Decimal(body["undiversified_volatility_pct"])

    assert portfolio < undiversified
    assert Decimal(body["diversification_benefit_pct"]) == (undiversified - portfolio).quantize(
        Decimal("0.01")
    )


def test_single_holding_portfolio_matches_that_holding(client: TestClient) -> None:
    _add(client, "AAPL", "10")
    body = client.get("/portfolio/risk").json()
    assert body["portfolio_volatility_pct"] == body["holdings"][0]["volatility_pct"]


def test_empty_portfolio_reports_no_risk_rather_than_failing(client: TestClient) -> None:
    body = client.get("/portfolio/risk").json()
    assert body["holdings"] == []
    assert body["portfolio_volatility_pct"] is None
    assert body["portfolio_band"] is None


def test_unpriceable_holding_is_listed_without_volatility(
    client: TestClient, provider: FakeProvider
) -> None:
    """One holding losing price data must not sink the whole risk report."""
    _add(client, "AAPL", "10")
    _add(client, "MSFT", "5")
    provider.known = {"AAPL"}

    body = client.get("/portfolio/risk").json()
    by_ticker = {h["ticker"]: h for h in body["holdings"]}

    assert by_ticker["MSFT"]["volatility_pct"] is None
    assert by_ticker["AAPL"]["volatility_pct"] is not None
    # The portfolio figure still computes from what is priceable.
    assert body["portfolio_volatility_pct"] is not None


def test_window_is_configurable_and_validated(client: TestClient) -> None:
    _add(client, "AAPL", "10")
    assert client.get("/portfolio/risk?days=180").json()["window_days"] == 180
    assert client.get("/portfolio/risk?days=10").status_code == 422  # below the 30-day floor
    assert client.get("/portfolio/risk?days=99999").status_code == 422


def test_volatility_is_reported_as_a_percentage(client: TestClient) -> None:
    """A ~1.2% daily sigma annualizes to roughly 19%, not 0.19."""
    _add(client, "AAPL", "10")
    vol = Decimal(client.get("/portfolio/risk").json()["holdings"][0]["volatility_pct"])
    assert Decimal("5") < vol < Decimal("60")
