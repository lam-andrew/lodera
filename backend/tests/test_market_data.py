"""Tests for US-4: retrieve and cache market data (FR-5, FR-6)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.data.provider import MarketDataError, PriceBar, UnknownSymbolError
from app.data.service import MarketDataService
from app.models.prices import PriceBarRow, PriceCoverageRow
from tests.fakes import FakeProvider

# --- API level ---------------------------------------------------------------


def test_prices_are_retrieved_for_a_valid_ticker(
    client: TestClient, provider: FakeProvider
) -> None:
    resp = client.get("/market-data/AAPL/prices?days=30")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert body["source"] == "provider"  # first call goes to the provider
    assert body["count"] > 0
    assert len(body["bars"]) == body["count"]
    assert provider.price_calls == 1

    bar = body["bars"][0]
    assert {"date", "open", "high", "low", "close", "adj_close", "volume"} <= set(bar)


def test_second_request_is_served_from_cache(client: TestClient, provider: FakeProvider) -> None:
    """FR-6: analysis run again uses cached data instead of re-fetching."""
    first = client.get("/market-data/AAPL/prices?days=30").json()
    second = client.get("/market-data/AAPL/prices?days=30").json()

    assert first["source"] == "provider"
    assert second["source"] == "cache"
    assert provider.price_calls == 1  # provider was NOT called again
    assert second["count"] == first["count"]
    assert second["bars"] == first["bars"]


def test_unknown_ticker_is_rejected(client: TestClient) -> None:
    resp = client.get("/market-data/ZZZZ/prices?days=30")
    assert resp.status_code == 422
    assert "Unrecognized" in resp.json()["detail"]


def test_ticker_is_normalized(client: TestClient) -> None:
    assert client.get("/market-data/aapl/prices?days=10").json()["ticker"] == "AAPL"


def test_days_window_is_validated(client: TestClient) -> None:
    assert client.get("/market-data/AAPL/prices?days=0").status_code == 422
    assert client.get("/market-data/AAPL/prices?days=99999").status_code == 422


# --- Service level -----------------------------------------------------------


@pytest.fixture()
def session_factory():  # type: ignore[no-untyped-def]
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture()
def threaded_session_factory(tmp_path):  # type: ignore[no-untyped-def]
    """A session factory whose sessions get genuinely independent connections.

    The in-memory ``session_factory`` above uses ``StaticPool``, which shares a single SQLite
    connection across every session. That is fine (and fast) for single-threaded tests, but
    threads hitting one connection at once corrupt it — the failure surfaces as an unrelated
    ``IndexError: tuple index out of range`` from the driver, not as anything about our code.
    A file-backed database with the default pool gives each thread its own connection, which
    is what production does: every request checks one out of the pool.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'cache.db'}")
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


def _age_cache(session, *, hours: int) -> None:  # type: ignore[no-untyped-def]
    """Push the cache past its TTL by backdating both bars and coverage."""
    stale = datetime.now(UTC) - timedelta(hours=hours)
    for row in session.query(PriceBarRow).all():
        row.fetched_at = stale
    for row in session.query(PriceCoverageRow).all():
        row.fetched_at = stale
    session.commit()


def test_stale_cache_triggers_a_refetch(session_factory) -> None:  # type: ignore[no-untyped-def]
    session = session_factory()
    provider = FakeProvider()
    service = MarketDataService(session, provider, ttl_hours=24)

    end = date(2026, 8, 30)
    start = end - timedelta(days=10)
    assert service.get_daily_prices("AAPL", start, end).source == "provider"
    assert service.get_daily_prices("AAPL", start, end).source == "cache"

    # Age the cache past the TTL (freshness is tracked on the coverage row).
    _age_cache(session, hours=48)

    assert service.get_daily_prices("AAPL", start, end).source == "provider"
    assert provider.price_calls == 2


def test_stale_cache_is_served_when_the_provider_fails(session_factory) -> None:  # type: ignore[no-untyped-def]
    """Analysis degrades gracefully rather than breaking during a provider outage."""
    session = session_factory()
    provider = FakeProvider()
    service = MarketDataService(session, provider, ttl_hours=24)

    end = date(2026, 8, 30)
    start = end - timedelta(days=10)
    fresh = service.get_daily_prices("AAPL", start, end)
    assert fresh.source == "provider"

    _age_cache(session, hours=48)

    class BrokenProvider(FakeProvider):
        def get_daily_prices(self, ticker: str, start: date, end: date) -> list[PriceBar]:
            raise MarketDataError("provider down")

    degraded = MarketDataService(session, BrokenProvider(), ttl_hours=24)
    result = degraded.get_daily_prices("AAPL", start, end)
    assert result.source == "cache"
    assert len(result.bars) == len(fresh.bars)


def test_unknown_symbol_propagates_when_nothing_is_cached(session_factory) -> None:  # type: ignore[no-untyped-def]
    service = MarketDataService(session_factory(), FakeProvider(), ttl_hours=24)
    with pytest.raises(UnknownSymbolError):
        service.get_daily_prices("ZZZZ", date(2026, 8, 1), date(2026, 8, 30))


