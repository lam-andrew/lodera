"""Portfolio CSV import (US-2, FR-2/FR-3).

Accepts a CSV or brokerage export, parses it with :mod:`app.data.csv_import`, and persists
the rows it can use. Rows it cannot use are returned to the caller rather than aborting the
import: the acceptance criterion is explicitly that valid rows land *and* bad rows are
reported.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import select

from app.api.auth import CurrentUser
from app.api.holdings import (
    ProviderDep,
    SessionDep,
    _get_or_create_default_portfolio,
)
from app.api.schemas import ImportProblemRead, ImportResultRead
from app.data.csv_import import parse_portfolio_csv
from app.data.provider import MarketDataError
from app.data.symbols import is_recognized_symbol
from app.models import Holding

router = APIRouter(prefix="/holdings", tags=["holdings"])

#: Positions files are small; anything larger is not a portfolio export.
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


@router.post("/import", response_model=ImportResultRead)
def import_holdings(
    session: SessionDep,
    provider: ProviderDep,
    user: CurrentUser,
    file: Annotated[UploadFile, File(description="CSV or brokerage positions export")],
) -> ImportResultRead:
    """Import holdings from a CSV / brokerage export.

    A ticker already in the portfolio has its quantity **updated** to the file's value —
    an export represents current positions, so it should replace rather than accumulate.
    """
    raw = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,  # Content Too Large
            detail="That file is larger than 2 MB. Please upload a positions export.",
        )
    if not raw.strip():
        raise HTTPException(status_code=422, detail="The uploaded file is empty.")

    parsed = parse_portfolio_csv(raw)

    problems = [
        ImportProblemRead(row=p.row_number, reason=p.reason, content=p.content[:120])
        for p in parsed.problems
    ]

    # Nothing usable at all: surface the failure rather than reporting a silent success.
    if not parsed.holdings and problems:
        return ImportResultRead(
            added=[],
            updated=[],
            problems=problems,
            skipped=parsed.skipped,
            ticker_column=parsed.ticker_column,
            quantity_column=parsed.quantity_column,
        )

    portfolio = _get_or_create_default_portfolio(session, user.id)
    existing = {
        holding.ticker: holding
        for holding in session.scalars(select(Holding).where(Holding.portfolio_id == portfolio.id))
    }

    added: list[str] = []
    updated: list[str] = []

    for row in parsed.holdings:
        # Reject symbols the market-data provider does not recognize, but never let a
        # provider outage block the import — that check degrades to the offline fallback.
        try:
            recognized = is_recognized_symbol(row.ticker, provider)
        except MarketDataError:
            recognized = True
        if not recognized:
            problems.append(
                ImportProblemRead(
                    row=row.row_number,
                    reason=f"Unrecognized ticker '{row.ticker}'.",
                    content=row.ticker,
                )
            )
            continue

        held = existing.get(row.ticker)
        if held is None:
            session.add(
                Holding(portfolio_id=portfolio.id, ticker=row.ticker, quantity=row.quantity)
            )
            added.append(row.ticker)
        else:
            held.quantity = row.quantity
            updated.append(row.ticker)

    session.commit()

    return ImportResultRead(
        added=added,
        updated=updated,
        problems=problems,
        skipped=parsed.skipped,
        ticker_column=parsed.ticker_column,
        quantity_column=parsed.quantity_column,
    )
