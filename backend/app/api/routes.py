"""Top-level API router.

Aggregates the versioned/feature routers that make up the backend's public contract. For
the Sprint 1 skeleton this is just the health check; portfolio, market-data, and risk
routes are added here as their user stories land.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.api import exposure, holdings, imports, market_data, portfolio, risk
from app.api.schemas import HealthResponse
from app.core.config import settings
from app.core.database import check_database

api_router = APIRouter()
api_router.include_router(holdings.router)
api_router.include_router(imports.router)
api_router.include_router(market_data.router)
api_router.include_router(portfolio.router)
api_router.include_router(risk.router)
api_router.include_router(exposure.router)


@api_router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Report service liveness and database connectivity.

    Always returns ``200`` so the frontend and orchestrators can distinguish "backend up,
    database down" from "backend down". The ``database`` field carries the DB status.
    """
    return HealthResponse(
        service=settings.app_name,
        version=__version__,
        environment=settings.environment,
        database="connected" if check_database() else "unavailable",
        market_data="configured" if settings.market_data_configured else "unconfigured",
    )
