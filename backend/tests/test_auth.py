"""Tests for US-13: authentication (FR-15, ADR 0014).

Beyond the happy path these check the properties that make auth actually protective:
routes reject anonymous callers, one account cannot see or touch another's data, and the
login endpoint does not reveal which email addresses have accounts.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.auth import COOKIE_NAME
from app.core.security import hash_password, hash_session_token, verify_password

GOOD_PASSWORD = "correct-horse-battery"


# --- password hashing -------------------------------------------------------------


def test_passwords_are_hashed_not_stored() -> None:
    stored = hash_password(GOOD_PASSWORD)
    assert GOOD_PASSWORD not in stored
    assert stored.startswith("$argon2id$")


def test_the_same_password_hashes_differently_each_time() -> None:
    """A per-password salt means identical passwords must not share a hash."""
    assert hash_password(GOOD_PASSWORD) != hash_password(GOOD_PASSWORD)


def test_verification_accepts_the_right_password_and_rejects_others() -> None:
    stored = hash_password(GOOD_PASSWORD)
    assert verify_password(GOOD_PASSWORD, stored) is True
    assert verify_password("wrong", stored) is False


def test_verification_returns_false_for_a_corrupt_hash() -> None:
    """A malformed hash must not raise — that would leak how the failure differed."""
    assert verify_password(GOOD_PASSWORD, "not-a-hash") is False


def test_session_tokens_are_unique_and_stored_only_as_hashes() -> None:
    from app.core.security import generate_session_token

    a, b = generate_session_token(), generate_session_token()
    assert a != b
    assert len(hash_session_token(a)) == 64  # sha256 hex
    assert hash_session_token(a) != a


# --- registration and login --------------------------------------------------------


def test_register_creates_an_account_and_signs_in(anon_client: TestClient) -> None:
    resp = anon_client.post(
        "/auth/register", json={"email": "New@Example.com", "password": GOOD_PASSWORD}
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"  # normalized
    assert "password" not in resp.text and "hash" not in resp.text
    assert COOKIE_NAME in resp.cookies

    assert anon_client.get("/auth/me").json()["email"] == "new@example.com"


def test_the_session_cookie_is_http_only(anon_client: TestClient) -> None:
    """HttpOnly is what stops an XSS bug from reading the session."""
    resp = anon_client.post(
        "/auth/register", json={"email": "flags@example.com", "password": GOOD_PASSWORD}
    )
    cookie_header = resp.headers["set-cookie"].lower()
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header


def test_duplicate_email_is_rejected(anon_client: TestClient) -> None:
    body = {"email": "dupe@example.com", "password": GOOD_PASSWORD}
    assert anon_client.post("/auth/register", json=body).status_code == 201
    assert anon_client.post("/auth/register", json=body).status_code == 409


def test_short_passwords_are_rejected(anon_client: TestClient) -> None:
    resp = anon_client.post(
        "/auth/register", json={"email": "short@example.com", "password": "abc"}
    )
    assert resp.status_code == 422


def test_invalid_email_is_rejected(anon_client: TestClient) -> None:
    resp = anon_client.post(
        "/auth/register", json={"email": "not-an-email", "password": GOOD_PASSWORD}
    )
    assert resp.status_code == 422


def test_login_succeeds_with_correct_credentials(anon_client: TestClient) -> None:
    anon_client.post(
        "/auth/register", json={"email": "user@example.com", "password": GOOD_PASSWORD}
    )
    anon_client.post("/auth/logout")

    resp = anon_client.post(
        "/auth/login", json={"email": "user@example.com", "password": GOOD_PASSWORD}
    )
    assert resp.status_code == 200
    assert anon_client.get("/auth/me").status_code == 200


def test_wrong_password_is_denied_with_a_clear_message(anon_client: TestClient) -> None:
    anon_client.post(
        "/auth/register", json={"email": "user@example.com", "password": GOOD_PASSWORD}
    )
    anon_client.post("/auth/logout")

    resp = anon_client.post(
        "/auth/login", json={"email": "user@example.com", "password": "wrong-password-here"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or password."


def test_login_does_not_reveal_whether_an_account_exists(anon_client: TestClient) -> None:
    """Unknown email and wrong password must be indistinguishable."""
    anon_client.post(
        "/auth/register", json={"email": "known@example.com", "password": GOOD_PASSWORD}
    )
    anon_client.post("/auth/logout")

    unknown = anon_client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": GOOD_PASSWORD}
    )
    wrong = anon_client.post(
        "/auth/login", json={"email": "known@example.com", "password": "definitely-wrong"}
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_email_is_case_insensitive_at_login(anon_client: TestClient) -> None:
    anon_client.post(
        "/auth/register", json={"email": "mixed@example.com", "password": GOOD_PASSWORD}
    )
    anon_client.post("/auth/logout")
    resp = anon_client.post(
        "/auth/login", json={"email": "MIXED@Example.COM", "password": GOOD_PASSWORD}
    )
    assert resp.status_code == 200


# --- sessions -----------------------------------------------------------------------


def test_logout_invalidates_the_session_server_side(client: TestClient) -> None:
    """Revocation must be real, not merely the client forgetting the token."""
    cookie = client.cookies.get(COOKIE_NAME)
    assert client.get("/auth/me").status_code == 200

    assert client.post("/auth/logout").status_code == 204

    # Even replaying the original cookie must fail — the row is gone.
    client.cookies.set(COOKIE_NAME, cookie or "")
    assert client.get("/auth/me").status_code == 401


def test_an_expired_session_is_rejected_and_cleaned_up(client: TestClient) -> None:
    from sqlalchemy import select

    from app.core.database import get_session
    from app.main import app
    from app.models import UserSession

    db = next(app.dependency_overrides[get_session]())
    record = db.scalar(select(UserSession))
    assert record is not None
    record.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()

    assert client.get("/auth/me").status_code == 401
    assert db.scalar(select(UserSession)) is None  # deleted on encounter


def test_a_forged_token_is_rejected(client: TestClient) -> None:
    client.cookies.set(COOKIE_NAME, "not-a-real-session-token")
    assert client.get("/auth/me").status_code == 401


# --- authorization ------------------------------------------------------------------


def test_portfolio_routes_require_a_session(anon_client: TestClient) -> None:
    for method, path in [
        ("get", "/holdings"),
        ("get", "/portfolio/summary"),
        ("get", "/portfolio/risk"),
        ("get", "/portfolio/correlation"),
        ("get", "/portfolio/concentration"),
        ("get", "/portfolio/drawdown"),
        ("get", "/portfolio/history"),
        ("get", "/market-data/AAPL/prices"),
        ("get", "/auth/me"),
    ]:
        assert getattr(anon_client, method)(path).status_code == 401, path

    assert (
        anon_client.post("/holdings", json={"ticker": "AAPL", "quantity": "1"}).status_code == 401
    )
    assert anon_client.patch("/holdings/1", json={"quantity": "1"}).status_code == 401
    assert anon_client.delete("/holdings/1").status_code == 401


def test_health_stays_public(anon_client: TestClient) -> None:
    """Liveness must not require a session, or orchestrators cannot check it."""
    assert anon_client.get("/health").status_code == 200


def test_one_account_cannot_see_anothers_holdings(anon_client: TestClient) -> None:
    anon_client.post("/auth/register", json={"email": "a@example.com", "password": GOOD_PASSWORD})
    anon_client.post("/holdings", json={"ticker": "AAPL", "quantity": "10"})
    a_holding_id = anon_client.get("/holdings").json()[0]["id"]
    anon_client.post("/auth/logout")

    anon_client.post("/auth/register", json={"email": "b@example.com", "password": GOOD_PASSWORD})
    assert anon_client.get("/holdings").json() == []
    assert anon_client.get("/portfolio/summary").json()["positions"] == []

    # And cannot reach it by id — that would be an IDOR.
    assert (
        anon_client.patch(f"/holdings/{a_holding_id}", json={"quantity": "99"}).status_code == 404
    )
    assert anon_client.delete(f"/holdings/{a_holding_id}").status_code == 404


def test_each_account_gets_its_own_portfolio(anon_client: TestClient) -> None:
    anon_client.post("/auth/register", json={"email": "one@example.com", "password": GOOD_PASSWORD})
    anon_client.post("/holdings", json={"ticker": "AAPL", "quantity": "5"})
    anon_client.post("/auth/logout")

    anon_client.post("/auth/register", json={"email": "two@example.com", "password": GOOD_PASSWORD})
    anon_client.post("/holdings", json={"ticker": "MSFT", "quantity": "3"})
    assert [h["ticker"] for h in anon_client.get("/holdings").json()] == ["MSFT"]

    anon_client.post("/auth/logout")
    anon_client.post("/auth/login", json={"email": "one@example.com", "password": GOOD_PASSWORD})
    assert [h["ticker"] for h in anon_client.get("/holdings").json()] == ["AAPL"]
