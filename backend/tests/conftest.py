"""Shared test fixtures.

The ``client`` fixture is registered and signed in, because every portfolio route is behind
authentication (US-13). Tests that need to exercise the unauthenticated case use
``anon_client``.

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
def anon_client(provider: FakeProvider) -> Iterator[TestClient]:
    """A client with no session, for testing that routes actually require sign-in."""
    yield from _build_client(provider, sign_in=False)


@pytest.fixture()
def client(provider: FakeProvider) -> Iterator[TestClient]:
    """A registered, signed-in client."""
    yield from _build_client(provider, sign_in=True)


def _build_client(provider: FakeProvider, *, sign_in: bool) -> Iterator[TestClient]:
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
        # Every portfolio route requires a signed-in user (US-13), so the shared client is
        # registered and authenticated. The cookie persists on the TestClient.
        if sign_in:
            registered = test_client.post(
                "/auth/register",
                json={"email": "owner@example.com", "password": "correct-horse-battery"},
            )
            assert registered.status_code == 201, registered.text
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()
