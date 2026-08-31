"""Shared test fixtures.

Provides a ``TestClient`` backed by a fresh in-memory SQLite database with the ORM schema
created, and the ``get_session`` dependency overridden to use it. This exercises the real
routes and persistence without needing a running PostgreSQL instance.

Market data is served by :class:`tests.fakes.FakeProvider`, so the suite needs no network
and no API key while still running the real service, cache, and route code.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # register models on Base.metadata
from app.api.holdings import get_symbol_provider
from app.api.market_data import get_market_data_service
from app.core.database import Base, get_session
from app.data.service import MarketDataService
from app.main import app
from tests.fakes import FakeProvider


@pytest.fixture()
def provider() -> FakeProvider:
    """The fake market-data provider wired into the app for a test."""
    return FakeProvider()


@pytest.fixture()
def client(provider: FakeProvider) -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared in-memory connection for the whole test
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_session() -> Iterator[Session]:
        session = testing_session()
        try:
            yield session
        finally:
            session.close()

    def override_market_data_service() -> MarketDataService:
        return MarketDataService(testing_session(), provider)

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_market_data_service] = override_market_data_service
    app.dependency_overrides[get_symbol_provider] = lambda: provider

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()
