"""Authentication routes (US-13, FR-15; see ADR 0014).

Sessions are server-side: the browser holds an opaque token in an HTTP-only cookie, and the
server stores only its hash. That combination means a cross-site scripting bug cannot read
the session, and logging out genuinely invalidates it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.schemas import LoginRequest, RegisterRequest, UserRead
from app.core.config import settings
from app.core.database import get_session
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.models import Portfolio, User, UserSession

router = APIRouter(prefix="/auth", tags=["auth"])

SessionDep = Annotated[Session, Depends(get_session)]

#: Name of the session cookie.
COOKIE_NAME = "orbit_session"

#: How long a login lasts before the user must sign in again.
SESSION_LIFETIME = timedelta(days=14)

DEFAULT_PORTFOLIO_NAME = "Personal portfolio"


def _set_session_cookie(response: Response, token: str) -> None:
    """Attach the session cookie.

    ``httponly`` keeps it out of reach of JavaScript; ``samesite=lax`` blocks it from being
    sent on cross-site form posts; ``secure`` is on everywhere except local development,
    where there is no HTTPS to carry it.
    """
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=settings.environment != "development",
        path="/",
    )


def _issue_session(session: Session, user: User, response: Response) -> None:
    token = generate_session_token()
    session.add(
        UserSession(
            token_hash=hash_session_token(token),
            user_id=user.id,
            expires_at=datetime.now(UTC) + SESSION_LIFETIME,
        )
    )
    session.commit()
    _set_session_cookie(response, token)


def get_current_user(
    session: SessionDep,
    orbit_session: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> User:
    """Resolve the signed-in user, or reject the request with 401.

    Expired sessions are deleted as they are encountered, so the table does not accumulate
    dead rows and an expired token can never be reused.
    """
    if orbit_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not signed in.")

    record = session.scalar(
        select(UserSession).where(UserSession.token_hash == hash_session_token(orbit_session))
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session is no longer valid."
        )

    expires = record.expires_at
    if expires.tzinfo is None:  # SQLite returns naive datetimes; PostgreSQL does not.
        expires = expires.replace(tzinfo=UTC)
    if expires <= datetime.now(UTC):
        session.delete(record)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session has expired."
        )

    user = session.get(User, record.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session is no longer valid."
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: SessionDep, response: Response) -> User:
    """Create an account and sign in.

    Each account gets its own portfolio immediately, so the rest of the application always
    has one to scope to.
    """
    email = payload.email.strip().lower()
    if session.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        )

    user = User(email=email, password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)

    session.add(Portfolio(user_id=user.id, name=DEFAULT_PORTFOLIO_NAME))
    session.commit()

    _issue_session(session, user, response)
    return user


@router.post("/login", response_model=UserRead)
def login(payload: LoginRequest, session: SessionDep, response: Response) -> User:
    """Sign in with an email and password.

    A wrong email and a wrong password produce the identical response, so the endpoint
    cannot be used to discover which addresses have accounts.
    """
    email = payload.email.strip().lower()
    user = session.scalar(select(User).where(User.email == email))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    _issue_session(session, user, response)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    session: SessionDep,
    response: Response,
    orbit_session: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
) -> None:
    """Sign out, deleting the session server-side as well as clearing the cookie."""
    if orbit_session is not None:
        session.execute(
            delete(UserSession).where(UserSession.token_hash == hash_session_token(orbit_session))
        )
        session.commit()
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> User:
    """The signed-in user. Used by the frontend to decide what to render."""
    return user
