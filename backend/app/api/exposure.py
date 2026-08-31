"""Concentration (US-7) and drawdown (US-8) routes.

Both reuse the aligned price series that volatility and correlation already build, so every
metric on the dashboard describes the same window and the same trading days.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api._portfolio_series import load_portfolio_series
from app.api.market_data import ServiceDep
from app.api.schemas import (
    DrawdownEpisodeRead,
    DrawdownPointRead,
    OverlapGroupRead,
    OverweightPositionRead,
    PortfolioConcentrationRead,
    PortfolioDrawdownRead,
)
from app.core.database import get_session
from app.engines.risk import (
    OVERLAP_CORRELATION,
    OVERWEIGHT_MULTIPLE,
    Position,
    correlation_matrix,
    current_drawdown,
    drawdown_episodes,
    drawdown_series,
    effective_holdings,
    herfindahl_index,
    max_drawdown,
    overlapping_exposure,
    overweight_positions,
    top_n_weight,
)

router = APIRouter(prefix="/portfolio", tags=["risk"])

SessionDep = Annotated[Session, Depends(get_session)]

DEFAULT_WINDOW_DAYS = 365


def _pct(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value * 100)).quantize(Decimal("0.01"))


def _round(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(Decimal("0.01"))


@router.get("/concentration", response_model=PortfolioConcentrationRead)
def get_concentration(
    session: SessionDep,
    service: ServiceDep,
    days: Annotated[int, Query(ge=30, le=3650)] = DEFAULT_WINDOW_DAYS,
) -> PortfolioConcentrationRead:
    """Where the portfolio is overexposed (US-7).

    Reports both kinds of concentration: single positions that are simply large, and groups
    of holdings that move together closely enough to behave as one much larger position.
    """
    data = load_portfolio_series(session, service, days=days)

    priced = data.priced_tickers
    values = [float(data.values[t]) for t in priced]
    total = sum(values)

    if not priced or total <= 0:
        return PortfolioConcentrationRead(
            holdings_count=len(data.holdings),
            overweight=[],
            overlaps=[],
            overweight_multiple=Decimal(str(OVERWEIGHT_MULTIPLE)),
            overlap_threshold=Decimal(str(OVERLAP_CORRELATION)),
        )

    positions = [Position(t, v / total) for t, v in zip(priced, values, strict=True)]
    equal_weight = 1.0 / len(positions)

    matrix = correlation_matrix(data.matrix) if data.matrix else None
    overlaps = overlapping_exposure(positions, priced, matrix) if matrix is not None else []

    return PortfolioConcentrationRead(
        hhi=_round(herfindahl_index([p.weight for p in positions])),
        effective_holdings=_round(effective_holdings([p.weight for p in positions])),
        holdings_count=len(positions),
        top_1_pct=_pct(top_n_weight([p.weight for p in positions], 1)),
        top_3_pct=_pct(top_n_weight([p.weight for p in positions], 3)),
        top_5_pct=_pct(top_n_weight([p.weight for p in positions], 5)),
        overweight=[
            OverweightPositionRead(
                ticker=p.ticker,
                weight_pct=_pct(p.weight) or Decimal(0),
                times_equal_weight=_round(p.weight / equal_weight) or Decimal(0),
            )
            for p in overweight_positions(positions)
        ],
        overlaps=[
            OverlapGroupRead(
                tickers=g.tickers,
                combined_weight_pct=_pct(g.combined_weight) or Decimal(0),
                min_correlation=_round(g.min_correlation) or Decimal(0),
            )
            for g in overlaps
        ],
        overweight_multiple=Decimal(str(OVERWEIGHT_MULTIPLE)),
        overlap_threshold=Decimal(str(OVERLAP_CORRELATION)),
    )


@router.get("/drawdown", response_model=PortfolioDrawdownRead)
def get_drawdown(
    session: SessionDep,
    service: ServiceDep,
    days: Annotated[int, Query(ge=30, le=3650)] = DEFAULT_WINDOW_DAYS,
) -> PortfolioDrawdownRead:
    """The portfolio's worst historical declines (US-8).

    Portfolio value is reconstructed at today's share quantities, so the series shows how
    the *current* portfolio would have behaved through the window.
    """
    data = load_portfolio_series(session, service, days=days)
    ordered_dates, decimal_values = data.value_series()

    if not ordered_dates:
        return PortfolioDrawdownRead(episodes=[], series=[], window_days=days, observations=0)

    values = [float(v) for v in decimal_values]

    series = drawdown_series(values)
    episodes = drawdown_episodes(ordered_dates, values)

    return PortfolioDrawdownRead(
        max_drawdown_pct=_pct(max_drawdown(values)),
        current_drawdown_pct=_pct(current_drawdown(values)),
        episodes=[
            DrawdownEpisodeRead(
                depth_pct=_pct(e.depth) or Decimal(0),
                peak_date=e.peak_date,
                trough_date=e.trough_date,
                recovery_date=e.recovery_date,
                decline_days=e.decline_days,
                recovery_days=e.recovery_days,
                recovered=e.recovered,
            )
            for e in episodes
        ],
        series=[
            DrawdownPointRead(date=day, drawdown_pct=_pct(value) or Decimal(0))
            for day, value in zip(ordered_dates, series, strict=True)
        ],
        window_days=days,
        observations=max(len(values) - 1, 0),
    )
