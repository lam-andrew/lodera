# Orbit — Portfolio Risk Intelligence

> A portfolio risk intelligence platform that helps individual investors understand what they actually hold and what could hurt them. It combines a quantitative **Risk & Exposure engine** (the core) with an evidence-grounded **document-intelligence / RAG layer** (secondary) that explains risk using primary financial filings.

**Status:** Active development · Academic capstone (Penn State MSE, SWENG 894) · Solo project
**Product name:** Orbit · **Working scope:** MVP over 14 weeks (4 sprints)

---

## 1. Context for AI agents / new contributors

This section exists so a fresh session (human or AI) has **zero context loss**. Read it fully before making changes.

- **What this is:** A capstone software product, not a research notebook. It is a real, deployable application with proper architecture, tests, and CI/CD — not just a model in a Jupyter notebook. Software-engineering rigor is mandatory.
- **What it is NOT:** It does **not** predict prices, execute trades, or give personalized investment advice. It **measures, contextualizes, and explains risk**. Any framing like "beat the market" is out of scope and off-thesis. The value is in analysis, risk, and grounded explanation.
- **Who it's for:** The self-directed individual investor holding stocks and ETFs who wants clearer, evidence-based risk insight than mainstream retail tools provide.
- **Core differentiator:** Fusing quantitative risk metrics with *evidence-grounded* explanations — every explanation cites the specific filing passage it came from. Competitors (e.g. Barebone AI, Magnifi) do one side or the other, shallowly; the integration is the edge.
- **Data:** All data is free/public and used for research/academic purposes only (no redistribution rights assumed). Sources: a free market-data API (prices), SEC EDGAR (filings), a hosted LLM API (RAG). Data is cached locally to respect free-tier rate limits.
- **Constraint that shapes everything:** Solo developer, fixed 14-week timeline. Scope is deliberately staged (core → secondary → stretch). When in doubt, protect the core; defer the rest to the backlog.

### Scope tiers (do not blur these)

| Tier | What | Build priority |
|---|---|---|
| **Core (committed)** | Portfolio ingestion + Risk & Exposure engine (volatility, correlation, concentration/exposure, drawdown, stress testing) | The significant algorithmic component; primary focus |
| **Secondary (in scope, after core is stable)** | Document intelligence / RAG over SEC filings with grounded, cited explanations | Built once the core is stable |
| **Stretch (backlog, only if core finishes early)** | Regime detection, anomaly detection, automated brokerage connection (Plaid/SnapTrade) | Not committed; un-pointed until core lands |

Per instructor guidance: the **Risk & Exposure engine is the core**; RAG is a **secondary** feature; the three stretch items are deferred.

---

## 2. Architecture

Layered, component-based, fully containerized. Everything inside the deployment boundary runs as Docker Compose services; external data sources and CI/CD sit outside it. The analytical engines are decoupled behind the API so the core can be built/tested/demoed independently and new engines plug in without modifying it.

```
                    ┌─────────────────────────────────────────────┐
                    │  Docker Compose (provider-agnostic)         │
                    │                                             │
  ┌──────────────┐  │   ┌──────────────────────────────────────┐  │
  │ Market data  │  │   │  React + TypeScript frontend         │  │
  │ API (prices) │  │   │  Portfolio entry, risk dashboard, Q&A│  │
  └──────┬───────┘  │   └───────────────────┬──────────────────┘  │
         │ (cached) │                       │ REST / JSON         │
         │          │   ┌───────────────────▼──────────────────┐  │
         │          │   │  FastAPI backend (API layer)         │  │
         │          │   │  Auth, routing, engine orchestration │  │
         │          │   └───────┬───────────────────┬──────────┘  │
         │          │           │                   │             │
         │          │   ┌───────▼────────┐  ┌───────▼──────────┐  │
         └──────────┼──▶│ Risk & Exposure│  │ RAG engine       │  │
                    │   │ engine (CORE)  │  │ (secondary)      │◀─┼── SEC EDGAR
                    │   └───────┬────────┘  └───────┬──────────┘  │   + hosted LLM API
                    │           │                   │             │
                    │   ┌───────▼────────┐  ┌───────▼──────────┐  │
                    │   │ PostgreSQL     │  │ pgvector         │  │
                    │   │ portfolios,    │  │ (in PostgreSQL)  │  │
                    │   │ holdings, cache│  │ filing embeddings│  │
                    │   └────────────────┘  └──────────────────┘  │
                    └─────────────────────────────────────────────┘
                    GitHub Actions CI/CD: build + test containers on
                    every push, then deploy the same images.
```

