# 0005. Scope tiers: core (risk engine) / secondary (RAG) / stretch (deferred)

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Orbit is built by a solo developer on a fixed 14-week (4-sprint) capstone timeline. Feature
ideas naturally exceed what one person can deliver well in that window, and an unbounded scope
would put the graded algorithmic centerpiece at risk. Per instructor guidance, the **Risk &
Exposure engine is the core deliverable**, the RAG layer is secondary, and several attractive
features (regime detection, anomaly detection, automated brokerage connection) are not
committed.

We needed an explicit, written prioritization rule so that in-session decisions (human or AI)
protect the graded core and do not silently pull deferred work into the current sprint.

## Decision

We will organize all work into three **scope tiers** and treat them as a hard prioritization
rule:

- **Core (committed):** portfolio ingestion + the Risk & Exposure engine — volatility,
  correlation, concentration/exposure, drawdown, stress testing. This is the primary focus and
  the significant algorithmic component.
- **Secondary (in scope, after the core is stable):** RAG over SEC filings with grounded, cited
  answers.
- **Stretch (backlog, only if the core finishes early):** regime detection, anomaly detection,
  automated brokerage connection. **Not built unless explicitly instructed.**

When in doubt, protect the core and defer everything else to the backlog. The tiers must not be
blurred.

## Consequences

- **Positive:** A clear, always-available priority order keeps the solo developer and any AI
  session focused on the graded core and prevents scope creep from destabilizing it.
- **Positive:** Sequencing (core → secondary → stretch) means the secondary RAG engine is only
  started once the core is stable, and it attaches via the API contract
  (see [0004](0004-decoupled-engines-api-contract.md)) without touching the core.
- **Cost:** Attractive stretch features may not ship. This is an accepted, deliberate trade to
  guarantee a solid, well-tested core within the timeline.

## Alternatives Considered

- **Flat backlog with no tiers, prioritized ad hoc each sprint:** more flexible, but invites
  scope creep and risks under-investing in the graded core.
- **Committing to the stretch features up front:** more ambitious, but a solo developer on 14
  weeks would likely deliver several shallow, half-tested features instead of one strong,
  well-engineered core — the opposite of what the capstone rewards.
