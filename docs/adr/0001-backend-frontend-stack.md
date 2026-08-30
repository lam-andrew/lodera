# 0001. Python + FastAPI backend, React + TypeScript frontend

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Orbit is a portfolio risk intelligence web application built as a Penn State MSE capstone
(SWENG 894) by a solo developer on a fixed 14-week timeline. The product has two analytical
workloads: a quantitative **Risk & Exposure engine** (the graded algorithmic core —
volatility, correlation, concentration, drawdown, stress testing) and a secondary
**RAG layer** over SEC filings. Both are numerically and ML-heavy. The application must be a
real, deployable, tested web app with a clear separation between presentation and business
logic, not a research notebook.

We needed a backend language/framework suited to numerical and ML work with first-class
API tooling, and a frontend stack suited to an interactive risk dashboard and Q&A UI.

## Decision

We will build the **backend in Python 3.12 with FastAPI**, and the **frontend in React with
TypeScript**.

- Python gives direct access to the scientific/ML ecosystem the core needs (pandas, NumPy,
  scikit-learn) and the RAG tooling (LLM/embedding clients, filing parsers).
- FastAPI provides async performance, Pydantic request/response validation, and
  auto-generated OpenAPI/Swagger documentation, which lets us rely on generated API docs
  instead of hand-maintaining endpoint documentation.
- React + TypeScript gives a component model for the dashboard/visualizations and static
  typing to reduce defects in a solo project. The frontend is presentation-only and talks to
  the backend exclusively over REST/JSON.

## Consequences

- **Positive:** One language (Python) spans both engines and the API, reducing context
  switching. FastAPI's generated OpenAPI docs satisfy the API-documentation requirement
  automatically. TypeScript catches interface drift between components at compile time.
- **Positive:** Large, well-documented ecosystems shorten the learning/searching curve for a
  solo developer under time pressure.
- **Cost:** Two languages/toolchains (Python + Node) must both be containerized, tested, and
  wired into CI. A shared API contract (see [0004](0004-decoupled-engines-api-contract.md))
  must be kept in sync between backend Pydantic models and frontend TypeScript types.

## Alternatives Considered

- **Node/TypeScript full-stack (e.g. NestJS + React):** one language end-to-end, but Python's
  numerical/ML ecosystem is materially stronger for the risk math and RAG, which are the
  point of the product.
- **Django + templates:** batteries-included, but heavier than needed and pushes toward
  server-rendered pages rather than the decoupled SPA + REST API the architecture requires.
- **Flask backend:** lighter than Django but lacks FastAPI's built-in async, Pydantic
  validation, and automatic OpenAPI generation.
