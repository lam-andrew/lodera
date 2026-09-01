"""Holdings routes (US-1: add a holding manually; US-3: view, edit, delete).

Part of the public API contract. Persists holdings for the MVP's single default portfolio
(user scoping arrives with auth, US-13). Ticker recognition uses the stopgap validator in
:mod:`app.data.symbols` until US-4 wires real market data.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import CurrentUser
from app.api.schemas import HoldingCreate, HoldingRead, HoldingUpdate
from app.core.config import settings
from app.core.database import get_session
from app.data.provider import MarketDataError, MarketDataProvider
from app.data.service import build_provider
from app.data.symbols import is_recognized_symbol
from app.models import Holding, Portfolio

router = APIRouter(prefix="/holdings", tags=["holdings"])

# FastAPI dependency type (the Annotated form avoids a call in the default argument).
SessionDep = Annotated[Session, Depends(get_session)]

DEFAULT_PORTFOLIO_NAME = "Personal portfolio"


def get_symbol_provider() -> MarketDataProvider | None:
    """The provider used to validate tickers, or ``None`` when market data isn't configured
    (then the bundled offline fallback applies). Overridable in tests."""
    if not settings.market_data_configured:
        return None
    try:
        return build_provider()
    except MarketDataError:
        return None


ProviderDep = Annotated[MarketDataProvider | None, Depends(get_symbol_provider)]


def _get_default_portfolio(session: Session, user_id: int) -> Portfolio | None:
    """The signed-in user's portfolio.

    Every read and write funnels through this (or its create-if-missing sibling), which is
    what keeps one account's holdings invisible to another.
    """
    return session.scalar(select(Portfolio).where(Portfolio.user_id == user_id))


def _get_or_create_default_portfolio(session: Session, user_id: int) -> Portfolio:
    portfolio = _get_default_portfolio(session, user_id)
    if portfolio is None:
        portfolio = Portfolio(user_id=user_id, name=DEFAULT_PORTFOLIO_NAME)
        session.add(portfolio)
        session.commit()
        session.refresh(portfolio)
    return portfolio


@router.get("", response_model=list[HoldingRead])
def list_holdings(session: SessionDep, user: CurrentUser) -> list[Holding]:
    """List the holdings in the portfolio (empty until the first one is added)."""
    portfolio = _get_default_portfolio(session, user.id)
    if portfolio is None:
        return []
    return list(
        session.scalars(
            select(Holding).where(Holding.portfolio_id == portfolio.id).order_by(Holding.ticker)
        )
    )


@router.post("", response_model=HoldingRead, status_code=status.HTTP_201_CREATED)
def add_holding(
    payload: HoldingCreate, session: SessionDep, provider: ProviderDep, user: CurrentUser
) -> Holding:
    """Add a holding by ticker and share quantity.

    Rejects an unrecognized ticker (422) and a ticker already in the portfolio (409); the
    quantity and ticker shape are validated by the request schema. Recognition is checked
    against the market-data provider when configured (US-4).
    """
    if not is_recognized_symbol(payload.ticker, provider):
        raise HTTPException(
            status_code=422,  # Unprocessable Content (validation-style rejection)
            detail=f"Unrecognized ticker '{payload.ticker}'. Check the symbol and try again.",
        )

    portfolio = _get_or_create_default_portfolio(session, user.id)

    already_held = session.scalar(
        select(Holding).where(
            Holding.portfolio_id == portfolio.id, Holding.ticker == payload.ticker
        )
    )
    if already_held is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{payload.ticker} is already in your portfolio; edit its quantity instead.",
        )

    holding = Holding(portfolio_id=portfolio.id, ticker=payload.ticker, quantity=payload.quantity)
    session.add(holding)
    session.commit()
    session.refresh(holding)
    return holding


def _get_owned_holding(session: Session, holding_id: int, user_id: int) -> Holding:
    """Fetch a holding in the default portfolio, or raise 404.

    Scoping the lookup to the user's portfolio (not just the id) is what stops one account
    from reading or editing another's holdings — a bare id lookup would be an IDOR.
    """
    portfolio = _get_default_portfolio(session, user_id)
    holding = (
        None
        if portfolio is None
        else session.scalar(
            select(Holding).where(Holding.id == holding_id, Holding.portfolio_id == portfolio.id)
        )
    )
    if holding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="That holding no longer exists.",
        )
    return holding


@router.patch("/{holding_id}", response_model=HoldingRead)
def update_holding(
    holding_id: int, payload: HoldingUpdate, session: SessionDep, user: CurrentUser
) -> Holding:
    """Edit a holding's share quantity (US-3). The new quantity must be positive; to remove
    a position entirely, delete it instead."""
    holding = _get_owned_holding(session, holding_id, user.id)
    holding.quantity = payload.quantity
    session.commit()
    session.refresh(holding)
    return holding


@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(holding_id: int, session: SessionDep, user: CurrentUser) -> None:
    """Remove a holding from the portfolio (US-3), excluding it from further analysis."""
    holding = _get_owned_holding(session, holding_id, user.id)
    session.delete(holding)
    session.commit()
