"""Tests for US-2: portfolio CSV / brokerage-export import (FR-2, FR-3).

The fixtures mimic the real shape of Fidelity, Schwab and Vanguard positions exports —
preamble title rows, fully quoted fields, ``$``/comma-formatted numbers, money-market and
"Account Total" rows, and trailing disclaimer paragraphs — because those quirks, not the
happy path, are what break naive CSV importers.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.data.csv_import import parse_portfolio_csv

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def upload(client: TestClient, name: str, data: bytes | None = None):  # type: ignore[no-untyped-def]
    payload = load(name) if data is None else data
    return client.post("/holdings/import", files={"file": (name, payload, "text/csv")})


# --- parser: real brokerage shapes --------------------------------------------


def test_parses_fidelity_export() -> None:
    result = parse_portfolio_csv(load("fidelity_positions.csv"))
    holdings = {h.ticker: h.quantity for h in result.holdings}

    assert holdings == {
        "AAPL": Decimal("1250"),
        "MSFT": Decimal("85"),
        "VOO": Decimal("40"),
    }
    # Money market, pending activity, blank line and disclaimer text are skipped, not errors.
    assert result.problems == []
    assert result.skipped >= 3
    assert result.ticker_column == "Symbol"
    assert result.quantity_column == "Quantity"


def test_parses_schwab_export_with_a_preamble_line() -> None:
    """The header is not row 1: Schwab opens with a title row."""
    result = parse_portfolio_csv(load("schwab_positions.csv"))
    holdings = {h.ticker: h.quantity for h in result.holdings}

    assert holdings == {"NVDA": Decimal("32"), "QQQ": Decimal("100")}
    assert result.problems == []  # "Cash & Cash Investments" and "Account Total" are skipped


def test_parses_vanguard_export_with_different_header_names() -> None:
    """Vanguard uses 'Shares' rather than 'Quantity'."""
    result = parse_portfolio_csv(load("vanguard_positions.csv"))
    holdings = {h.ticker: h.quantity for h in result.holdings}

    assert holdings == {"VTI": Decimal("150.2340"), "BND": Decimal("300.0000")}
    assert result.quantity_column == "Shares"


def test_parses_a_simple_hand_written_csv() -> None:
    result = parse_portfolio_csv(load("simple.csv"))
    assert {h.ticker: h.quantity for h in result.holdings} == {
        "AAPL": Decimal("10"),
        "MSFT": Decimal("5.5"),
    }


# --- parser: formatting quirks -------------------------------------------------


@pytest.mark.parametrize(
    ("csv_text", "expected"),
    [
        ('Symbol,Quantity\nAAPL,"1,234.567"\n', Decimal("1234.567")),
        ("Symbol,Quantity\nAAPL,$250\n", Decimal("250")),
        ("Symbol,Quantity\nAAPL, 42 \n", Decimal("42")),
    ],
)
def test_number_formats_are_normalized(csv_text: str, expected: Decimal) -> None:
    result = parse_portfolio_csv(csv_text.encode())
    assert result.holdings[0].quantity == expected


def test_utf8_bom_and_crlf_are_handled() -> None:
    data = "﻿Symbol,Quantity\r\nAAPL,10\r\n".encode()
    result = parse_portfolio_csv(data)
    assert [h.ticker for h in result.holdings] == ["AAPL"]


def test_class_share_tickers_are_accepted() -> None:
    result = parse_portfolio_csv(b"Symbol,Quantity\nBRK.B,3\n")
    assert result.holdings[0].ticker == "BRK.B"


def test_duplicate_symbols_are_combined() -> None:
    """The same holding across two accounts in one export should sum, not conflict."""
    result = parse_portfolio_csv(b"Symbol,Quantity\nAAPL,10\nAAPL,15\n")
    assert [(h.ticker, h.quantity) for h in result.holdings] == [("AAPL", Decimal("25"))]


def test_file_without_recognizable_columns_is_reported() -> None:
    result = parse_portfolio_csv(b"Name,Address\nBob,123 Main St\n")
    assert result.holdings == []
    assert "Could not find a ticker column" in result.problems[0].reason


def test_empty_file_is_reported() -> None:
    assert parse_portfolio_csv(b"").problems[0].reason == "The file is empty."


# --- parser: bad rows are reported, good rows survive (FR-3) -------------------


def test_bad_rows_are_reported_with_reasons_and_row_numbers() -> None:
    result = parse_portfolio_csv(load("messy.csv"))

    holdings = {h.ticker: h.quantity for h in result.holdings}
    assert holdings == {"AAPL": Decimal("125"), "TSLA": Decimal("1000.5")}  # 100 + 25 combined

    reasons = {p.row_number: p.reason for p in result.problems}
    assert any("not a valid ticker" in r for r in reasons.values())  # NOT A TICKER
    assert any("Could not read a share quantity" in r for r in reasons.values())  # abc
    assert any("must be positive" in r for r in reasons.values())  # -5 and 0
    # Row numbers are 1-based file lines so the user can find them.
    assert all(p.row_number > 1 for p in result.problems)


# --- API ----------------------------------------------------------------------


def test_import_adds_holdings_and_they_appear_in_the_portfolio(client: TestClient) -> None:
    """US-2 AC 1: a correctly formatted CSV puts all valid holdings in the portfolio."""
    resp = upload(client, "vanguard_positions.csv")
    assert resp.status_code == 200
    body = resp.json()

    assert sorted(body["added"]) == ["BND", "VTI"]
    assert body["problems"] == []

    listed = {h["ticker"] for h in client.get("/holdings").json()}
    assert {"VTI", "BND"} <= listed


def test_import_reports_bad_rows_while_importing_good_ones(client: TestClient) -> None:
    """US-2 AC 2: valid rows import, unparseable rows are reported back."""
    body = upload(client, "messy.csv").json()

    assert "AAPL" in body["added"]
    assert len(body["problems"]) >= 3
    assert all({"row", "reason", "content"} <= set(p) for p in body["problems"])

    # The good row really landed.
    assert "AAPL" in {h["ticker"] for h in client.get("/holdings").json()}


def test_import_updates_an_existing_holding(client: TestClient) -> None:
    """An export is a snapshot of current positions, so it replaces the quantity."""
    client.post("/holdings", json={"ticker": "VTI", "quantity": "1"})

    body = upload(client, "vanguard_positions.csv").json()
    assert "VTI" in body["updated"]

    held = {h["ticker"]: Decimal(h["quantity"]) for h in client.get("/holdings").json()}
    assert held["VTI"] == Decimal("150.234")


def test_import_rejects_symbols_the_provider_does_not_recognize(client: TestClient) -> None:
    body = upload(client, "unknown.csv", b"Symbol,Quantity\nAAPL,10\nZZZZ,5\n").json()

    assert body["added"] == ["AAPL"]
    assert any("Unrecognized ticker 'ZZZZ'" in p["reason"] for p in body["problems"])


def test_import_reports_the_columns_it_matched(client: TestClient) -> None:
    body = upload(client, "vanguard_positions.csv").json()
    assert body["ticker_column"] == "Symbol"
    assert body["quantity_column"] == "Shares"


def test_empty_upload_is_rejected(client: TestClient) -> None:
    assert upload(client, "empty.csv", b"   ").status_code == 422


def test_oversized_upload_is_rejected(client: TestClient) -> None:
    huge = b"Symbol,Quantity\n" + b"AAPL,1\n" * 400_000
    assert upload(client, "huge.csv", huge).status_code == 413


# --- a real Schwab export ---------------------------------------------------------


def test_parses_a_real_schwab_export() -> None:
    """Regression for the format an actual Schwab "Positions" export uses.

    Two things broke on the real file that the earlier hand-built fixture did not have:
    the quantity column is written ``"Qty (Quantity)"`` rather than ``"Quantity"``, and the
    footer row is labelled ``"Positions Total"``. Holdings here are substituted — the
    structure is what matters and this repository is public.
    """
    result = parse_portfolio_csv(load("schwab_positions_real.csv"))

    assert {h.ticker: h.quantity for h in result.holdings} == {
        "AAPL": Decimal("3"),
        "MSFT": Decimal("2.0078"),
        "NVDA": Decimal("0.4555"),
        "QQQ": Decimal("10.0876"),
        "VOO": Decimal("20.3868"),
    }
    # "Cash & Cash Investments" and "Positions Total" are structural, not failures.
    assert result.problems == []
    assert result.skipped >= 2
    assert result.quantity_column == "Qty (Quantity)"


def test_short_long_header_forms_are_both_matched() -> None:
    """Schwab labels columns "Short (Long)"; either half should identify the column."""
    for header in ("Qty (Quantity)", "Quantity (Qty)", "Shares (Qty)"):
        csv_text = f'Symbol,"{header}"\nAAPL,7\n'
        result = parse_portfolio_csv(csv_text.encode())
        assert [h.quantity for h in result.holdings] == [Decimal("7")], header


def test_unrecognized_columns_are_reported_with_what_was_found() -> None:
    """A user cannot fix their file unless told which columns we actually saw."""
    result = parse_portfolio_csv(b"Account,Description,Value\nX,Something,10\n")
    reason = result.problems[0].reason
    assert "Could not find a ticker column" in reason
    assert "Columns found: Account, Description, Value" in reason


def test_a_rate_limited_provider_does_not_reject_valid_tickers(client: TestClient) -> None:
    """Regression: hitting the provider's hourly limit mid-import must not lose holdings.

    Previously an unreachable provider fell back to a small bundled symbol list, so a real
    Schwab export part-way through validation reported ten genuine tickers as
    "Unrecognized" — wrong, and nothing the user could act on. We cannot disprove a symbol
    when the provider is down, so it is accepted; a truly bad one still fails later when
    pricing finds nothing.
    """
    from app.api.holdings import get_symbol_provider
    from app.data.provider import RateLimitedError
    from app.main import app

    class RateLimited:
        def get_daily_prices(self, ticker, start, end):  # type: ignore[no-untyped-def]
            raise RateLimitedError("hourly allocation exceeded")

        def symbol_exists(self, ticker: str) -> bool:
            raise RateLimitedError("hourly allocation exceeded")

    app.dependency_overrides[get_symbol_provider] = lambda: RateLimited()
    try:
        body = upload(client, "obscure.csv", b"Symbol,Quantity\nHOOD,20\nVXUS,11\nARKX,20\n").json()
    finally:
        app.dependency_overrides.pop(get_symbol_provider, None)

    assert sorted(body["added"]) == ["ARKX", "HOOD", "VXUS"]
    assert body["problems"] == []
