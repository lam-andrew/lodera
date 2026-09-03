# Software Requirements Specification — Orbit

**Project:** Orbit (repository: `portfolio-risk-intelligence`)
**Course:** SWENG 894 — Penn State MSE Capstone
**Author:** Andrew Lam (solo)
**Status:** Living document. Created Week 2; updated as requirements are refined.

> This is a **living document**, per the instructor's guidance to begin the four final
> deliverables early rather than assembling them in Week 14. It reflects the current
> understanding of the requirements. The Week 2 submission artifact — a snapshot of the
> *initial* plan — is [`week2-report.md`](week2-report.md) and is deliberately not
> retrofitted with later progress.

---

## 1. Introduction

### 1.1 Purpose

This document specifies the functional and non-functional requirements for **Orbit**, a
portfolio risk intelligence web application for individual investors. It is the reference
against which the system is designed, built, and tested.

### 1.2 Product scope

Orbit **measures, contextualizes, and explains** the risk in a self-directed investor's
portfolio. It combines:

- a quantitative **Risk & Exposure engine** (the core, and the graded algorithmic
  component): volatility, correlation structure, concentration/exposure, drawdown, and
  scenario stress testing; and
- an evidence-grounded **RAG layer** over public SEC filings that answers natural-language
  questions with citations back to the source text.

Orbit explicitly does **not** predict prices, execute trades, or give investment advice.
These exclusions are requirements, not omissions: they bound the problem and keep the
system on the right side of the line separating analysis from regulated financial advice.

### 1.3 Definitions

| Term | Meaning |
|---|---|
| **Holding** | One position: a ticker symbol and a share quantity. |
| **Portfolio** | The set of holdings belonging to one authenticated user. |
| **Volatility** | Annualized standard deviation of daily returns; the dispersion of outcomes. |
| **Correlation** | Pearson correlation between two holdings' daily return series. |
| **Concentration** | The degree to which portfolio value is clustered in few positions or in positions that move together. |
| **Drawdown** | Decline in portfolio value from its running peak. |
| **Stress test** | Estimated portfolio impact under a defined adverse market scenario. |
| **RAG** | Retrieval-Augmented Generation: answers generated only from retrieved source text, with citations. |
| **Grounded** | An answer traceable to specific retrieved filing text, not to model recall. |

### 1.4 References

- [`architecture.md`](architecture.md) — Software Architecture & Design Specification (C4).
- [`adr/`](adr/) — Architecture Decision Records; each significant decision and its rationale.
- [`testing.md`](testing.md) — Software Testing Report.
- [`user-guide.md`](user-guide.md) — End-user documentation.
- `README.md` — project overview, stack, and roadmap.
- GitHub Issues US-1 … US-18 — user stories with Given-When-Then acceptance criteria.

---

## 2. Overall description

### 2.1 Product perspective

Orbit is a new, self-contained system. It is not a component of a larger product and has no
predecessor to remain compatible with. It depends on three external systems, all free or
public, all reached **only** from the backend:

| External system | Used for | Requirement |
|---|---|---|
| Market-data API | Historical daily prices | FR-5, FR-6 |
| SEC EDGAR | Company filings (10-K, 10-Q, 8-K) | FR-13 |
| Hosted LLM API | Embeddings and grounded generation | FR-14 |

### 2.2 User characteristics

The intended user is a **self-directed individual investor** who holds stocks and ETFs
through a retail brokerage. Assumed to be financially literate but not a quantitative
analyst: comfortable with the idea of risk, not with reading a covariance matrix. This
drives a requirement that outputs be **explained**, not merely displayed (FR-12), and it is
why the in-app methodology documentation exists.

### 2.3 Constraints

- **CON-1** Free-tier external services only. Market-data providers impose request quotas,
  which the system must actively work within rather than assume away (drives FR-6).
- **CON-2** Solo developer, ~14 weeks, fixed academic deadlines. Scope discipline is a
  constraint, formalized as the tier system in [ADR 0005](adr/0005-scope-tiers.md).
- **CON-3** No cloud-vendor lock-in; the system must run on any container host
  ([ADR 0003](adr/0003-docker-compose-provider-agnostic.md)).
- **CON-4** Public data only. No brokerage credentials are ever accepted or stored.
- **CON-5** Software-engineering rigor is graded: tests, CI/CD, and documentation are
  requirements of the deliverable, not optional extras.

### 2.4 Assumptions and dependencies

- Market-data and EDGAR endpoints remain freely available for academic use.
- Users enter positions manually or via a brokerage CSV export; no live brokerage
  connection is in scope for this release (deferred to US-18, stretch tier).
- Daily (end-of-day) price granularity is sufficient. Intraday data is out of scope.

### 2.5 Scope tiers

Requirements are tiered, and the tiers must not be blurred. This is recorded in
[ADR 0005](adr/0005-scope-tiers.md).

