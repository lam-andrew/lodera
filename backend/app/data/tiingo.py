"""Tiingo implementation of :class:`~app.data.provider.MarketDataProvider` (ADR 0011).

Talks to Tiingo's end-of-day API and converts its JSON into provider-neutral
:class:`~app.data.provider.PriceBar` values. Prices are parsed via ``str`` into ``Decimal``
so we never introduce binary-float error into money.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

from app.data.provider import (
    MarketDataError,
    PriceBar,
    RateLimitedError,
    UnknownSymbolError,
)

_BASE_URL = "https://api.tiingo.com/tiingo/daily"
_TIMEOUT = httpx.Timeout(15.0)


def _to_decimal(value: Any, field: str, ticker: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise MarketDataError(f"Bad {field!r} for {ticker} in provider response") from exc


class TiingoProvider:
    """Fetches end-of-day prices from Tiingo."""

    def __init__(self, api_key: str, *, client: httpx.Client | None = None) -> None:
        if not api_key.strip():
            raise MarketDataError("Tiingo API key is not configured.")
        self._api_key = api_key.strip()
        self._client = client

    def _request(self, path: str, params: dict[str, str] | None = None) -> Any:
        query = {"token": self._api_key, **(params or {})}
        headers = {"Content-Type": "application/json"}
        try:
            if self._client is not None:
                response = self._client.get(f"{_BASE_URL}{path}", params=query, headers=headers)
            else:
                with httpx.Client(timeout=_TIMEOUT) as client:
                    response = client.get(f"{_BASE_URL}{path}", params=query, headers=headers)
        except httpx.HTTPError as exc:
            raise MarketDataError(f"Could not reach the market-data provider: {exc}") from exc

        if response.status_code == 404:
            raise UnknownSymbolError("Symbol not recognized by the market-data provider.")
        if response.status_code == 429:
            raise RateLimitedError("Market-data rate limit reached; try again later.")
        if response.status_code in (401, 403):
            raise MarketDataError("Market-data provider rejected the API key.")
        if response.status_code >= 400:
            raise MarketDataError(f"Market-data provider error (HTTP {response.status_code}).")

        try:
            return response.json()
        except ValueError as exc:
            raise MarketDataError("Market-data provider returned invalid JSON.") from exc

    def get_daily_prices(self, ticker: str, start: date, end: date) -> list[PriceBar]:
        payload = self._request(
            f"/{ticker.upper()}/prices",
            {"startDate": start.isoformat(), "endDate": end.isoformat()},
        )
        if not isinstance(payload, list):
            raise MarketDataError("Unexpected price payload from the market-data provider.")

        bars: list[PriceBar] = []
        for row in payload:
            if not isinstance(row, dict) or "date" not in row:
                continue
            try:
                # Tiingo returns e.g. "2026-08-20T00:00:00.000Z"; keep the calendar date.
                bar_date = datetime.fromisoformat(str(row["date"]).replace("Z", "+00:00")).date()
            except ValueError as exc:
                raise MarketDataError(f"Bad date for {ticker} in provider response") from exc

            # Fall back to close when a provider omits the adjusted series.
            adj_close = row.get("adjClose", row.get("close"))
            bars.append(
                PriceBar(
                    date=bar_date,
                    open=_to_decimal(row.get("open", row.get("close")), "open", ticker),
                    high=_to_decimal(row.get("high", row.get("close")), "high", ticker),
                    low=_to_decimal(row.get("low", row.get("close")), "low", ticker),
                    close=_to_decimal(row.get("close"), "close", ticker),
                    adj_close=_to_decimal(adj_close, "adjClose", ticker),
                    volume=int(row.get("volume") or 0),
                )
            )

        bars.sort(key=lambda bar: bar.date)
        return bars

    def symbol_exists(self, ticker: str) -> bool:
        try:
            payload = self._request(f"/{ticker.upper()}")
        except UnknownSymbolError:
            return False
        # Tiingo answers 200 with an empty/blank ticker for some unlisted symbols.
        return isinstance(payload, dict) and bool(str(payload.get("ticker", "")).strip())
