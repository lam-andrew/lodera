"""Password hashing and session tokens (ADR 0014).

Cryptography is delegated to reviewed primitives — ``argon2-cffi`` for hashing and
``secrets`` for token generation. Nothing here invents a scheme.
"""

from __future__ import annotations

import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

#: OWASP's current recommendation for interactive logins: Argon2id, ~64 MiB, 3 iterations.
#: Memory-hardness is the property that resists GPU-accelerated cracking.
_hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=1)

#: Bytes of entropy in a session token. 32 bytes = 256 bits, far beyond guessing range.
_TOKEN_BYTES = 32


def hash_password(password: str) -> str:
    """Hash a password. The salt and cost parameters live inside the returned string."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a password against a stored hash.

    Returns ``False`` rather than raising for any failure, so callers cannot accidentally
    distinguish "wrong password" from "corrupt hash" in a way that leaks information.
    """
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """Whether a stored hash was made with weaker parameters than we now use."""
    try:
        return _hasher.check_needs_rehash(password_hash)
    except (InvalidHashError, ValueError):
        return False


def generate_session_token() -> str:
    """A fresh, unguessable session token to hand to the browser."""
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    """The value stored server-side for a session token.

    A plain SHA-256 is right here and a password KDF would be wrong: the token already has
    256 bits of entropy, so there is nothing to brute-force, and this runs on every
    authenticated request.
    """
    return hashlib.sha256(token.encode()).hexdigest()
