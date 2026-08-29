# Renaming the project

The product name is centralized so a **display-name** change is trivial, and a **full
rebrand** (identifiers + repo) is a bounded, mechanical task. This runbook captures both.

## 1. Change only the visible name (easy — no code change)

Everything the user sees reads from one constant per side:

- **Frontend:** `frontend/src/config/branding.ts` → `APP_NAME` (fallback `"Lodera"`).
- **Backend:** `backend/app/core/config.py` → `Settings.app_name` (fallback `"Lodera API"`),
  which sets the FastAPI/OpenAPI title and the `/health` `service` field.

Override at runtime without touching code via environment variables:

```bash
# .env
VITE_APP_NAME=NewName
APP_NAME=NewName API
```

That's the whole change for the name shown in the UI header, browser tab, and API docs.

## 2. Full rebrand (identifiers — mechanical find/replace)

These are technical identifiers, intentionally *not* wired to the display constant. Rename
them together when you want the codebase itself to stop saying "lodera":

| Where | What to change |
|---|---|
| `frontend/package.json`, `backend/pyproject.toml` | package `name` (`lodera-frontend`, `lodera-backend`) |
| `.github/workflows/ci.yml` | Docker image tags `lodera-backend` / `lodera-frontend` |
| `frontend/index.html` | static fallback `<title>` (pre-hydration only) |
| `.env.example`, `docker-compose.yml` | DB name/user (`lodera`) if you also rename the database |
| Comments & docs | `README.md`, `CLAUDE.md`, `docs/**`, file header comments |

Suggested approach: `git grep -il lodera` to list files, review, then a scoped find/replace.
Re-run the test suites and `docker compose up` afterward.

> The backend env-var prefix is intentionally **`APP_`** (brand-neutral), not the product
> name, so a rename does **not** touch env var names (`APP_NAME`, `APP_DATABASE_URL`, …).
> Vite requires the `VITE_` prefix for client vars — also brand-neutral.

### Renaming the database (optional)

The default DB name is `lodera`. Changing `POSTGRES_DB` only affects a **fresh** volume; an
existing dev volume keeps the old name. To reset locally: `docker compose down -v` (destroys
local data) then `docker compose up`. In a real environment, rename with SQL instead.

## 3. Rename the GitHub repository (easy)

```bash
gh repo rename NEW-NAME            # from within the repo
git remote set-url origin https://github.com/lam-andrew/NEW-NAME.git
```

GitHub automatically **redirects** the old URLs (web, git, API), so existing clones and links
keep working — but update the remote as above and any hard-coded URLs in docs/badges. The
GitHub **Project board** and issues are unaffected by a repo rename.

## Order of operations for a late-phase rename

1. Decide the new name.
2. Do step 1 (display name) — immediate visible change, low risk.
3. Optionally do step 2 (identifiers) in one PR; run CI.
4. Do step 3 (repo rename) last; update the remote and any links.