def test_cached_values_round_trip_exactly(session_factory) -> None:  # type: ignore[no-untyped-def]
    """Prices must survive the cache as exact Decimals (no float drift)."""
    session = session_factory()
    service = MarketDataService(session, FakeProvider(), ttl_hours=24)
    end = date(2026, 8, 30)
    start = end - timedelta(days=5)

    live = service.get_daily_prices("AAPL", start, end)
    cached = service.get_daily_prices("AAPL", start, end)

    assert cached.source == "cache"
    assert [b.adj_close for b in cached.bars] == [b.adj_close for b in live.bars]
    assert all(isinstance(b.adj_close, Decimal) for b in cached.bars)


# --- Portfolio summary (holdings + market data) -------------------------------


def test_summary_prices_positions_and_totals(client: TestClient) -> None:
    client.post("/holdings", json={"ticker": "AAPL", "quantity": "10"})
    client.post("/holdings", json={"ticker": "MSFT", "quantity": "5"})

    body = client.get("/portfolio/summary").json()
    assert body["priced"] is True
    assert [p["ticker"] for p in body["positions"]] == ["AAPL", "MSFT"]

    for position in body["positions"]:
        assert position["latest_price"] is not None
        assert position["market_value"] is not None
        # market_value == price * quantity
        assert Decimal(position["market_value"]) == (
            Decimal(position["latest_price"]) * Decimal(position["quantity"])
        ).quantize(Decimal("0.01"))

    # Total equals the sum of the positions, and weights sum to ~100%.
    assert Decimal(body["total_value"]) == sum(
        Decimal(p["market_value"]) for p in body["positions"]
    )
    assert abs(sum(Decimal(p["weight_pct"]) for p in body["positions"]) - 100) < Decimal("0.05")


def test_summary_is_empty_for_an_empty_portfolio(client: TestClient) -> None:
    body = client.get("/portfolio/summary").json()
    assert body["positions"] == []
    assert body["priced"] is False


def test_summary_still_lists_a_position_when_pricing_fails(
    client: TestClient, provider: FakeProvider
) -> None:
    """One unpriceable symbol must not hide the rest of the portfolio."""
    client.post("/holdings", json={"ticker": "AAPL", "quantity": "10"})
    client.post("/holdings", json={"ticker": "MSFT", "quantity": "5"})
    # MSFT stops being priceable after the holdings were created.
    provider.known = {"AAPL"}

    body = client.get("/portfolio/summary").json()
    by_ticker = {p["ticker"]: p for p in body["positions"]}
    assert by_ticker["AAPL"]["market_value"] is not None
    assert by_ticker["MSFT"]["market_value"] is None
    assert body["priced"] is True


def test_a_narrow_cached_window_does_not_answer_a_wider_request(session_factory) -> None:  # type: ignore[no-untyped-def]
    """Regression: a 10-day fetch must not silently answer a 365-day request.

    Without coverage tracking the wider call returned only the 10 cached days while
    reporting source="cache", which quietly starved anything computed from it (risk
    metrics saw ~5 observations instead of a year).
    """
    session = session_factory()
    provider = FakeProvider()
    service = MarketDataService(session, provider, ttl_hours=24)
    end = date(2026, 8, 30)

    narrow = service.get_daily_prices("AAPL", end - timedelta(days=10), end)
    assert narrow.source == "provider"

    wide = service.get_daily_prices("AAPL", end - timedelta(days=365), end)
    assert wide.source == "provider", "wider window must re-fetch, not reuse the narrow cache"
    assert len(wide.bars) > len(narrow.bars) * 5
    assert provider.price_calls == 2

    # Now the wide window is cached, and a narrower request inside it is a hit.
    inner = service.get_daily_prices("AAPL", end - timedelta(days=30), end)
    assert inner.source == "cache"
    assert provider.price_calls == 2


def test_concurrent_requests_fetch_a_ticker_only_once(threaded_session_factory) -> None:  # type: ignore[no-untyped-def]
    """Regression: five dashboard endpoints hitting a cold cache at once.

    Before the per-ticker lock they all missed together, all called the provider, and then
    collided inserting identical (ticker, date) rows — a unique-constraint violation that
    reached the user as HTTP 500 and blank risk figures. Now the first caller fetches and
    the rest find a warm cache.
    """
    import threading

    provider = FakeProvider()
    end = date(2026, 8, 30)
    start = end - timedelta(days=365)

    results: list[str] = []
    errors: list[BaseException] = []
    barrier = threading.Barrier(5)

    def worker() -> None:
        try:
            service = MarketDataService(threaded_session_factory(), provider, ttl_hours=24)
            barrier.wait()  # maximise the overlap
            results.append(service.get_daily_prices("AAPL", start, end).source)
        except BaseException as exc:  # noqa: BLE001 - surfaced via `errors` below
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len(results) == 5
    # Exactly one provider call, and the other four served from cache.
    assert provider.price_calls == 1
    assert results.count("provider") == 1
    assert results.count("cache") == 4


def test_storing_bars_twice_does_not_raise(session_factory) -> None:  # type: ignore[no-untyped-def]
    """Belt and braces: even if two processes race past the in-process lock, the write
    must degrade rather than 500. The database constraint stays the real guarantee."""
    session = session_factory()
    provider = FakeProvider()
    end = date(2026, 8, 30)
    start = end - timedelta(days=30)

    first = MarketDataService(session, provider, ttl_hours=24)
    bars = provider.get_daily_prices("AAPL", start, end)

    first._store("AAPL", start, end, bars)
    # A second store of the same window, as a lost race would attempt.
    first._store("AAPL", start, end, bars)

    assert len(first.get_daily_prices("AAPL", start, end).bars) == len(bars)
