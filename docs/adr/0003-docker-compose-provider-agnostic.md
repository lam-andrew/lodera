# 0003. Docker + Docker Compose, provider-agnostic (no cloud lock-in)

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Lodera comprises multiple services (FastAPI backend, React frontend, PostgreSQL/pgvector
database) that must run together locally for development and be deployable to a real host for
the capstone demos. As a graded software-engineering project, reproducible builds, a
consistent local/CI/production environment, and portability all matter. A solo developer also
cannot afford to be locked into one cloud provider's proprietary services or to hand-configure
environments.

We needed a way to orchestrate the services that is reproducible, runs identically on any
developer machine and in CI, and does not tie the project to a specific cloud vendor.

## Decision

We will containerize every internal service with **Docker** and orchestrate them with
**Docker Compose**, keeping the stack **provider-agnostic** (no cloud-specific services).

- Each service (backend, frontend, database) has its own Dockerfile.
- A root `docker-compose.yml` brings the full stack up and lets the services communicate.
- The same images built and tested in CI are the images that get deployed.
- External dependencies (market-data API, SEC EDGAR, hosted LLM API) are reached over the
  network and configured via environment variables — never baked into images.

## Consequences

- **Positive:** One command (`docker compose up`) reproduces the whole environment; local, CI,
  and production stay consistent, which reduces "works on my machine" failures.
- **Positive:** The stack runs on any container-friendly host, satisfying the portability
  quality attribute and avoiding vendor lock-in.
- **Positive:** Services are isolated with explicit ports/networks, reinforcing the decoupled
  architecture (see [0004](0004-decoupled-engines-api-contract.md)).
- **Cost:** Docker adds build/image-management overhead and a learning cost. Image sizes and
  build caching need attention to keep CI fast.
- **Cost:** Provider-agnostic means we forgo managed conveniences (e.g. a managed vector DB or
  serverless autoscaling); we accept more manual ops in exchange for portability.

## Alternatives Considered

- **A specific PaaS (Heroku, Vercel + managed DB, AWS Elastic Beanstalk):** faster to deploy
  but couples the project to one vendor's model and config, conflicting with the no-lock-in
  goal.
- **Kubernetes:** far more powerful orchestration, but operationally heavy and unjustified for
  a three-service, single-developer, capstone-scale system.
- **Run services directly on the host (no containers):** lowest overhead, but sacrifices
  reproducibility and environment parity, which are exactly what a graded SE project needs.
