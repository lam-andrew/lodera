"""User accounts and login sessions (US-13, ADR 0014)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """An account.

    Identified by email, stored lower-cased and unique. There is deliberately no ``salt``
    column: Argon2id encodes the salt and cost parameters inside the hash string itself, and
    a separate salt column is the signature of a hand-rolled scheme.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserSession(Base):
    """A live login session.

    Only the SHA-256 hash of the session token is stored, so disclosure of this table does
    not hand an attacker usable sessions. Rows are deleted on logout and on expiry, which is
    what makes revocation real rather than advisory.
    """

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
