# Contributing to Lodera

Lodera is a solo Penn State MSE capstone (SWENG 894), but it is built to professional
standards — this guide documents the workflow so the process is reproducible and reads clearly
for review. Please read [`CLAUDE.md`](CLAUDE.md) (the working rulebook) and [`README.md`](README.md)
(project overview) before contributing.

## Prerequisites

- **Docker** + **Docker Compose** (the supported way to run the full stack)
- **Python 3.12** (backend, if running outside Docker)
- **Node.js 20+** and **npm** (frontend, if running outside Docker)
- **Git**

## Getting started

```bash
# 1. Clone
git clone <repo-url> lodera && cd lodera

# 2. Configure environment (never commit real secrets)
cp .env.example .env        # then fill in values

# 3. Bring the whole stack up
docker compose up --build
```

Once up:

- Backend API + docs: `http://localhost:8000` (Swagger UI at `/docs`)
- Health check: `http://localhost:8000/health`
- Frontend: `http://localhost:5173`

To run a service on its own outside Docker, see the README in `backend/` and `frontend/`.

## Branch & PR flow

1. Branch off `main` with a descriptive name: `feat/US-1-add-holding`, `fix/...`, `docs/...`,
   `chore/...`.
2. Make focused commits; keep the change scoped to one story/issue where possible.
3. Open a **pull request** into `main`. Link the user story / issue (US-#).
4. **CI must pass** (build + tests for both backend and frontend) before merge.
5. Merge to `main` (squash or merge commit — keep history readable).

Each user story (US-1 … US-15) is a GitHub issue labeled by tier (`core`, `secondary`,
`stretch`, `architectural`) and sprint, tracked on the project board.

## Testing expectations

- **New backend logic ships with pytest coverage.** API endpoints are validated in CI.
- **Frontend components** are tested with Vitest + React Testing Library.
- **API/integration** checks use Postman collections where applicable.
- Run the suites locally before opening a PR:

```bash
# Backend
docker compose run --rm backend pytest

# Frontend
docker compose run --rm frontend npm test
```

## Architecture & documentation rules

- **Keep engines decoupled behind the API contract.** The frontend and any engine call another
  engine **only** through defined API routes — never internal code (see
  [ADR 0004](docs/adr/0004-decoupled-engines-api-contract.md)).
- **Write or update an ADR** for any architecturally significant decision
  (`docs/adr/`, using `0000-template.md`). To reverse a past decision, add a new ADR that
  supersedes it — do not rewrite history. See `CLAUDE.md` for when to write vs. skip an ADR.
- **Keep diagrams current.** Update the C4 diagrams in
  [`docs/architecture.md`](docs/architecture.md) when the architecture changes; keep them
  consistent with `README.md` §2.
- **Respect the scope tiers** (core → secondary → stretch). Protect the core; new feature ideas
  go to the backlog, not the current sprint (see
  [ADR 0005](docs/adr/0005-scope-tiers.md)).

## Data & secrets hygiene

- **Never commit secrets.** All credentials/config come from environment variables via `.env`
  (git-ignored); document new variables in `.env.example`.
- **Never commit cached external data** (market data, filings). Local caches live under
  git-ignored paths.
- All external data is free/public and used for academic purposes only.
