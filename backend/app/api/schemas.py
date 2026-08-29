"""Pydantic schemas for API request/response bodies (the wire contract).

These types define the JSON shapes exchanged with clients and are the source of truth for
the auto-generated OpenAPI documentation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness/readiness payload returned by ``GET /health``."""

    status: Literal["ok"] = "ok"
    service: str
    version: str
    environment: str
    database: Literal["connected", "unavailable"]
