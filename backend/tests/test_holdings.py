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


# --- US-3: view, edit, delete -------------------------------------------------


def _add(client: TestClient, ticker: str, quantity: str) -> int:
    resp = client.post("/holdings", json={"ticker": ticker, "quantity": quantity})
    assert resp.status_code == 201
    return int(resp.json()["id"])


def test_edit_quantity_is_saved(client: TestClient) -> None:
    holding_id = _add(client, "AAPL", "10")

    resp = client.patch(f"/holdings/{holding_id}", json={"quantity": "12.5"})
    assert resp.status_code == 200
    assert Decimal(str(resp.json()["quantity"])) == Decimal("12.5")

    # ...and is reflected in the list the analysis reads from.
    listed = client.get("/holdings").json()
    assert Decimal(str(listed[0]["quantity"])) == Decimal("12.5")


def test_edit_rejects_non_positive_quantity(client: TestClient) -> None:
    holding_id = _add(client, "AAPL", "10")
    for bad in ("0", "-2"):
        assert client.patch(f"/holdings/{holding_id}", json={"quantity": bad}).status_code == 422
    # unchanged
    assert Decimal(str(client.get("/holdings").json()[0]["quantity"])) == Decimal("10")


def test_edit_unknown_holding_returns_404(client: TestClient) -> None:
    assert client.patch("/holdings/999", json={"quantity": "1"}).status_code == 404


def test_delete_removes_holding_from_further_analysis(client: TestClient) -> None:
    keep = _add(client, "AAPL", "10")
    drop = _add(client, "MSFT", "4")

    assert client.delete(f"/holdings/{drop}").status_code == 204

    remaining = client.get("/holdings").json()
    assert [h["ticker"] for h in remaining] == ["AAPL"]
    assert [h["id"] for h in remaining] == [keep]


def test_delete_unknown_holding_returns_404(client: TestClient) -> None:
    assert client.delete("/holdings/999").status_code == 404


def test_deleted_ticker_can_be_added_again(client: TestClient) -> None:
    holding_id = _add(client, "AAPL", "10")
    assert client.delete(f"/holdings/{holding_id}").status_code == 204
    # the unique (portfolio, ticker) constraint must not block re-adding
    assert client.post("/holdings", json={"ticker": "AAPL", "quantity": "3"}).status_code == 201
