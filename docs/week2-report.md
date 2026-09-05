# Week 2 Report — Software Requirements & Architecture

**Project:** Orbit — Portfolio Risk Intelligence
**Repository:** [`lam-andrew/portfolio-risk-intelligence`](https://github.com/lam-andrew/portfolio-risk-intelligence)
**Course:** SWENG 894 — Penn State MSE Capstone
**Student:** Andrew Lam (solo project)
**Date:** September 2, 2026

---

## Contents

1. [Project summary](#1-project-summary)
2. [Software requirements](#2-software-requirements)
3. [Product backlog](#3-product-backlog)
4. [Sprint 1 backlog](#4-sprint-1-backlog)
5. [Agile board](#5-agile-board)
6. [Software architecture](#6-software-architecture)
7. [Non-functional requirements](#7-non-functional-requirements-software-quality-attributes)
8. [Living documentation](#8-living-documentation)
9. [Appendix A — Risk register](#appendix-a--risk-register)

---

## 1. Project summary

**Orbit** is a portfolio risk intelligence web application for individual investors. It
combines a quantitative **Risk & Exposure engine** (the core, and the significant algorithmic
component of this capstone) with an evidence-grounded **retrieval layer** over public SEC
filings.

Orbit **measures, contextualizes, and explains** the risk already present in a portfolio. It
does **not** predict prices, execute trades, or give investment advice. These exclusions are
stated as requirements rather than left implicit, because they bound the problem and keep the
system clearly on the analysis side of the line separating measurement from regulated
financial advice.

The target user is a **self-directed individual investor** who holds stocks and ETFs through a
retail brokerage: financially literate, but not a quantitative analyst. This single fact drives
much of the design. It is why the system must *explain* each metric rather than merely display
it, and it is why the interface is a dashboard of interpreted results rather than a table of
numbers.

### Scope tiers

Scope is tiered explicitly, and the tiers are not blurred. This is a deliberate risk control
for a solo project on a fixed academic timeline.

| Tier | Contents | Commitment |
|---|---|---|
| **Core** | Portfolio ingestion and the Risk & Exposure engine | Committed. The graded algorithmic component. |
| **Secondary** | Retrieval-augmented Q&A over SEC filings | Begins only once the core is stable. |
| **Stretch** | Regime detection, anomaly detection, automated brokerage connection | Backlog only. Built only if the core finishes early. |

---

## 2. Software requirements

Requirements are expressed in the IEEE 29148 "the system shall…" form. Fifteen functional
requirements were elicited from the Week 1 concept of operations and product context.

### 2.1 Functional requirements

| ID | Requirement |
|---|---|
| **FR-1** | The system shall allow the user to add a holding by entering a ticker symbol and share quantity. |
| **FR-2** | The system shall allow the user to upload a portfolio via a CSV / brokerage-export file. |
| **FR-3** | The system shall validate uploaded portfolio data and report rows it cannot parse. |
| **FR-4** | The system shall persist a user's portfolio and allow the user to view, edit, and delete holdings. |
| **FR-5** | The system shall retrieve historical price data for each holding from an external market-data source. |
| **FR-6** | The system shall cache retrieved market data locally to limit redundant external calls. |
| **FR-7** | The system shall compute the volatility of each holding and of the overall portfolio. |
| **FR-8** | The system shall compute the correlation structure among the portfolio's holdings. |
| **FR-9** | The system shall compute concentration/exposure metrics identifying overweight positions and overlapping exposure. |
| **FR-10** | The system shall compute historical drawdown for the portfolio. |
| **FR-11** | The system shall run scenario-based stress tests estimating portfolio impact under defined adverse market conditions. |
| **FR-12** | The system shall present risk results to the user through a dashboard with supporting visualizations. |
| **FR-13** | The system shall ingest SEC filings (10-K, 10-Q, 8-K) for a user's holdings and index them for retrieval. |
| **FR-14** | The system shall answer a user's natural-language question about a holding with an explanation grounded in and citing the retrieved filing text. |
| **FR-15** | The system shall allow a user to authenticate before accessing their portfolio. |

### 2.2 Architectural requirements

The product backlog contains both functional and architectural requirements. Two requirements
deliver structural quality rather than user-visible behavior. They carry no FR number because
no user story of the "as an investor" form describes them, but they are requirements, they are
estimated, and they are scheduled first.

| ID | Requirement |
|---|---|
| **AR-1** | The system shall run as containerized services orchestrated by Docker Compose, deployable to any container host without modification. |
| **AR-2** | The analysis engines shall be reachable only through the backend's API contract, such that a new engine can be added without modifying existing engines. |

### 2.3 Explicit exclusions

Stated as requirements because excluding them is a deliberate design position, not an oversight.

| ID | Requirement |
|---|---|
| **EX-1** | The system shall not predict or forecast security prices. |
| **EX-2** | The system shall not execute, place, or recommend trades. |
| **EX-3** | The system shall not provide personalized investment advice. |
| **EX-4** | The system shall not accept, transmit, or store brokerage credentials. |

### 2.4 Requirements quality assessment (IEEE 29148)

Each requirement was assessed against the seven quality characteristics.

| Characteristic | Assessment |
|---|---|
| **Singular** | Each requirement states one capability. FR-2 and FR-3 were deliberately split: uploading a file and validating its contents are separate obligations, and a system could satisfy one while failing the other. Likewise FR-5 (retrieve) and FR-6 (cache). |
| **Feasible** | All fifteen are feasible with free-tier external services and the chosen stack. FR-11 and FR-14 carry the most delivery risk and are scheduled into Sprint 3 with the largest estimates. |
| **Unambiguous** | Each requirement was tested by asking "how would I verify this?" FR-9 was revised during this assessment: "identifies overweight positions and overlapping exposure" replaced an earlier, vaguer "measures diversification," which had no testable meaning. Quantitative thresholds are fixed in an Architecture Decision Record rather than left to interpretation. |
| **Complete** | The set covers the full path from portfolio ingestion through analysis to explanation, plus the authentication that gates it. Gaps identified during review, principally that the requirement set said nothing about deployment or engine isolation, were closed by adding AR-1 and AR-2. |
| **Consistent** | No requirement contradicts another. The exclusions (EX-1 … EX-4) were added specifically to make the boundaries consistent and explicit, since "explains risk" (FR-14) could otherwise be read as licensing advice. |
| **Verifiable** | Every requirement has a verification method recorded in the traceability matrix of the [SRS](SRS.md). Requirements that resisted verification were rewritten rather than accepted. |
| **Traceable** | Requirements are numbered and mapped to user stories, sprints, and tests. Each user story is a GitHub issue; commits and pull requests reference the story they implement, giving an unbroken chain from requirement to story to commit to test. |

---

## 3. Product backlog

The product backlog contains all requirements, functional and architectural, needed for a
minimum viable product. The fifteen functional requirements map to thirteen user stories; two
further stories carry the architectural requirements, and three stretch stories are held in the
backlog without estimates. Fifteen stories are estimated and prioritized.

### 3.1 Estimation and prioritization method

**Effort estimation — Fibonacci story points.** Points express relative size combined with
uncertainty, not hours. The scale is anchored on US-1 (add a holding) as 2 points: a small,
well-understood, full-stack change. A story is 8 points when it is both large and genuinely
uncertain in approach, which is why FR-11 (stress testing) and FR-14 (grounded Q&A) sit at the
top of the scale.

**Prioritization — MoSCoW, informed by four factors:**

1. **Breadth of desirability.** Does every user need it, or some?
2. **Criticality to the primary stakeholder.** For an academic capstone, the graded algorithmic
   core is the primary stakeholder interest, so the risk engine outranks convenience features.
3. **Cohesion with other stories.** A story that unblocks several others is raised in priority.
4. **Dependency and technical risk.** Foundational and high-uncertainty work is pulled earlier
   so that discovering a problem is survivable.

The rule applied: **Must** = the system is not a portfolio risk tool without it. **Should** =
materially increases value, but the core proposition survives its absence in this release.
**Could** = stretch tier. **Won't** = deliberately excluded (§2.3).

### 3.2 Backlog

| Story | Requirement | Description | Points | Priority | Risk note |
|---|---|---|---|---|---|
| **US-14** | AR-1 | Containerized, provider-agnostic deployment | 5 | Must | Setup cost is front-loaded and easy to underestimate; nothing else can be demonstrated until it works. |
| **US-15** | AR-2 | Decoupled analysis engine behind an API | 3 | Must | Discipline risk more than technical risk. The boundary must be established before code accretes across it, or retrofitting becomes expensive. |
| **US-1** | FR-1 | Add a holding manually | 2 | Must | Ticker validation depends on an external symbol source; behavior when that source is unavailable must be defined, not accidental. |
| **US-3** | FR-4 | View, edit, and delete holdings | 2 | Must | Low. Standard persistence work. |
| **US-4** | FR-5, FR-6 | Retrieve and cache market data | 5 | Must | **High.** Free-tier providers impose hard request quotas. A portfolio of *n* holdings costs *n* requests per uncached analysis, so caching is what makes the system viable, not merely faster. |
| **US-5** | FR-7 | Volatility per holding and for the portfolio | 3 | Must | Methodology choices (return type, annualization factor, sample vs population deviation) must be fixed once and shared, or metrics will silently disagree with each other. |
| **US-2** | FR-2, FR-3 | Upload a portfolio via CSV | 3 | Should | **Medium.** Brokerage export formats are undocumented and mutually inconsistent. Each brokerage is effectively a separate parsing problem; mitigated with a fixture per brokerage. |
| **US-13** | FR-15 | Authenticate before accessing a portfolio | 3 | Must | **Medium.** Security-sensitive and costly to get wrong. Mitigated by using well-understood primitives rather than inventing anything. |
| **US-7** | FR-9 | Concentration and exposure | 3 | Must | "Overlapping exposure" has no single standard definition; the threshold chosen must be defensible and documented, not arbitrary. |
| **US-8** | FR-10 | Historical drawdown | 2 | Must | Low. Well-defined computation over a value series. |
| **US-6** | FR-8 | Correlation among holdings | 5 | Must | **Medium.** Requires aligning return series across holdings with different trading histories. A holding that listed recently will silently corrupt results if alignment is handled carelessly. |
| **US-10** | FR-12 | Risk dashboard with visualizations | 5 | Must | **Medium.** Visualization effort is routinely underestimated, and this story is where the system either becomes comprehensible or does not. |
| **US-9** | FR-11 | Scenario-based stress testing | 8 | Must | **High.** The widest design space in the project (historical replay, factor shock, or simulation) and the Week 9 graded algorithmic deliverable. Principal risk is scope creep. |
| **US-11** | FR-13 | Ingest SEC filings for a holding | 5 | Should | **Medium.** EDGAR imposes rate limits, filing formats vary, and this is where the pgvector learning curve is paid. |
| **US-12** | FR-14 | Ask a grounded question | 8 | Should | **High.** The central risk is an answer that reads convincingly but is not actually supported by retrieved text. Requires explicit grounding tests, not just plausible output. |
| **US-16** | — | Regime detection | — | Could | Stretch. Not estimated; not scheduled. |
| **US-17** | — | Anomaly detection | — | Could | Stretch. Not estimated; not scheduled. |
| **US-18** | — | Automated brokerage connection | — | Could | Stretch. Constrained by EX-4: any implementation must use a consented aggregator, never brokerage credentials. |

**Total estimated: 61 points across 15 stories**, allocated to four three-week sprints.

### 3.3 Story sizing review

Stories were reviewed against common story smells. Two adjustments resulted:

- **Too large.** An initial single "compute risk metrics" story was split into US-5, US-6, US-7,
  and US-8. At its original size it would not have fit a sprint and would have hidden four
  distinct methodological decisions inside one estimate.
- **Too much detail too early.** Sprint 3 and 4 stories are deliberately left at story level
  without elaborated implementation detail. Specifying US-12 in depth now, before US-11 has
  taught us what the filings actually look like, would be planning ahead of knowledge.

---

## 4. Sprint 1 backlog

**Sprint 1 — Weeks 3 to 5 (three weeks) · 20 points**

### 4.1 Sprint goal

> A running, deployable application that ingests a portfolio and displays a real risk metric
> computed from live market data: a thin but complete end-to-end slice through every layer of
> the architecture.

The goal is fixed for the duration of the sprint.

### 4.2 Selection rationale

The six stories were chosen to satisfy two objectives simultaneously.

**Establish the foundation before anything is built on it.** US-14 and US-15 are architectural
and come first for dependency reasons. Nothing can be demonstrated until the stack runs
(US-14), and the engine boundary (US-15) is far cheaper to establish before application code
exists than to retrofit afterward. Together they de-risk the entire remaining project.

**Prove the architecture with a vertical slice.** The remaining four stories cut a thin path
through every layer: enter a holding (US-1), persist and manage it (US-3), fetch real market
data for it (US-4), and compute a genuine risk metric from that data (US-5). At the end of
Sprint 1 every layer has been exercised end to end with real data. A horizontal alternative,
such as building the complete data layer first, would have deferred integration risk to a later
sprint, which is precisely when it is most expensive to discover.

US-4 is also pulled forward deliberately because it carries the highest technical risk in the
core (external rate limits). Discovering a problem there in Week 4 is recoverable; discovering
it in Week 10 is not.

### 4.3 Prioritized sprint backlog

Listed in dependency order; each story is blocked by those above it.

| # | Story | Requirement | Points | Priority |
|---|---|---|---|---|
| 1 | US-14 — Containerized, provider-agnostic deployment | AR-1 | 5 | Must |
| 2 | US-15 — Decoupled analysis engine behind an API | AR-2 | 3 | Must |
| 3 | US-1 — Add a holding manually | FR-1 | 2 | Must |
| 4 | US-3 — Manage holdings | FR-4 | 2 | Must |
| 5 | US-4 — Retrieve market data | FR-5, FR-6 | 5 | Must |
| 6 | US-5 — See portfolio and holding volatility | FR-7 | 3 | Must |
| | | **Sprint total** | **20** | |

### 4.4 Story detail and acceptance criteria

---

#### US-14 — Containerized, provider-agnostic deployment
**Requirement:** AR-1 · **Points:** 5 · **Priority:** Must · **Tier:** Architectural

**Story**
As the developer, I want every service containerized with Docker Compose, so that the system
runs consistently and is not locked to one cloud provider.

**Acceptance criteria**
- **Given** the repository, **when** I run the Compose stack, **then** frontend, backend, and
  database start and communicate locally.
- **Given** a push to the main branch, **when** CI runs, **then** the same container images are
  built and tested before deployment.

---

#### US-15 — Decoupled analysis engine behind an API
**Requirement:** AR-2 · **Points:** 3 · **Priority:** Must · **Tier:** Architectural

**Story**
As the developer, I want the risk engine isolated behind a well-defined API, so that new
engines can be added without changing the core.

**Acceptance criteria**
- **Given** the backend, **when** the frontend requests analysis, **then** it calls the engine
  only through the API contract, not internal code.
- **Given** a new engine is added, **when** it is integrated, **then** it plugs in behind the
  same API layer without modifying the risk engine.

---

#### US-1 — Add a holding manually
**Requirement:** FR-1 · **Points:** 2 · **Priority:** Must · **Tier:** Core

**Story**
As an investor, I want to add a holding by entering a ticker and share quantity, so that I can
build my portfolio without a brokerage connection.

**Acceptance criteria**
- **Given** the portfolio page, **when** I enter a valid ticker and quantity and submit,
  **then** the holding is added and displayed.
- **Given** an unrecognized ticker, **when** I submit, **then** a clear error is shown and
  nothing is added.

---

#### US-3 — Manage holdings
**Requirement:** FR-4 · **Points:** 2 · **Priority:** Must · **Tier:** Core

**Story**
As an investor, I want to view, edit, and delete my holdings, so that I can keep my portfolio
accurate.

**Acceptance criteria**
- **Given** existing holdings, **when** I edit a quantity, **then** the change is saved and
  reflected in analysis.
- **Given** a holding, **when** I delete and confirm, **then** it is removed and excluded from
  further analysis.

---

#### US-4 — Retrieve market data
**Requirement:** FR-5, FR-6 · **Points:** 5 · **Priority:** Must · **Tier:** Core

**Story**
As an investor, I want the system to pull historical prices for my holdings, so that risk can
be calculated on real data.

**Acceptance criteria**
- **Given** a holding with a valid ticker, **when** analysis is requested, **then** the system
  retrieves its historical prices.
- **Given** price data was recently retrieved, **when** analysis runs again, **then** the system
  uses cached data instead of re-fetching.

---

#### US-5 — See portfolio and holding volatility
**Requirement:** FR-7 · **Points:** 3 · **Priority:** Must · **Tier:** Core

**Story**
As an investor, I want to see how volatile my holdings and overall portfolio are, so that I
understand how much they swing.

**Acceptance criteria**
- **Given** my portfolio has price data, **when** I open the risk dashboard, **then** I see
  volatility for each holding and for the portfolio.

---

### 4.5 Release plan

| Sprint | Weeks | Focus | Points |
|---|---|---|---|
| **Sprint 1** | 3–5 | Foundation and first risk metric (thin end-to-end slice) | 20 |
| **Sprint 2** | 6–8 | Full risk core and dashboard → **Product Demo I** | 18 |
| **Sprint 3** | 9–11 | Algorithmic centerpiece (stress testing) and secondary retrieval feature | 21 |
| **Sprint 4** | 12–14 | Stretch items or hardening → **Product Demo II** | TBD |

---

## 5. Agile board

Both the product backlog and the Sprint 1 backlog are maintained in **GitHub Projects**. Every
user story (US-1 … US-18) exists as a GitHub issue, labeled by tier (`core`, `secondary`,
`stretch`, `architectural`), by sprint, and by story-point estimate.

> **Product backlog:** `[PRODUCT BACKLOG LINK — paste GitHub Project URL]`
>
> **Sprint 1 backlog:** `[SPRINT 1 BACKLOG LINK — paste Sprint 1 view URL]`

Issues are the single source of truth for acceptance criteria. This report reproduces the
Sprint 1 criteria in §4.4 for convenience, but the issues remain authoritative and are updated
as stories are refined.

---

## 6. Software architecture

### 6.1 Architectural style

Orbit uses a **layered architecture combined with a component-based architecture**, fully
containerized.

**Layered** partitions the system's concerns into stacked groups: presentation (React
frontend), application (FastAPI API layer), domain (the analysis engines), and data
(PostgreSQL). Calls flow downward only. A layer never reaches around the one beneath it: the
frontend holds no business logic and never contacts the database directly, and the engines
never know the frontend exists.

**Component-based** decomposes the domain layer into independent functional components that
expose well-defined interfaces. Each analytical capability is composed by the API layer rather
than by its peers. This style was selected for the benefits it is known to provide, and which
this project specifically needs: **reusability, ease of development, ease of deployment, and
reduced technical complexity**. For a solo developer on a fixed timeline, reduced technical
complexity is not a nicety; it is what makes the schedule achievable.

The combination was chosen because the graded deliverable is a *maintainable, testable* system,
not merely a working one. Layering is what makes the algorithmic core unit-testable in
isolation. Component boundaries are what allow the secondary retrieval tier to be added later
without destabilizing that core.

### 6.2 Architecture narrative

The application is organized in four layers, each mapped to a container in the deployed system.
Source code for every layer, along with infrastructure definitions and documentation, is version
controlled in a single **Git** repository hosted on **GitHub**, using a feature-branch workflow:
work happens on a branch, is proposed as a pull request, must pass continuous integration, and
only then merges to `main`, which is always intended to be deployable. Users interact with a
**React + TypeScript** single-page application that holds presentation logic only and
communicates exclusively over **REST/JSON**. Requests terminate at a **Python 3.12 + FastAPI**
backend, which is the system's single entry point and orchestrator: it authenticates the
caller, validates input, performs all input and output, and invokes the analysis engines.

The engines themselves are the domain layer. The **Risk & Exposure engine** is the core and the
significant algorithmic component; the **retrieval engine** over SEC filings is secondary and
deliberately isolated from it. Both are reached only through the API contract, never by
importing internals, which is what allows a new engine to be introduced without modifying an
existing one. Data is persisted in **PostgreSQL 16 with the pgvector extension**, chosen so
that relational records and vector embeddings live in one service rather than two, reducing
operational surface for a solo project. Schema changes are applied as versioned **Alembic**
migrations checked into the repository. Security architecture consists of email and password
authentication with **Argon2id** password hashing and revocable server-side sessions delivered
in HttpOnly cookies; every portfolio route requires a valid session, and all external API
credentials remain server-side, never reaching the browser. The entire stack is packaged as
**Docker** images orchestrated by **Docker Compose**, deliberately avoiding managed
cloud-provider services so the system runs unchanged on any container host. **GitHub Actions**
builds and tests those same images on every push, running linting, strict type checking, unit
and integration tests, dependency auditing, static analysis, and secret scanning before any
change can merge.

### 6.3 Architecture views

The architecture is documented using the **C4 model**, maintained as plain-text diagrams in
[`docs/architecture.md`](architecture.md) so they are version-controlled as text and render
natively on GitHub. Three views are maintained: System Context, Container, and a Component view
of the Risk & Exposure engine.

#### View 1 — System Context

Orbit as a black box among its users and external systems.

```
                      ┌──────────────────────────────┐
                      │     Individual Investor      │
                      │          [Person]            │
                      │                              │
                      │   Self-directed investor     │
                      │   holding stocks and ETFs    │
                      └───────────────┬──────────────┘
                                      │
                    Enters portfolio, views dashboard,
                          asks questions   [HTTPS]
                                      ▼
    ┌───────────────────────────────────────────────────────────────┐
    │                            ORBIT                              │
    │                      [Software System]                        │
    │                                                               │
    │   Portfolio risk intelligence. Computes risk and exposure     │
    │   metrics and explains them with citations grounded in        │
    │   SEC filings.                                                │
    │                                                               │
    │   Does NOT predict prices, execute trades, or give advice.    │
    └──────┬──────────────────────┬─────────────────────┬───────────┘
           │                      │                     │
   Retrieves prices        Retrieves filings     Requests embeddings
   [HTTPS, cached]              [HTTPS]          and answers [HTTPS]
           ▼                      ▼                     ▼
 ┌──────────────────┐  ┌───────────────────┐  ┌──────────────────────┐
 │ Market-Data API  │  │     SEC EDGAR     │  │    Hosted LLM API    │
 │ [External System]│  │ [External System] │  │  [External System]   │
 │                  │  │                   │  │                      │
 │ Historical daily │  │ Public filings:   │  │ Embeddings and       │
 │ prices, cached   │  │ 10-K, 10-Q, 8-K   │  │ grounded generation  │
 │ locally (FR-6)   │  │                   │  │                      │
 └──────────────────┘  └───────────────────┘  └──────────────────────┘
```

All three external dependencies are free or public, and all are reached only from the backend.
No API credential is ever present in the browser.

#### View 2 — Container

The runnable units inside the deployment boundary. Everything inside the boundary is a Docker
Compose service; external systems and CI/CD sit outside it.

```
                      ┌──────────────────────────────┐
                      │     Individual Investor      │
                      │          [Person]            │
                      └───────────────┬──────────────┘
                                      │ Uses [HTTPS]
 ┌════════════════════════════════════╪════════════════════════════════┐
 ‖  ORBIT — Docker Compose deployment boundary                         ‖
 ‖                                    ▼                                ‖
 ‖  ┌───────────────────────────────────────────────────────────────┐  ‖
 ‖  │ Frontend                    [Container: React + TypeScript]   │  ‖
 ‖  │ Presentation only: portfolio entry, risk dashboard,           │  ‖
 ‖  │ visualizations, Q&A.  No business logic.                      │  ‖
 ‖  └──────────────────────────────┬────────────────────────────────┘  ‖
 ‖                                 │ REST / JSON [HTTPS]               ‖
 ‖                                 ▼                                   ‖
 ‖  ┌───────────────────────────────────────────────────────────────┐  ‖
 ‖  │ Backend / API layer         [Container: Python 3.12 + FastAPI]│  ‖
 ‖  │ Single entry point and orchestrator: authentication, routing, │  ‖
 ‖  │ input validation, engine invocation.                          │  ‖
 ‖  │ Performs ALL external I/O.  THE API CONTRACT.                 │  ‖
 ‖  └───┬──────────────────┬────────────────────────┬───────────────┘  ‖
 ‖      │ invokes behind   │ invokes behind         │ reads / writes   ‖
 ‖      │ the API contract │ the API contract       │ [SQL]            ‖
 ‖      ▼                  ▼                        │                  ‖
 ‖  ┌─────────────────┐  ┌──────────────────────┐   │                  ‖
 ‖  │ Risk & Exposure │  │ RAG engine           │   │                  ‖
 ‖  │ engine   [CORE] │  │ [SECONDARY]          │   │                  ‖
 ‖  │                 │  │                      │   │                  ‖
 ‖  │ Volatility,     │  │ Retrieves, embeds    │   │                  ‖
 ‖  │ correlation,    │  │ and indexes SEC      │   │                  ‖
 ‖  │ concentration,  │  │ filings. Produces    │   │                  ‖
 ‖  │ drawdown,       │  │ grounded, cited      │   │                  ‖
 ‖  │ stress testing. │  │ explanations.        │   │                  ‖
 ‖  │                 │  │                      │   │                  ‖
 ‖  │ PURE — no I/O   │  └──────────┬───────────┘   │                  ‖
 ‖  └─────────────────┘             │ embeddings    │                  ‖
 ‖                                  │ [SQL/pgvector]│                  ‖
 ‖                                  ▼               ▼                  ‖
 ‖          ┌───────────────────────────────────────────────┐          ‖
 ‖          │ PostgreSQL 16 + pgvector      [Container]     │          ‖
 ‖          │ Users, portfolios, holdings, cached price     │          ‖
 ‖          │ bars, coverage windows, filing embeddings     │          ‖
 ‖          └───────────────────────────────────────────────┘          ‖
 └══════════════════════════════════════════════════════════════════════┘
        │                        │                        │
  Backend fetches          RAG fetches              RAG requests
  prices, then caches      filings                  embeddings/answers
  [HTTPS]                  [HTTPS]                  [HTTPS]
        ▼                        ▼                        ▼
 ┌─────────────────┐  ┌────────────────────┐  ┌─────────────────────┐
 │ Market-Data API │  │     SEC EDGAR      │  │   Hosted LLM API    │
 │   [External]    │  │     [External]     │  │     [External]      │
 └─────────────────┘  └────────────────────┘  └─────────────────────┘

 CI/CD sits outside the boundary: GitHub Actions builds and tests these
 same container images on every push.
```

#### View 3 — Component: the Risk & Exposure engine

The core is decomposed into four independent metric components. The property this view exists to
communicate is the **purity boundary**: every metric component is a pure function over numeric
inputs, importing no database, HTTP, or provider code. All input and output happens in the API
layer above the boundary and is handed down. This is what makes the algorithmic core testable
against hand-computed expected values, and it is the concrete realization of AR-2.

```
                 ┌────────────────────────────────────┐
                 │ Frontend        [Container: React] │
                 │ Requests analysis over REST        │
                 └─────────────────┬──────────────────┘
                                   │ REST / JSON [HTTPS]
 ┌─────────────────────────────────┼────────────────────────────────┐
 │ BACKEND / API LAYER — performs ALL input and output              │
 │                                 ▼                                │
 │ ┌──────────────────────────────────────────────────────────────┐ │
 │ │ Risk and exposure routes             [Component: FastAPI]    │ │
 │ │ The public API contract: /portfolio/risk, /correlation,      │ │
 │ │ /concentration, /drawdown                                    │ │
 │ └──┬───────────────────────────────────────────────────────────┘ │
 │    │ requests aligned series and weights                         │
 │    ▼                                                             │
 │ ┌──────────────────────────────────────────────────────────────┐ │
 │ │ Portfolio series assembler           [Component: Python]     │ │
 │ │ Loads holdings, aligns price series to common trading        │ │
 │ │ dates, derives portfolio weights                             │ │
 │ └──┬───────────────────────────────────────────────────────────┘ │
 │    │ requests daily bars                                         │
 │    ▼                                                             │
 │ ┌──────────────────────────────────────────────────────────────┐ │
 │ │ Market-data service                  [Component: Python]     │ │
 │ │ Cache-aware price access. Serves from PostgreSQL when fresh, │ │
 │ │ else fetches and stores. Single-flight per symbol.           │ │
 │ └──┬──────────────────────────────┬────────────────────────────┘ │
 └────┼──────────────────────────────┼──────────────────────────────┘
      │ reads / writes               │ fetches ONLY on a
      │ cached bars [SQL]            │ cache miss [HTTPS]
      ▼                              ▼
 ┌──────────────────────────┐  ┌──────────────────────────────┐
 │ PostgreSQL   [Container] │  │ Market-Data API   [External] │
 │ Holdings, cached price   │  │ Historical daily prices;     │
 │ bars, coverage windows   │  │ hard hourly request quota    │
 └──────────────────────────┘  └──────────────────────────────┘

   The routes then call the engine below with PLAIN NUMBERS:
   returns and weights, aligned return series, portfolio value series.

┌──────────────────────────────────────────────────────────────────────────────┐
│ RISK AND EXPOSURE ENGINE — PURE FUNCTIONS, NO INPUT OR OUTPUT                │
│                                                                              │
│ ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│ │   Volatility  │  │  Correlation  │  │ Concentration │  │    Drawdown   │   │
│ │    [NumPy]    │  │    [NumPy]    │  │    [Python]   │  │    [Python]   │   │
│ ├───────────────┤  ├───────────────┤  ├───────────────┤  ├───────────────┤   │
│ │Daily returns, │  │Pearson        │  │Herfindahl     │  │Running-peak   │   │
│ │annualized     │  │correlation    │  │index,         │  │drawdown,      │   │
│ │standard       │  │matrix, most   │  │effective      │  │maximum and    │   │
│ │deviation,     │  │and least      │  │holdings,      │  │current,       │   │
│ │covariance     │  │correlated     │  │overweight,    │  │decline        │   │
│ │portfolio      │  │pairs          │  │overlap        │  │episodes       │   │
│ │volatility     │  │               │  │groups         │  │               │   │
│ └───────────────┘  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                                              │
│ No module here imports a database, an HTTP client, or a                      │
│ market-data provider. The routes hand these components plain                 │
│ numbers and get plain numbers back, which is what makes the                  │
│ algorithmic core testable against hand-computed values.                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 6.4 Component descriptions and allocation of responsibilities

Responsibilities are allocated so that each component has exactly one reason to change. The
"not responsible for" column is as important as the first: it is what keeps the boundaries
enforceable rather than aspirational.

| Component | Technology | Responsible for | Explicitly **not** responsible for |
|---|---|---|---|
| **Frontend** | React + TypeScript | Presentation: portfolio entry, risk dashboard, visualizations, Q&A interface. Client-side routing and form validation for usability. | Business logic; risk mathematics; direct database access; contacting any external API. |
| **Backend / API layer** | Python 3.12 + FastAPI | The single entry point. Authentication and authorization, request routing, input validation, orchestration of engines, and **all** input/output: database access and external API calls. Defines the public API contract. | Implementing risk mathematics; rendering. |
| **Risk & Exposure engine** (core) | Python, NumPy | The significant algorithmic component: volatility, correlation, concentration/exposure, drawdown, and stress testing, as pure functions over numeric inputs. | Knowing about HTTP, the database, the frontend, or the retrieval engine. It receives numbers and returns numbers. |
| **Retrieval (RAG) engine** (secondary) | Python | Filing retrieval, chunking, embedding, indexing, and producing grounded answers with citations to source text. | Touching the risk engine's internals or its data. |
| **Data layer** | PostgreSQL 16 + pgvector | Durable storage of users, portfolios, holdings, cached price bars, and filing embeddings. Enforcing integrity constraints. | Business rules. |
| **External services** | Market-data API, SEC EDGAR, hosted LLM API | Supplying prices, filings, and inference. | Being reached from the browser. All calls are server-side. |
| **CI/CD** | GitHub Actions, Docker Compose | Building and testing the container images that are deployed; running all quality gates on every change. | Being a deployment target itself. |

### 6.5 Design decisions and rationale

Every architecturally significant decision is recorded as an **Architecture Decision Record** in
[`docs/adr/`](adr/), capturing context, the decision, alternatives considered, and consequences
accepted. Decisions are never silently reversed: a superseding ADR is added and the original is
marked superseded, preserving the reasoning history. The decisions that most shape the
architecture:

| Decision | Rationale | Consequence accepted |
|---|---|---|
| **Python + FastAPI backend** | The quantitative and machine-learning ecosystem lives in Python, and the graded core is algorithmic. FastAPI provides typed request validation and generated OpenAPI documentation at no extra cost. | Not the fastest runtime available, which is irrelevant when the workload is bounded by external data retrieval. |
| **React + TypeScript frontend** | Static typing across the client/server boundary catches contract drift at compile time rather than in the browser. | A build step, and a larger toolchain than server-rendered templates. |
| **PostgreSQL 16 + pgvector, one service** | Relational data and vector embeddings in one engine means one service to run, back up, and reason about. A dedicated vector database would have added an operational component and a cross-store consistency problem for a solo developer. | pgvector is less specialized than a purpose-built vector store; acceptable at this corpus size. |
| **Engines behind the API contract** | The architectural spine. It is what allows the secondary retrieval tier to be added without destabilizing the graded core, and what keeps the core independently testable. | Some indirection and data marshalling at the boundary versus calling engine code directly. |
| **Docker Compose, provider-agnostic** | Portability and reproducibility. A grader can run the system without a cloud account, and no hosting decision is locked in prematurely. | Forgoes managed-service conveniences such as autoscaling and managed backups. |
| **Explicit scope tiers** | Scope discipline made a written commitment rather than an intention. It is the primary schedule risk control for a solo project. | Attractive stretch ideas are deferred even when they are tempting. |
| **Aggressive local caching of market data** | Free-tier providers impose hard request quotas. Caching is what makes the system viable at all, not merely faster. | Cached data may be up to one TTL stale, which is acceptable for end-of-day risk analysis. |
| **Fixed risk-math conventions** | Adjusted close prices, simple returns, sample standard deviation, and a 252-day year, fixed once and shared. Metrics computed from the same return series cannot silently disagree. | Rules out mixing methodologies later without an explicit, recorded decision. |

---

## 7. Non-functional requirements (software quality attributes)

Four quality attributes drive the architecture, with a fifth supporting attribute derived from
the user profile. Each is stated with a verification criterion, because a quality attribute
that cannot be checked is an aspiration rather than a requirement. Each is also mapped to the
specific components that carry responsibility for delivering it.

### NFR-1 — Maintainability / Modifiability

**Requirement.** The system shall isolate analytical logic behind the API contract so that a new
engine can be added without modifying existing engines.

**Why it matters here.** The core must remain stable while the secondary retrieval tier is built
on top of it, and the project is expected to evolve across four sprints. Modifiability is the
attribute that determines whether Sprint 3 is a straightforward addition or a rewrite.

**How the architecture delivers it.** Layering separates presentation, application, domain, and
data. Within the domain layer, each metric is an independent component. Engine modules are pure
functions that import no database, HTTP, or provider code, so they can be understood, tested,
and changed in isolation.

**Responsibility allocation.** The *API layer* owns the contract and all I/O. The *engines* own
mathematics only. Neither may take on the other's responsibility.

**Verification.** Engine modules contain no I/O imports, which is directly checkable. Linting,
strict type checking, and the full test suite run in CI on every change.

---

### NFR-2 — Portability

**Requirement.** The system shall run on any Docker-capable host via a single `docker compose up`,
with no dependency on cloud-provider-specific services.

**Why it matters here.** Two reasons, one academic and one practical. A grader must be able to
run the system without provisioning cloud infrastructure, and no hosting decision should be
locked in before it needs to be made.

**How the architecture delivers it.** Every runnable piece is a container. All environment-specific
values arrive as environment variables. Nothing depends on a managed service.

**Responsibility allocation.** *Docker Compose* owns service orchestration and networking.
*GitHub Actions* owns building and testing the identical images that would be deployed.

**Verification.** The stack builds and boots from a clean checkout with no manual steps beyond
supplying environment variables; CI exercises this on every push.

---

### NFR-3 — Security

**Requirement.** The system shall require authentication before any portfolio data is read or
written, shall store credentials only in irreversible hashed form, and shall keep all external
API keys server-side.

**Why it matters here.** The system holds a user's financial positions, which are sensitive even
though they are not directly monetizable. It must also never become a route by which brokerage
credentials are exposed, which is why EX-4 forbids accepting them at all.

**How the architecture delivers it.** Authentication is enforced at the API layer, the single
entry point, so no route can accidentally bypass it. Passwords are stored as Argon2id hashes.
Sessions are server-side and revocable, delivered in HttpOnly cookies that page JavaScript
cannot read. Resources resolve by owner as well as identifier, so one user cannot reach
another's data by guessing an identifier. All external credentials stay on the server.

**Responsibility allocation.** The *API layer* owns authentication, authorization, and secret
handling. The *frontend* holds no secrets and makes no trust decisions. *CI* owns automated
secret scanning, dependency auditing, and static analysis.

**Verification.** Every portfolio route rejects unauthenticated requests; ownership isolation is
tested directly; secret scanning, dependency audit, and static analysis run on every push.

---

### NFR-4 — Performance / Scalability

**Requirement.** The system shall serve repeated analysis of an unchanged portfolio from cached
market data rather than re-fetching, and shall keep the network off the analysis path.

**Why it matters here.** This is a hard external constraint, not a tuning goal. Free-tier
market-data providers impose strict request quotas, and a portfolio of *n* holdings costs *n*
requests per uncached analysis. Without caching the system does not merely feel slow; it stops
working.

**How the architecture delivers it.** Retrieved price data is persisted locally along with a
record of which date window has actually been fetched for each symbol, so a narrow earlier
fetch cannot silently satisfy a wider later request with insufficient data. Cache entries carry
a freshness lifetime. The API is stateless apart from the session store, so it can scale
horizontally.

**Responsibility allocation.** The *market-data service* in the API layer owns caching, freshness,
and coverage. The *engines* assume data is already present and perform no retrieval.

**Verification.** A repeated request for the same symbol and window reports its source as the
cache rather than the provider.

---

### NFR-5 — Usability (supporting)

**Requirement.** The system shall explain what each risk metric means and how it was computed,
not merely display its value.

**Why it matters here.** It follows directly from the user profile. The target user understands
investing but not quantitative finance. An unexplained number is not insight, and a number the
user misinterprets is worse than no number at all.

**How the architecture delivers it.** The frontend presents each metric with its interpretation
and links to in-application methodology documentation covering the formula, the reasoning behind
the method chosen, and its limitations.

**Responsibility allocation.** The *frontend* owns presentation and explanation. The *API layer*
supplies the supporting context, such as observation counts and thresholds, that makes an
honest explanation possible.

**Verification.** Every displayed metric is accompanied by interpretation and a route to its
methodology.

---

## 8. Living documentation

Following the guidance to begin the final documentation now rather than assembling it in
Week 14, the four final documents already exist in the repository and are maintained as living
documents, updated in the same pull request as the code they describe:

| Document | Location | Status |
|---|---|---|
| Software Requirements Specification | [`docs/SRS.md`](SRS.md) | Initial version complete |
| Software Architecture & Design Specification | [`docs/architecture.md`](architecture.md) | Initial version complete, with three C4 views |
| Software Testing Report | [`docs/testing.md`](testing.md) | Initial version: strategy, coverage, quality gates |
| End-User Documentation | [`docs/user-guide.md`](user-guide.md) | Initial version, grows as features land |

Supporting these, `docs/adr/` holds the Architecture Decision Records, and `README.md` carries
the project overview, stack, and roadmap. Because the architecture diagrams are plain text
rather than images, they are reviewed and versioned like source code, which is what keeps them
from drifting out of date.

This report is deliberately a **snapshot of the initial plan**. Progress against the plan
belongs in subsequent weekly reports, not retrofitted into this one.

---

## Appendix A — Risk register

Risks are carried at the project level; per-requirement risk notes are in §3.2.

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-1 | **Market-data free-tier rate limits.** A portfolio of *n* holdings costs *n* requests per uncached analysis; quotas are hourly and strict. | High | High | Aggressive local caching with explicit coverage tracking (FR-6); provider abstracted behind an interface so a different vendor is a configuration change; graceful degradation to stale cached data rather than failure. |
| R-2 | **Retrieval grounding uncertainty.** A generated answer may read convincingly while not actually being supported by the retrieved filing text. | Medium | High | Require citations to retrieved text for every claim; write explicit grounding tests rather than accepting plausible output; keep the retrieval tier secondary so the graded core does not depend on it. |
| R-3 | **pgvector learning curve.** Vector indexing and similarity search are new to the developer. | Medium | Medium | Scheduled in Sprint 3, well after the core is stable; a spike precedes committing to an indexing approach. |
| R-4 | **Scope creep into stretch features.** Regime detection and brokerage connection are attractive and out of scope. | Medium | High | Tiers recorded in an ADR; stretch items stay in the backlog unlabeled for any sprint; the core is protected by explicit written commitment. |
| R-5 | **Stress-testing design space (US-9).** Historical replay, factor shocks, and simulation are all defensible; choosing badly wastes the largest single estimate in the project. | Medium | High | Timeboxed design spike at the start of Sprint 3; the methodology decision is recorded as an ADR before implementation begins. |
| R-6 | **Solo-developer schedule risk.** No capacity to absorb an illness or a bad week. | Medium | High | Sprint 1 front-loads foundational and highest-risk work; scope tiers give a pre-agreed reduction path; Sprint 4 is deliberately left flexible for hardening rather than committed to features. |
| R-7 | **Brokerage export format variability.** Each brokerage exports a different, undocumented CSV shape. | High | Low | A test fixture per brokerage; per-row error reporting so one unparseable row never silently drops a position; manual entry always remains available as a fallback. |
