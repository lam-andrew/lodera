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


# --- US-6: correlation ---------------------------------------------------------


def test_correlation_returns_a_symmetric_matrix_for_the_holdings(client: TestClient) -> None:
    """US-6 acceptance: with 2+ priced holdings, the correlation structure is displayed."""
    _add(client, "AAPL", "10")
    _add(client, "MSFT", "5")
    _add(client, "VTI", "8")

    body = client.get("/portfolio/correlation").json()

    assert body["tickers"] == ["AAPL", "MSFT", "VTI"]
    matrix = body["matrix"]
    assert len(matrix) == 3 and all(len(row) == 3 for row in matrix)

    for i in range(3):
        assert Decimal(matrix[i][i]) == Decimal("1.00")  # diagonal
        for j in range(3):
            assert matrix[i][j] == matrix[j][i]  # symmetric
            assert Decimal("-1") <= Decimal(matrix[i][j]) <= Decimal("1")

    assert body["observations"] > 0
    assert body["average_correlation"] is not None


def test_correlation_surfaces_most_and_least_correlated_pairs(client: TestClient) -> None:
    _add(client, "AAPL", "10")
    _add(client, "MSFT", "5")
    _add(client, "NVDA", "3")

    body = client.get("/portfolio/correlation").json()

    # 3 holdings -> 3 distinct pairs, never self-pairs or duplicates.
    assert len(body["most_correlated"]) == 3
    for pair in body["most_correlated"]:
        assert pair["a"] != pair["b"]

    top = [Decimal(p["correlation"]) for p in body["most_correlated"]]
    assert top == sorted(top, reverse=True)

    bottom = [Decimal(p["correlation"]) for p in body["least_correlated"]]
    assert bottom == sorted(bottom)


def test_correlation_needs_two_holdings(client: TestClient) -> None:
    _add(client, "AAPL", "10")
    body = client.get("/portfolio/correlation").json()
    assert body["tickers"] == []
    assert body["matrix"] == []
    assert body["average_correlation"] is None


def test_correlation_of_an_empty_portfolio_does_not_fail(client: TestClient) -> None:
    body = client.get("/portfolio/correlation").json()
    assert body["tickers"] == []
    assert body["matrix"] == []


def test_correlation_excludes_unpriceable_holdings(
    client: TestClient, provider: FakeProvider
) -> None:
    _add(client, "AAPL", "10")
    _add(client, "MSFT", "5")
    _add(client, "NVDA", "3")
    provider.known = {"AAPL", "MSFT"}

    body = client.get("/portfolio/correlation").json()
    assert body["tickers"] == ["AAPL", "MSFT"]
    assert len(body["matrix"]) == 2


def test_correlation_window_is_validated(client: TestClient) -> None:
    _add(client, "AAPL", "10")
    _add(client, "MSFT", "5")
    assert client.get("/portfolio/correlation?days=180").json()["window_days"] == 180
    assert client.get("/portfolio/correlation?days=10").status_code == 422


def test_correlation_thresholds_are_exposed(client: TestClient) -> None:
    """Client and server must agree on what counts as 'high', so the server states it."""
    body = client.get("/portfolio/correlation").json()
    assert Decimal(body["high_threshold"]) == Decimal("0.75")
    assert Decimal(body["low_threshold"]) == Decimal("0.30")
