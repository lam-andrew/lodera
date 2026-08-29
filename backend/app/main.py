"""FastAPI application entry point.

Constructs the app, wires CORS for the frontend, and mounts the API router that defines the
backend's public contract. Run with: ``uvicorn app.main:app``.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    """Application factory — builds and configures the FastAPI instance."""
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        summary="Portfolio risk intelligence API. Measures, contextualizes, and explains "
        "risk — it does not predict prices, execute trades, or give investment advice.",
    )

    # The frontend is a separate origin; allow it to call the API contract over CORS.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount the public API contract. All client-facing routes live under this router.
    app.include_router(api_router)

    return app


app = create_app()