### Component responsibilities

- **React + TypeScript frontend** — presentation only (portfolio entry, risk dashboard + visualizations, natural-language Q&A). No business logic; talks to the backend over REST.
- **FastAPI backend (API layer)** — single entry point/orchestrator: authentication, routing, input validation, engine invocation. Exposes engines **only** through the API contract; the frontend never touches engine internals.
- **Risk & Exposure engine (core)** — the significant algorithmic component: volatility, correlation structure, concentration/exposure, drawdown, stress testing. Consumes cached market data. No knowledge of the frontend or RAG engine.
- **RAG engine (secondary)** — isolated document intelligence: retrieves SEC filings, embeds/indexes them, produces grounded, cited explanations. Kept separate so the core stays stable.
- **Data layer** — PostgreSQL + pgvector. Relational data (portfolios, holdings, cached prices) and vector embeddings live in one service to reduce moving parts.
- **External services** — free market-data API, SEC EDGAR, hosted LLM API. Reached only through the backend; credentials and rate-limited calls stay server-side.
- **Docker Compose + GitHub Actions** — Compose orchestrates internal services; Actions builds/tests container images on every push and deploys the same images.

### Quality attributes the architecture targets

- **Maintainability / Modifiability** — decoupled engines behind an API contract; new engines added without touching the core.
- **Portability** — full containerization, provider-agnostic; no cloud vendor lock-in.
- **Security** — auth gates portfolio access; all external calls/credentials are server-side.
- **Performance / Scalability** — market-data caching avoids redundant calls and respects free-tier limits; stateless API can scale horizontally.

---

## 3. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Backend / ML / RAG | **Python 3.12**, FastAPI | pandas, NumPy, scikit-learn for risk math; LLM/embedding client + filings parser for RAG |
| Frontend | **TypeScript**, React | Axios for HTTP; risk dashboard + Q&A UI |
| Database | **PostgreSQL 16 + pgvector** | Relational data + vector embeddings in one service |
| Containerization | **Docker + Docker Compose** | Provider-agnostic deployment; the deployment backbone |
| CI/CD | **GitHub Actions** | Build + test containers on every push |
| Testing | **pytest** (backend), **Vitest + React Testing Library** (frontend), **Postman** (API/integration) | Runs in CI |
| LLM (RAG) | **Hosted LLM API** | Abstracted behind an interface so the provider can be swapped |
| Deployment | Container host (provider-agnostic) | The containerized stack runs on any container-friendly host |

Guiding principles: provider-agnostic + container-based (no lock-in), open-source where practical, decoupled architecture, free/public data only.

---

## 4. Repository layout (planned)

> This is the intended structure; it will fill in as sprints progress. Keep the frontend/backend decoupled and the engines isolated behind the API.

```
orbit/
├── README.md
├── docker-compose.yml          # orchestrates backend, frontend, db
├── .github/workflows/          # GitHub Actions CI/CD
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── api/                # routes (the API contract)
│   │   ├── engines/
│   │   │   ├── risk/           # CORE: volatility, correlation, drawdown, stress
│   │   │   └── rag/            # SECONDARY: retrieval + grounded explanations
│   │   ├── data/               # market-data + EDGAR clients, caching
│   │   ├── models/             # DB models (portfolios, holdings, filings)
│   │   └── auth/               # authentication
│   └── tests/                  # pytest
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── components/         # dashboard, portfolio entry, Q&A
│       └── api/                # Axios client
└── docs/                       # architecture, requirements, living docs
```

---

## 5. Roadmap (4 sprints, ~14 weeks)

