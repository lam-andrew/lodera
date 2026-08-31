"""Pydantic schemas for API request/response bodies (the wire contract).

These types define the JSON shapes exchanged with clients and are the source of truth for
the auto-generated OpenAPI documentation.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Basic ticker shape (e.g. AAPL, BRK.B). Recognition against real symbols is a separate,
# domain-level check performed in the route (see app.data.symbols).
_TICKER_RE = re.compile(r"^[A-Z]{1,6}(\.[A-Z]{1,2})?$")


class HealthResponse(BaseModel):
    """Liveness/readiness payload returned by ``GET /health``."""

    status: Literal["ok"] = "ok"
    service: str
    version: str
    environment: str
    database: Literal["connected", "unavailable"]
    # Whether a market-data API key is configured (US-4). "unconfigured" is a valid state:
    # the app runs without it, but price-backed risk analysis needs it.
    market_data: Literal["configured", "unconfigured"]


class HoldingCreate(BaseModel):
    """Request body for adding a holding (US-1): a ticker and a share quantity."""

    ticker: str = Field(min_length=1, max_length=12, examples=["AAPL"])
    quantity: Decimal = Field(gt=0, examples=["10"])

    @field_validator("ticker")
    @classmethod
    def _normalize_ticker(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not _TICKER_RE.match(normalized):
            raise ValueError("Ticker must be 1-6 letters, optionally like 'BRK.B'.")
        return normalized


class HoldingUpdate(BaseModel):
    """Request body for editing a holding (US-3). Only the quantity is editable; to change
    the ticker, delete the holding and add the new one."""

    quantity: Decimal = Field(gt=0, examples=["12.5"])


class HoldingRead(BaseModel):
    """A stored holding, as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    quantity: Decimal
