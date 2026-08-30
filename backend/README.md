# Orbit Backend

Python 3.12 + FastAPI. The API layer and the analytical engines (Risk & Exposure core; RAG
secondary). The API package is the backend's public contract; engines are reached only
through it (see [ADR 0004](../docs/adr/0004-decoupled-engines-api-contract.md)).

## Layout

```
app/
  main.py            # FastAPI entry point (application factory, CORS, router mount)
  api/               # THE API CONTRACT — routes + request/response schemas
    routes.py        # aggregated router (currently: /health)
    schemas.py       # Pydantic wire types
  core/              # cross-cutting: config (env), database engine/session
  engines/           # decoupled analytical engines (risk, rag) — added per user story
tests/               # pytest
```

## Run with Docker (recommended)

From the repo root: `docker compose up --build`. The API is served at
`http://localhost:8000`; interactive docs at `/docs`; health at `/health`.

## Run locally (without Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Test

```bash
cd backend
pip install -e ".[dev]"
pytest
```