Sprints are 3 weeks each. Story IDs (US-#) map to issues in this repo and to the GitHub Project board. Story points use Fibonacci (relative size + uncertainty).

### Sprint 1 (Wks 3–5) — foundation + first risk metric · 20 pts
Goal: a running, deployable app that ingests a portfolio and shows a real risk metric on live market data (thin end-to-end slice).
- US-14 Containerized deployment skeleton (5)
- US-15 Decoupled engine behind API (3)
- US-1 Add holding manually (2)
- US-3 Manage holdings (2)
- US-4 Retrieve + cache market data (5)
- US-5 Volatility (holding + portfolio) (3)

### Sprint 2 (Wks 6–8) — full risk core + dashboard → **Product Demo I** · 18 pts
- US-2 Upload portfolio via CSV (3)
- US-13 Authenticate (3)
- US-7 Concentration/exposure (3)
- US-8 Historical drawdown (2)
- US-6 Correlation among holdings (5)
- US-10 Risk dashboard + visualizations (5)

### Sprint 3 (Wks 9–11) — algorithmic centerpiece + secondary feature · 21 pts
- US-9 Stress testing (8) — rounds out the risk engine (**Week 9 Significant Algorithmic Component** deliverable)
- US-11 Ingest SEC filings (5)
- US-12 Ask grounded question / RAG (8)

### Sprint 4 (Wks 12–14) — stretch or hardening → **Product Demo II** · TBD
- Stretch (only if on track): regime detection, anomaly detection, brokerage connection
- Otherwise: testing, deployment hardening, UX polish, final documentation (SRS, architecture doc, testing report, user manual)

---

## 6. Functional requirements (IEEE)

| ID | Requirement |
|---|---|
| FR-1 | The system shall allow the user to add a holding by entering a ticker symbol and share quantity. |
| FR-2 | The system shall allow the user to upload a portfolio via a CSV / brokerage-export file. |
| FR-3 | The system shall validate uploaded portfolio data and report rows it cannot parse. |
| FR-4 | The system shall persist a user's portfolio and allow the user to view, edit, and delete holdings. |
| FR-5 | The system shall retrieve historical price data for each holding from an external market-data source. |
| FR-6 | The system shall cache retrieved market data locally to limit redundant external calls. |
| FR-7 | The system shall compute the volatility of each holding and of the overall portfolio. |
| FR-8 | The system shall compute the correlation structure among the portfolio's holdings. |
| FR-9 | The system shall compute concentration/exposure metrics identifying overweight positions and overlapping exposure. |
| FR-10 | The system shall compute historical drawdown for the portfolio. |
| FR-11 | The system shall run scenario-based stress tests estimating portfolio impact under defined adverse market conditions. |
| FR-12 | The system shall present risk results to the user through a dashboard with supporting visualizations. |
| FR-13 | The system shall ingest SEC filings (10-K, 10-Q, 8-K) for a user's holdings and index them for retrieval. |
| FR-14 | The system shall answer a user's natural-language question about a holding with an explanation grounded in and citing the retrieved filing text. |
| FR-15 | The system shall allow a user to authenticate before accessing their portfolio. |

Full user stories with Given-When-Then acceptance criteria live in the GitHub Issues / Project board (US-1 … US-15).

---

## 7. Conventions

- **Branching:** feature branches → PR → CI must pass → merge to `main`.
- **Issues:** each user story is an issue, labeled by tier (`core`, `secondary`, `stretch`, `architectural`) and sprint; tracked on the GitHub Project board.
- **Engines stay decoupled:** the frontend and other engines call the risk engine **only** through the API contract, never internal code.
- **Data hygiene:** never commit API keys; external services are configured via environment variables. Cache external data locally.
- **Testing:** new backend logic ships with pytest coverage; API endpoints validated (Postman/integration) and run in CI.
- **Scope discipline:** protect the core; new feature ideas go to the backlog as stretch, not into the current sprint.

---

## 8. Academic context

Penn State World Campus — Master of Software Engineering — **SWENG 894 Capstone Experience**. Solo project (Group 5). Instructor: Dr. Raghu Sangwan. The build follows an agile-like process (SCRUM/Kanban/DevOps adapted for an academic setting) with weekly reports, two product demos (end of Sprint 2 and Sprint 4), and a final documentation suite (SRS, architecture & design, testing report, end-user manual).
