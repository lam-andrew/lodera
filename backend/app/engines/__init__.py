"""Analytical engines — decoupled components behind the API contract.

Each engine (the Risk & Exposure core; later the RAG secondary layer) is an isolated
component with no knowledge of the frontend or of sibling engines. Callers reach an engine
**only** through the API layer in :mod:`app.api`, never by importing another engine's
internals. This boundary is user story US-15 and
docs/adr/0004-decoupled-engines-api-contract.md; new engines plug in behind the same
contract without modifying existing ones.

The subpackages (``risk``, ``rag``) are created as their user stories begin.
"""
