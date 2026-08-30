"""Orbit backend application package.

Layered, component-based backend. The FastAPI app in :mod:`app.main` is the single
entry point and orchestrator; analytical engines live under :mod:`app.engines` and are
reached only through the API layer (see docs/adr/0004-decoupled-engines-api-contract.md).
"""

__version__ = "0.1.0"