| Tier | Contents | Commitment |
|---|---|---|
| **Core** | Portfolio ingestion + Risk & Exposure engine (FR-1 … FR-12, FR-15) | Committed |
| **Secondary** | RAG over SEC filings (FR-13, FR-14) | After the core is stable |
| **Stretch** | Regime detection, anomaly detection, brokerage connection (US-16 … US-18) | Backlog only; built only if the core finishes early |

---

## 3. Functional requirements

Each requirement is stated in IEEE "the system shall…" form, mapped to the user story that
delivers it, sized in Fibonacci story points, and prioritized with MoSCoW.

**MoSCoW rule used.** *Must* = the system is not a portfolio risk tool without it.
*Should* = materially increases value but the core proposition survives its absence in this
release. *Could* = stretch tier. *Won't (this release)* = deliberately excluded.

| ID | Requirement | Story | Pts | Priority |
|---|---|---|---|---|
| FR-1 | The system shall allow the user to add a holding by entering a ticker symbol and share quantity. | US-1 | 2 | Must |
| FR-2 | The system shall allow the user to upload a portfolio via a CSV / brokerage-export file. | US-2 | 3 | Should |
| FR-3 | The system shall validate uploaded portfolio data and report rows it cannot parse. | US-2 | — | Should |
| FR-4 | The system shall persist a user's portfolio and allow the user to view, edit, and delete holdings. | US-3 | 2 | Must |
| FR-5 | The system shall retrieve historical price data for each holding from an external market-data source. | US-4 | 5 | Must |
| FR-6 | The system shall cache retrieved market data locally to limit redundant external calls. | US-4 | — | Must |
| FR-7 | The system shall compute the volatility of each holding and of the overall portfolio. | US-5 | 3 | Must |
| FR-8 | The system shall compute the correlation structure among the portfolio's holdings. | US-6 | 5 | Must |
| FR-9 | The system shall compute concentration/exposure metrics identifying overweight positions and overlapping exposure. | US-7 | 3 | Must |
| FR-10 | The system shall compute historical drawdown for the portfolio. | US-8 | 2 | Must |
| FR-11 | The system shall run scenario-based stress tests estimating portfolio impact under defined adverse market conditions. | US-9 | 8 | Must |
| FR-12 | The system shall present risk results to the user through a dashboard with supporting visualizations. | US-10 | 5 | Must |
| FR-13 | The system shall ingest SEC filings (10-K, 10-Q, 8-K) for a user's holdings and index them for retrieval. | US-11 | 5 | Should |
| FR-14 | The system shall answer a user's natural-language question about a holding with an explanation grounded in and citing the retrieved filing text. | US-12 | 8 | Should |
| FR-15 | The system shall allow a user to authenticate before accessing their portfolio. | US-13 | 3 | Must |

FR-3 and FR-6 are delivered by the same story as FR-2 and FR-5 respectively, so their
points are counted once, against the parent story.

### 3.1 Architectural requirements

Two stories carry no FR because they deliver structural quality rather than user-visible
behavior. They are nonetheless requirements, and they are scheduled first.

| ID | Requirement | Story | Pts | Priority |
|---|---|---|---|---|
| AR-1 | The system shall run as containerized services orchestrated by Docker Compose, deployable to any container host without modification. | US-14 | 5 | Must |
| AR-2 | The analysis engines shall be reachable only through the backend's API contract, such that a new engine can be added without modifying the existing engines. | US-15 | 3 | Must |

### 3.2 Explicit exclusions

The following are **Won't (this release)** and are stated as requirements because excluding
them is a deliberate design position, not an oversight:

- **EX-1** The system shall not predict or forecast security prices.
- **EX-2** The system shall not execute, place, or recommend trades.
- **EX-3** The system shall not provide personalized investment advice.
- **EX-4** The system shall not accept, transmit, or store brokerage credentials.

---

## 4. Non-functional requirements

Four quality attributes drive the architecture. Each is stated with a target that can be
checked, because a quality attribute that cannot be verified is an aspiration, not a
requirement.

### NFR-1 — Maintainability / Modifiability

| | |
|---|---|
| **Requirement** | The system shall isolate analytical logic behind the API contract so a new engine can be added without modifying existing engines. |
| **Rationale** | The core must stay stable while the secondary RAG tier is built on top of it. |
| **Verification** | Risk engine modules import no database, HTTP, or provider code — they are pure functions over numeric inputs. CI enforces linting (Ruff), strict type checking (mypy), and tests on every push. |
| **Architecture link** | [ADR 0004](adr/0004-decoupled-engines-api-contract.md), AR-2 |

### NFR-2 — Portability

| | |
|---|---|
| **Requirement** | The system shall run on any Docker-capable host via a single `docker compose up`, with no cloud-provider-specific services. |
| **Rationale** | Avoiding lock-in keeps deployment options open and keeps the academic deliverable reproducible by a grader on their own machine. |
| **Verification** | The full stack builds and boots from the repository with no manual steps beyond supplying environment variables; CI runs the same container images that would be deployed. |
| **Architecture link** | [ADR 0003](adr/0003-docker-compose-provider-agnostic.md), AR-1 |

### NFR-3 — Security

