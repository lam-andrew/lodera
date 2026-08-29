# Lodera Frontend

React + TypeScript (Vite). Presentation only — it talks to the backend exclusively through
the typed API client in `src/api/`, which targets the backend's public API contract (never
engine internals).

## Layout

```
src/
  main.tsx           # React entry point
  App.tsx            # root component (Sprint 1: renders backend /health)
  api/client.ts      # typed backend client (axios; base URL from VITE_API_BASE_URL)
  test/setup.ts      # Vitest + Testing Library setup
```

## Environment

- `VITE_API_BASE_URL` — backend base URL. Defaults to `http://localhost:8000`.

## Run with Docker (recommended)

From the repo root: `docker compose up --build`. The app is served at `http://localhost:5173`.

## Run locally (without Docker)

```bash
cd frontend
npm install
npm run dev
```

## Test

```bash
cd frontend
npm install
npm test
```
