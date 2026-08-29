"""Database engine and session management.

A single SQLAlchemy engine is created for the process. Request handlers obtain a session
via the :func:`get_session` FastAPI dependency. Models will register against :class:`Base`.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# ``pool_pre_ping`` avoids handing out connections that the database has already dropped —
# important when the DB container restarts independently of the backend.
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a database session and closing it afterward."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_database() -> bool:
    """Return ``True`` if a trivial query against the database succeeds, else ``False``.

    Used by the health endpoint to report database connectivity without raising.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - health check must never propagate.
        return False
