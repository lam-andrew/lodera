# Architecture Decision Records

This directory holds Lodera's Architecture Decision Records (ADRs): short documents that
capture an architecturally significant decision, its context, and its consequences.

## Conventions

- Files are named `NNNN-short-title.md` with a zero-padded, monotonically increasing number.
- Every ADR uses [`0000-template.md`](0000-template.md) and contains: **Title · Status · Date ·
  Context · Decision · Consequences · Alternatives Considered**.
- **Status** is one of `Proposed`, `Accepted`, or `Superseded by NNNN`.
- Decisions are **append-only**: to reverse one, add a new ADR that supersedes it and set the
  old ADR's status to `Superseded by NNNN`. Never rewrite a past decision's history.
- Write an ADR for architecturally significant choices (structure, data flow, external
  interfaces, cross-cutting concerns, security, deployment, scope). Skip ADRs for tiny,
  low-risk, easily reversible, or already-covered decisions. See `CLAUDE.md` →
  "Documentation standards" for the full rule.

## Index

| ADR | Title | Status |
|---|---|---|
| [0000](0000-template.md) | Template | — |
| [0001](0001-backend-frontend-stack.md) | Python + FastAPI backend, React + TypeScript frontend | Accepted |
| [0002](0002-postgres-pgvector.md) | PostgreSQL 16 + pgvector (relational + vector store in one service) | Accepted |
| [0003](0003-docker-compose-provider-agnostic.md) | Docker + Docker Compose, provider-agnostic (no cloud lock-in) | Accepted |
| [0004](0004-decoupled-engines-api-contract.md) | Decoupled engines behind an API contract | Accepted |
| [0005](0005-scope-tiers.md) | Scope tiers: core / secondary / stretch | Accepted |
| [0006](0006-portfolio-ingestion-manual-csv.md) | Portfolio ingestion via manual entry + CSV for MVP | Accepted |
| [0007](0007-quality-gates-and-security-scanning.md) | CI quality gates and security scanning | Accepted |
| [0008](0008-defer-continuous-deployment.md) | Defer Continuous Deployment until a host is selected | Accepted |
| [0009](0009-ui-styling-tailwind-shadcn-tremor.md) | UI styling: Tailwind + shadcn/ui + Tremor | Accepted |
