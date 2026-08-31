"""Tests for US-1: add a holding manually."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient


def test_add_valid_holding_then_appears_in_list(client: TestClient) -> None:
    resp = client.post("/holdings", json={"ticker": "AAPL", "quantity": "10"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert Decimal(str(body["quantity"])) == Decimal("10")
    assert "id" in body

    listing = client.get("/holdings")
    assert listing.status_code == 200
    assert [h["ticker"] for h in listing.json()] == ["AAPL"]


def test_empty_portfolio_lists_nothing(client: TestClient) -> None:
    resp = client.get("/holdings")
    assert resp.status_code == 200
    assert resp.json() == []


def test_ticker_is_normalized(client: TestClient) -> None:
    resp = client.post("/holdings", json={"ticker": "  aapl ", "quantity": "1.5"})
    assert resp.status_code == 201
    assert resp.json()["ticker"] == "AAPL"


def test_fractional_quantity_is_allowed(client: TestClient) -> None:
    resp = client.post("/holdings", json={"ticker": "VTI", "quantity": "2.75"})
    assert resp.status_code == 201
    assert Decimal(str(resp.json()["quantity"])) == Decimal("2.75")


def test_unrecognized_ticker_is_rejected_and_adds_nothing(client: TestClient) -> None:
    resp = client.post("/holdings", json={"ticker": "ZZZZ", "quantity": "5"})
    assert resp.status_code == 422
    assert "Unrecognized" in resp.json()["detail"]
    assert client.get("/holdings").json() == []


def test_invalid_ticker_format_is_rejected(client: TestClient) -> None:
    resp = client.post("/holdings", json={"ticker": "123", "quantity": "1"})
    assert resp.status_code == 422


def test_non_positive_quantity_is_rejected(client: TestClient) -> None:
    for bad in ("0", "-3"):
        resp = client.post("/holdings", json={"ticker": "AAPL", "quantity": bad})
        assert resp.status_code == 422


def test_duplicate_ticker_is_rejected(client: TestClient) -> None:
    assert client.post("/holdings", json={"ticker": "MSFT", "quantity": "4"}).status_code == 201
    dup = client.post("/holdings", json={"ticker": "MSFT", "quantity": "9"})
    assert dup.status_code == 409
    assert "already in your portfolio" in dup.json()["detail"]
