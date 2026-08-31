"""Pydantic schemas for API request/response bodies (the wire contract).

These types define the JSON shapes exchanged with clients and are the source of truth for
the auto-generated OpenAPI documentation.
"""

from __future__ import annotations

import datetime as dt
import re
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

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


#: Prices serialize at a fixed scale so a response looks identical whether it came straight
#: from the provider or from the cache (the DB column is Numeric(18, 6), which round-trips
#: Decimal("100") as Decimal("100.000000")). Without this, the same request would return
#: "100" on a cache miss and "100.000000" on a hit.
_PRICE_SCALE = Decimal("0.000001")


class PriceBarRead(BaseModel):
    """One daily bar as returned by the API."""

    date: dt.date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    adj_close: Decimal
    volume: int

    @field_serializer("open", "high", "low", "close", "adj_close")
    def _serialize_price(self, value: Decimal) -> Decimal:
        return value.quantize(_PRICE_SCALE)


class PriceSeriesRead(BaseModel):
    """Daily prices for one symbol (US-4).

    ``source`` reports whether this response came from the local cache or a live provider
    call, which makes the caching behaviour (FR-6) visible to clients and tests.
    """

    ticker: str
    source: Literal["cache", "provider"]
    count: int
    start: dt.date | None
    end: dt.date | None
    bars: list[PriceBarRead]


class PositionRead(BaseModel):
    """A holding enriched with market data (US-1/US-3 + US-4).

    Price fields are nullable: a position is still reported when its price cannot be
    retrieved, so one bad symbol never hides the rest of the portfolio.
    """

    id: int
    ticker: str
    quantity: Decimal
    latest_price: Decimal | None = None
    market_value: Decimal | None = None
    weight_pct: Decimal | None = None
    price_as_of: dt.date | None = None


class PortfolioSummaryRead(BaseModel):
    """Portfolio positions with market values and the total."""

    positions: list[PositionRead]
    total_value: Decimal | None = None
    #: False when no position could be priced (e.g. market data unconfigured or offline).
    priced: bool


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


class HoldingRiskRead(BaseModel):
    """Risk figures for a single holding (US-5).

    ``volatility_pct`` is annualized, expressed as a percentage (18.70 == 18.7%). It is
    ``None`` when there is too little price history to estimate it meaningfully.
    """

    id: int
    ticker: str
    volatility_pct: Decimal | None = None
    band: Literal["low", "moderate", "high"] | None = None
    #: Number of daily returns the estimate is based on.
    observations: int


class PortfolioRiskRead(BaseModel):
    """Portfolio-level risk (US-5), with the per-holding breakdown."""

    holdings: list[HoldingRiskRead]
    portfolio_volatility_pct: Decimal | None = None
    portfolio_band: Literal["low", "moderate", "high"] | None = None
    #: Weighted average of standalone volatilities — what the portfolio would be if its
    #: holdings moved together perfectly. The gap to the actual figure is diversification.
    undiversified_volatility_pct: Decimal | None = None
    diversification_benefit_pct: Decimal | None = None
    window_days: int
    #: Daily returns shared by all priced holdings, backing the portfolio figure.
    observations: int


class ImportProblemRead(BaseModel):
    """A CSV row that could not be imported, reported back to the user (FR-3)."""

    row: int
    reason: str
    content: str


class ImportResultRead(BaseModel):
    """Outcome of a portfolio CSV import (US-2).

    Valid rows are imported even when others fail, so a single bad line never costs the
    user the whole upload.
    """

    added: list[str]
    updated: list[str]
    problems: list[ImportProblemRead]
    #: Rows deliberately ignored (cash lines, totals, disclaimer text) — not failures.
    skipped: int
    #: Which columns the parser matched, so the user can tell it read their file correctly.
    ticker_column: str | None = None
    quantity_column: str | None = None


class CorrelationPairRead(BaseModel):
    """Two holdings and how closely they move together (US-6)."""

    a: str
    b: str
    correlation: Decimal


class PortfolioCorrelationRead(BaseModel):
    """Correlation structure among holdings (US-6, FR-8).

    ``matrix[i][j]`` is the correlation between ``tickers[i]`` and ``tickers[j]``; a cell is
    ``None`` when it is undefined (a holding with no price variation over the window).
    """

    tickers: list[str]
    matrix: list[list[Decimal | None]]
    #: Pairs that move together most — where concentration hides.
    most_correlated: list[CorrelationPairRead]
    #: Pairs that move together least — where diversification comes from.
    least_correlated: list[CorrelationPairRead]
    average_correlation: Decimal | None = None
    window_days: int
    observations: int
    #: Reference points the UI uses to label a pair, exposed so client and server agree.
    high_threshold: Decimal
    low_threshold: Decimal


class PortfolioValuePointRead(BaseModel):
    """Portfolio market value on one trading day."""

    date: dt.date
    value: Decimal


class PortfolioHistoryRead(BaseModel):
    """Portfolio value over time at today's share quantities (US-10).

    Quantities are held constant, so this shows how the *current* portfolio would have
    moved — it is not a record of past trades. US-8 builds drawdown on this series.
    """

    points: list[PortfolioValuePointRead]
    start: dt.date | None = None
    end: dt.date | None = None


class OverweightPositionRead(BaseModel):
    """A position larger than its equal-weight share by the configured multiple (US-7)."""

    ticker: str
    weight_pct: Decimal
    #: How many times an equal-weight share this position is.
    times_equal_weight: Decimal


class OverlapGroupRead(BaseModel):
    """Holdings that move together closely enough to act as a single position (US-7)."""

    tickers: list[str]
    combined_weight_pct: Decimal
    min_correlation: Decimal


class PortfolioConcentrationRead(BaseModel):
    """Concentration and exposure (US-7, FR-9)."""

    #: Herfindahl-Hirschman Index of position weights, 1/n (equal) to 1 (single holding).
    hhi: Decimal | None = None
    #: 1 / HHI — equally-weighted positions that would be as concentrated as this portfolio.
    effective_holdings: Decimal | None = None
    holdings_count: int
    top_1_pct: Decimal | None = None
    top_3_pct: Decimal | None = None
    top_5_pct: Decimal | None = None
    overweight: list[OverweightPositionRead]
    overlaps: list[OverlapGroupRead]
    #: The equal-weight multiple used to flag a position, exposed so the UI can explain it.
    overweight_multiple: Decimal
    overlap_threshold: Decimal


class DrawdownEpisodeRead(BaseModel):
    """One peak-to-trough decline (US-8)."""

    depth_pct: Decimal
    peak_date: dt.date
    trough_date: dt.date
    recovery_date: dt.date | None = None
    decline_days: int
    recovery_days: int | None = None
    recovered: bool


class DrawdownPointRead(BaseModel):
    """Portfolio decline from its running peak on one trading day."""

    date: dt.date
    drawdown_pct: Decimal


class PortfolioDrawdownRead(BaseModel):
    """Historical drawdown (US-8, FR-10).

    Figures are realized historical facts about the window, not annualized rates.
    """

    max_drawdown_pct: Decimal | None = None
    current_drawdown_pct: Decimal | None = None
    episodes: list[DrawdownEpisodeRead]
    #: The underwater series, for plotting.
    series: list[DrawdownPointRead]
    window_days: int
    observations: int
