"""API layer — the public contract of the backend.

Every route the frontend or any client may call is defined here. This package is the
**only** sanctioned boundary for reaching the analytical engines: callers invoke engines
through these routes, never by importing engine internals
(see docs/adr/0004-decoupled-engines-api-contract.md, user story US-15).
"""
