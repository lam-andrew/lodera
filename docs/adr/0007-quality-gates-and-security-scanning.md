# 0007. CI quality gates and security scanning

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Orbit is graded on software-engineering rigor, not just working features. As a solo project
that will accrue feature code quickly across four sprints, defects and inconsistencies are
cheapest to catch automatically and early — before code review or a demo. We want the same
industry-standard guardrails a professional team would run: consistent formatting, static
analysis, type checking, automated tests, and security scanning (SAST, secrets, and dependency
vulnerabilities). These should run both locally (fast feedback before a commit) and in CI (the
enforced gate before merge to `main`), and they should be established at the foundation stage
so quality is built in rather than retrofitted.

## Decision

We will enforce a layered set of quality and security gates, wired into pre-commit hooks
(local) and GitHub Actions (CI):

**Code quality**

- **Backend (Python):** [Ruff](https://docs.astral.sh/ruff/) for linting and formatting;
  [mypy](https://mypy-lang.org/) (strict) for static type checking; **pytest** for tests.
- **Frontend (TypeScript):** [ESLint](https://eslint.org/) (flat config, typescript-eslint +
  React Hooks rules) for linting; [Prettier](https://prettier.io/) for formatting; `tsc
  --noEmit` for type checking; **Vitest** for tests.

**Security scanning** (reported to the repository Security tab where applicable)

- **SAST:** [CodeQL](https://codeql.github.com/) for Python and JavaScript/TypeScript.
- **Secrets:** [gitleaks](https://github.com/gitleaks/gitleaks) scans history and diffs; GitHub
  native secret scanning also applies on public repositories.
- **Dependencies:** [Dependabot](https://docs.github.com/code-security/dependabot) opens update
  PRs for pip, npm, Docker base images, and GitHub Actions; `pip-audit` and `npm audit` gate on
  known vulnerabilities in CI.
- **Filesystem / images:** [Trivy](https://trivy.dev/) scans for vulnerabilities,
  misconfigurations, and secrets, uploading SARIF results.

**Where the gates run**

- **Local (pre-commit):** formatting, lint, type checks, and secret/large-file guards run on
  every commit; the full backend and frontend test suites run on push (`pre-push` stage).
- **CI (GitHub Actions):** the backend and frontend jobs run lint + type-check + test + build
  inside the same container images that get deployed; an integration job boots the full stack
  and asserts `/health`; separate CodeQL and Security workflows run the scanners.

**Calibration.** Dependency-audit gates fail on vulnerabilities in **shipped** (production)
dependencies; dev-only tooling advisories remain visible via Dependabot and Trivy without
blocking the pipeline, to avoid flaky red builds from transitive dev-server advisories.

## Consequences

- **Positive:** Consistent style and types across the codebase; regressions and many security
  issues are caught automatically before merge. The setup demonstrates the CI/CD and
  quality-engineering rigor the capstone is graded on.
- **Positive:** The same gates run locally and in CI, so contributors get fast feedback and CI
  rarely surprises them.
- **Positive:** Security findings are centralized in the GitHub Security tab (CodeQL, Trivy) and
  as Dependabot PRs.
- **Cost:** More configuration to maintain and keep versions current (mitigated by Dependabot on
  the Actions and tool versions). CI takes longer than tests alone.
- **Cost:** Some scanners (CodeQL/Trivy SARIF upload) require a **public** repository or GitHub
  Advanced Security; on a private repo without GHAS those steps will not surface results.
- **Cost:** Local pre-commit hooks that use system tools require the backend venv and frontend
  dependencies to be installed (documented in `CONTRIBUTING.md`).

## Alternatives Considered

- **No enforced gates (rely on discipline):** lowest overhead, but inconsistent quality and
  missed security issues — the opposite of what a graded SE capstone rewards.
- **Lean subset (lint + tests + Dependabot only):** lower maintenance, but forgoes SAST, secret,
  and container scanning that are standard practice and cheap to add now. Rejected in favor of
  the comprehensive set while the codebase is small.
- **Black + Flake8 + isort (backend):** the established trio, but Ruff replaces all three with a
  single, much faster tool and one config.
- **Third-party CI (CircleCI/GitLab CI):** capable, but GitHub Actions is already where the repo
  lives and integrates natively with CodeQL, Dependabot, and the Security tab.