| | |
|---|---|
| **Requirement** | The system shall require authentication before any portfolio data is read or written, shall store credentials only in irreversible hashed form, and shall keep all external API keys server-side. |
| **Rationale** | The system holds a user's financial positions. It also must never become a route by which brokerage credentials are exposed (EX-4). |
| **Verification** | Every portfolio route rejects unauthenticated requests; secrets are supplied via environment variables and never committed; automated secret scanning, dependency auditing, and static analysis run in CI. |
| **Architecture link** | [ADR 0014](adr/0014-authentication.md), [ADR 0007](adr/0007-quality-gates-and-security-scanning.md), FR-15 |

### NFR-4 — Performance / Scalability

| | |
|---|---|
| **Requirement** | The system shall serve repeated analysis of an unchanged portfolio from cached market data rather than re-fetching, and shall keep the network off the analysis path. |
| **Rationale** | Free-tier providers impose hard request quotas (CON-1). Caching is what makes the system usable at all, not merely faster. |
| **Verification** | A repeated request for the same ticker and window reports its data source as the cache rather than the provider; concurrent requests for the same symbol result in a single upstream fetch. |
| **Architecture link** | [ADR 0011](adr/0011-market-data-provider.md), FR-6 |

### NFR-5 — Usability (supporting)

| | |
|---|---|
| **Requirement** | The system shall explain what each risk metric means and how it was computed, not merely display its value. |
| **Rationale** | The target user (§2.2) is financially literate but not a quantitative analyst. An unexplained number is not insight. |
| **Verification** | Every displayed metric has accompanying interpretation, and the methodology is documented in-app. |
| **Architecture link** | FR-12 |

---

## 5. User stories

Full Given-When-Then acceptance criteria live in the GitHub Issues (US-1 … US-18) and are
the authoritative form. Sprint 1's six stories are reproduced in full in
[`week2-report.md`](week2-report.md) §3.

| Story | Title | Tier | Sprint | Pts |
|---|---|---|---|---|
| US-14 | Containerized, provider-agnostic deployment | Architectural | 1 | 5 |
| US-15 | Decoupled analysis engine behind an API | Architectural | 1 | 3 |
| US-1 | Add a holding manually | Core | 1 | 2 |
| US-3 | Manage holdings | Core | 1 | 2 |
| US-4 | Retrieve market data | Core | 1 | 5 |
| US-5 | See portfolio and holding volatility | Core | 1 | 3 |
| US-2 | Upload a portfolio via CSV | Core | 2 | 3 |
| US-13 | Authenticate | Core | 2 | 3 |
| US-7 | See concentration/exposure | Core | 2 | 3 |
| US-8 | See historical drawdown | Core | 2 | 2 |
| US-6 | See correlation among holdings | Core | 2 | 5 |
| US-10 | Risk dashboard | Core | 2 | 5 |
| US-9 | Run a stress test | Core | 3 | 8 |
| US-11 | Ingest filings for a holding | Secondary | 3 | 5 |
| US-12 | Ask a grounded question | Secondary | 3 | 8 |
| US-16 | Regime detection | Stretch | — | — |
| US-17 | Anomaly detection | Stretch | — | — |
| US-18 | Automated brokerage connection | Stretch | — | — |

---

## 6. Traceability matrix

Every requirement traces to a story, a sprint, and the tests that verify it.

| Requirement | Story | Sprint | Verified by |
|---|---|---|---|
| FR-1 | US-1 | 1 | Backend unit + API tests; frontend component tests |
| FR-2, FR-3 | US-2 | 2 | Parser unit tests with per-brokerage fixtures; API tests |
| FR-4 | US-3 | 1 | API CRUD tests; frontend interaction tests |
| FR-5, FR-6 | US-4 | 1 | Cache freshness/coverage tests; provider-fake integration tests |
| FR-7 | US-5 | 1 | Engine unit tests against hand-computed values |
| FR-8 | US-6 | 2 | Engine unit tests cross-checked against NumPy |
| FR-9 | US-7 | 2 | Engine unit tests against hand-computed HHI |
| FR-10 | US-8 | 2 | Engine unit tests over synthetic peak/trough series |
| FR-11 | US-9 | 3 | Engine unit tests over defined scenarios |
| FR-12 | US-10 | 2 | Frontend component + routing tests |
| FR-13 | US-11 | 3 | Ingestion/indexing integration tests |
| FR-14 | US-12 | 3 | Grounding tests: every claim traceable to retrieved text |
| FR-15 | US-13 | 2 | Auth tests: unauthenticated rejection, session lifecycle, ownership isolation |
| AR-1 | US-14 | 1 | CI integration job: full stack boots and services communicate |
| AR-2 | US-15 | 1 | Engine modules import no I/O; enforced by review and static analysis |
| NFR-1 … NFR-5 | — | ongoing | See [`testing.md`](testing.md) |

---

## 7. Change log

| Date | Change |
|---|---|
| 2026-09-02 | Initial SRS created as a living document (Week 2 deliverable guidance). |
