"""Holdings routes (US-1: add a holding manually; US-3 later: edit/delete).

Part of the public API contract. Persists holdings for the MVP's single default portfolio
(user scoping arrives with auth, US-13). Ticker recognition uses the stopgap validator in
:mod:`app.data.symbols` until US-4 wires real market data.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import HoldingCreate, HoldingRead
from app.core.database import get_session
from app.data.symbols import is_known_symbol
from app.models import Holding, Portfolio

router = APIRouter(prefix="/holdings", tags=["holdings"])

# FastAPI dependency type (the Annotated form avoids a call in the default argument).
SessionDep = Annotated[Session, Depends(get_session)]

DEFAULT_PORTFOLIO_NAME = "Personal portfolio"


def _get_default_portfolio(session: Session) -> Portfolio | None:
    return session.scalar(select(Portfolio).where(Portfolio.name == DEFAULT_PORTFOLIO_NAME))


def _get_or_create_default_portfolio(session: Session) -> Portfolio:
    portfolio = _get_default_portfolio(session)
    if portfolio is None:
        portfolio = Portfolio(name=DEFAULT_PORTFOLIO_NAME)
        session.add(portfolio)
        session.commit()
        session.refresh(portfolio)
    return portfolio


@router.get("", response_model=list[HoldingRead])
def list_holdings(session: SessionDep) -> list[Holding]:
    """List the holdings in the portfolio (empty until the first one is added)."""
    portfolio = _get_default_portfolio(session)
    if portfolio is None:
        return []
    return list(
        session.scalars(
            select(Holding).where(Holding.portfolio_id == portfolio.id).order_by(Holding.ticker)
        )
    )


@router.post("", response_model=HoldingRead, status_code=status.HTTP_201_CREATED)
def add_holding(payload: HoldingCreate, session: SessionDep) -> Holding:
    """Add a holding by ticker and share quantity.

    Rejects an unrecognized ticker (422) and a ticker already in the portfolio (409); the
    quantity and ticker shape are validated by the request schema.
    """
    if not is_known_symbol(payload.ticker):
        raise HTTPException(
            status_code=422,  # Unprocessable Content (validation-style rejection)
            detail=f"Unrecognized ticker '{payload.ticker}'. Check the symbol and try again.",
        )

    portfolio = _get_or_create_default_portfolio(session)

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
