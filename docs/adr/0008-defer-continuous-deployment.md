# 0008. Defer Continuous Deployment until a host is selected

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

The project targets a full CI/CD pipeline. Continuous **Integration** is in place from the
foundation: every push builds the container images and runs the full test and security suites
(see [ADR 0007](0007-quality-gates-and-security-scanning.md)). Continuous **Deployment** — the
step that ships those images to a running environment — requires a concrete deployment target:
a host, its credentials, a registry, and a rollback story.

By design, Lodera is provider-agnostic with **no host chosen yet**
(see [ADR 0003](0003-docker-compose-provider-agnostic.md)); the Sprint 1 goal is a running,
locally-deployable stack, and the graded demos are the milestones that actually need a hosted
environment. Wiring a deploy job now would mean either inventing a target we have not committed
to (creating misleading, dead configuration and secrets) or blocking foundation work on an
infrastructure decision that does not need to be made yet.

## Decision

We will **defer Continuous Deployment** until a deployment target is selected. Concretely:

- CI (build + test + scan of the deployable images) is fully in place now.
- A **manual, no-op placeholder** deploy workflow (`.github/workflows/deploy.yml`,
  `workflow_dispatch` only) documents where deployment will attach and intentionally does
  nothing until configured — so there is a visible, honest placeholder rather than fake
  infrastructure.
- When a host is chosen, a **new ADR will supersede this one**, recording the target, the image
  registry, how secrets are managed, and the deploy/rollback flow; the placeholder workflow will
  then be implemented (e.g. push images to a registry and deploy on merge to `main` or on tag).

## Consequences

- **Positive:** No misleading or dead deployment config, no unused cloud credentials, and no
  premature lock-in — consistent with the provider-agnostic stance.
- **Positive:** Foundation and feature work proceed without waiting on an infrastructure
  decision; the images CI produces are already deploy-ready when a target is chosen.
- **Cost:** "CD" is not literally continuous yet — deploying for a demo is a manual step until
  the pipeline is completed. Accepted for now; revisited before the Sprint 2 demo.

## Alternatives Considered

- **Wire a specific host now (e.g. Fly.io, Render, a VPS, GHCR + a runner):** delivers true CD
  immediately, but commits to a provider before it is needed and adds real secrets/config to
  maintain for a target that may change. Deferred, not adopted.
- **Publish images to a registry on every push (build-and-push, no deploy):** a partial step that
  still needs a registry decision and credentials; folded into the future CD ADR instead of done
  piecemeal now.
