"""Application configuration, loaded from environment variables.

All external configuration (database DSN, allowed CORS origins, etc.) is supplied via the
environment — never hard-coded and never committed. See ``.env.example`` at the repo root
for the full list of variables.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings resolved from environment variables (prefixed ``LODERA_``).

    Defaults are development-friendly and match ``docker-compose.yml`` so the stack boots
    with zero manual configuration; override them via the environment in other contexts.
    """

    model_config = SettingsConfigDict(
        env_prefix="LODERA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application metadata
    app_name: str = "Lodera API"
    environment: str = "development"

    # Database (PostgreSQL 16 + pgvector). Async-agnostic SQLAlchemy DSN.
    database_url: str = "postgresql+psycopg://lodera:lodera@db:5432/lodera"

    # CORS: origins allowed to call the API (the frontend dev server by default).
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
"""Process-wide settings singleton. Import this rather than instantiating ``Settings``."""
