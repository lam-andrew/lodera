# Contributing to Orbit

Orbit is a solo Penn State MSE capstone (SWENG 894), but it is built to professional
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
git clone <repo-url> orbit && cd orbit

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

## Quality gates & pre-commit hooks

Quality and security gates run both locally and in CI (see
[ADR 0007](docs/adr/0007-quality-gates-and-security-scanning.md)). Set them up once:

```bash
# Backend tools (Ruff, mypy, pytest, pip-audit) into a venv
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]" && cd ..

# Frontend tools (ESLint, Prettier, Vitest, tsc)
npm --prefix frontend install

# Pre-commit: fast checks on commit, test suites on push
pip install pre-commit
pre-commit install --install-hooks
```

The local hooks use system tools, so keep the backend venv active (or on `PATH`) and the
frontend dependencies installed when committing.

**What runs where**

| Gate | Backend | Frontend |
|---|---|---|
| Lint | `ruff check` | `eslint` |
| Format | `ruff format` | `prettier` |
| Types | `mypy` (strict) | `tsc --noEmit` |
| Tests | `pytest` | `vitest` |

Run any of them by hand, e.g. `cd backend && ruff check . && mypy app && pytest`, or
`npm --prefix frontend run lint`. Run every hook across the repo with
`pre-commit run --all-files`.

## Testing expectations

- **New backend logic ships with pytest coverage.** API endpoints are validated in CI.
- **Frontend components** are tested with Vitest + React Testing Library.
- **API/integration** checks use Postman collections where applicable.
- Run the suites locally before opening a PR (via pre-commit on push, or directly):

```bash
# Backend
docker compose run --rm backend pytest

# Frontend
docker compose run --rm frontend npm test
```

## Security scanning

On every push/PR (and weekly), CI runs: **CodeQL** (SAST for Python + TS), **gitleaks**
(secrets), **pip-audit** / **npm audit** (dependency vulnerabilities), and **Trivy**
(filesystem vuln/secret/misconfig). **Dependabot** opens dependency-update PRs. Findings surface
in the repository's **Security** tab and as PRs. Note: CodeQL and Trivy SARIF results require a
public repository or GitHub Advanced Security.

## CI/CD

CI (`.github/workflows/ci.yml`) builds the container images and runs lint + type-check + tests
inside them, plus a full-stack integration check. **Continuous Deployment is deferred** until a
host is chosen — see [ADR 0008](docs/adr/0008-defer-continuous-deployment.md); the deploy
workflow is a manual-only placeholder until then.

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
