# 0004. Decoupled engines behind an API contract (layered, component-based)

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Orbit's central value is a quantitative **Risk & Exposure engine** (the core), with a
secondary **RAG engine** over SEC filings added later, and possible future engines (regime
detection, anomaly detection) in the backlog. The graded algorithmic core must be buildable,
testable, and demoable independently of the frontend and of the other engines. If the frontend
or one engine reached into another engine's internals, the core could not evolve without
breaking callers, and the secondary/stretch work would risk destabilizing the graded core.

We needed an architectural rule that keeps the engines independent and lets new engines be
added without modifying the core.

## Decision

We will use a **layered, component-based architecture in which every engine is decoupled behind
the backend's API contract.** The frontend and any engine communicate with another engine
**only** through defined API routes exposed by the FastAPI layer — never by importing or calling
another engine's internal code.

- The FastAPI backend is the single entry point and orchestrator: authentication, routing,
  input validation, and engine invocation live there.
- Each engine (risk, later RAG) is an isolated component with no knowledge of the frontend or of
  sibling engines.
- New engines plug in behind the same API contract without changing existing engines.

This decision is the concrete implementation of user story **US-15** (decoupled engine behind an
API) and is enforced from the skeleton onward (US-14).

## Consequences

- **Positive:** The core risk engine can be developed, unit-tested, and demoed on its own; the
  secondary RAG engine and any stretch engines attach without touching it.
- **Positive:** A stable API contract lets the frontend and backend evolve independently; the
  contract is documented automatically via FastAPI's generated OpenAPI/Swagger.
- **Positive:** Clear component boundaries improve testability (engines can be tested through the
  API) and maintainability, both graded quality attributes.
- **Cost:** Going through the API adds a small amount of ceremony versus calling functions
  directly; some data crosses a serialization boundary. This is an accepted trade for the
  decoupling.
- **Cost:** The contract must be governed — changes to API routes are architecturally
  significant and warrant an ADR and a README/architecture-doc update.

## Alternatives Considered

- **A single monolithic module where the frontend or engines call each other's code directly:**
  simplest short-term, but couples the graded core to everything else and violates the core's
  requirement to be independently testable/demoable.
- **Full microservices (each engine its own deployable service):** maximal decoupling, but
  operationally heavy for a solo developer and premature at this scale; the API-contract
  boundary within one backend achieves the needed decoupling without the ops cost. If an engine
  ever needed independent scaling/deployment, a future ADR could promote it to its own service.
