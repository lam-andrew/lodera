# CLAUDE.md — Lodera

Agent-facing context and working rules for this repository. Every Claude Code session
should read this file first. Human-facing project detail lives in `README.md`; this file
is the concise rulebook. If anything here conflicts with a user instruction in-session,
follow the user, but flag the conflict.

---

## Project in one paragraph

**Lodera** is a portfolio risk intelligence web app for individual investors. It combines a
quantitative **Risk & Exposure engine** (the core) with an evidence-grounded **RAG layer**
over SEC filings (secondary). It **measures, contextualizes, and explains** risk. It does
**NOT** predict prices, execute trades, or give investment advice. This is a Penn State MSE
capstone (SWENG 894): a real, deployable, tested application with CI/CD — not a notebook.
Software-engineering rigor is graded.

## Scope tiers — DO NOT BLUR

- **Core (committed):** portfolio ingestion + Risk & Exposure engine (volatility,
  correlation, concentration/exposure, drawdown, stress testing). The significant
  algorithmic component; primary focus.
- **Secondary (after core is stable):** RAG over SEC filings with grounded, cited answers.
- **Stretch (backlog; only if core finishes early):** regime detection, anomaly detection,
  automated brokerage connection. Do NOT build unless explicitly told to.

When in doubt: protect the core, defer everything else to the backlog.

## Stack (see `docs/adr/`)

Python 3.12 + FastAPI backend · React + TypeScript frontend · PostgreSQL 16 + pgvector
(relational + vectors in one service) · Docker + Docker Compose (provider-agnostic, no cloud
lock-in) · GitHub Actions CI/CD · pytest / Vitest / Postman for tests · hosted LLM API for
RAG, abstracted behind an interface.

## Architecture rule

Layered, component-based, containerized. **Engines are decoupled behind the API contract:**
the frontend and other engines call an engine ONLY through the API, never internal code. New
engines plug in behind the same API without modifying the core. See `README.md` §2.

---

## Documentation standards (industry-aligned; enforced by this file)

### 1. Architecture Decision Records (ADRs) — REQUIRED

- Location: `docs/adr/`, named `NNNN-short-title.md` (zero-padded, e.g. `0007-add-redis-cache.md`).
- Template: `docs/adr/0000-template.md`.
- Each ADR contains: **Title · Status** (Proposed / Accepted / Superseded by NNNN) **· Date ·
  Context · Decision · Consequences · Alternatives Considered**.
- **Write or update an ADR whenever a design, infrastructure, or architecture decision is
  made or changed.** Never change architecture silently. To reverse a past decision, add a
  new ADR that supersedes the old one (set the old one's status to "Superseded by NNNN") —
  do not edit history.
- When an ADR changes the stack, architecture, or scope, update `README.md` to match.

**When to WRITE an ADR:** architecturally significant choices — anything affecting structure,
data flow, external interfaces, cross-cutting concerns, security, deployment, or long-term
maintainability (e.g. choosing pgvector, adding auth, changing the API contract, adding a
new engine, changing how data is ingested).

**When to SKIP an ADR:** decisions that are tiny, low-risk, self-contained, easily reversible,
temporary (spikes/experiments), or already covered by an existing ADR or standard. Don't
document routine coding choices — that creates noise, not signal.

### 2. Architecture diagrams — C4 model via Mermaid

- Use the **C4 model** for architecture diagrams, kept as **Mermaid** in markdown so they
  render natively on GitHub and stay version-controlled as text.
- Maintain at least **Level 1 (System Context)** and **Level 2 (Container)** diagrams in
  `docs/architecture.md`. Add **Level 3 (Component)** only for a part that genuinely needs
  the detail (likely the Risk engine, given it's the graded algorithmic component).
- Keep diagrams in sync with reality; a stale diagram is worse than none.

### 3. Baseline repo hygiene

- `README.md` (project overview, setup, architecture) — keep current.
- `LICENSE` (MIT).
- `CONTRIBUTING.md` (setup, branch/PR flow, test expectations) — even solo, it documents the
  workflow and reads well for a capstone/portfolio.
- FastAPI auto-generates OpenAPI/Swagger docs for the API — rely on that rather than
  hand-maintaining endpoint docs.

---

## Conventions

- Feature branch → PR → CI must pass → merge to `main`.
- **Commit often and push regularly.** Prefer small, focused commits over large batched
  ones, and push the working branch to the GitHub remote (`origin`) frequently — after each
  logical unit of work, not just at the end of a session — so progress is backed up, visible
  on GitHub, and exercised by CI early. Don't accumulate many local commits without pushing.
- Each user story is a GitHub issue (US-1…US-18), labeled by tier + sprint, tracked on the
  project board.
- Never commit secrets; external services configured via environment variables (`.env`,
  git-ignored; provide `.env.example`).
- New backend logic ships with pytest coverage; API endpoints validated in CI.
- Keep engines decoupled behind the API contract (see Architecture rule).
- Cache external data (market data, filings) locally to respect free-tier rate limits.

## Current status

Sprint 1 (Weeks 3–5). Goal: a running, deployable app that ingests a portfolio and shows a
real risk metric (volatility) on live market data — a thin end-to-end slice. Sprint 1
stories: US-14, US-15 (architectural, do first), then US-1, US-3, US-4, US-5. Full stories
with acceptance criteria are in GitHub Issues and the project board.
