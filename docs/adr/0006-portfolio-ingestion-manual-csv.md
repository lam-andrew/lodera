# 0006. Portfolio ingestion via manual entry + CSV for MVP; brokerage connection deferred

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Before Lodera can compute any risk metric it needs a portfolio: a set of holdings (ticker +
share quantity) to analyze. There are several ways a user could get their holdings into the
system, ranging from typing them in, to uploading a broker's export file, to connecting a
brokerage account programmatically (e.g. via Plaid or SnapTrade).

Automated brokerage connection is attractive but is explicitly a **stretch** item
(see [0005](0005-scope-tiers.md)): it adds OAuth flows, a paid/rate-limited third-party
aggregator, financial-data security obligations, and provider lock-in — none of which serve the
graded algorithmic core, and all of which cost a solo developer scarce time.

We needed to decide how portfolios enter the system for the MVP.

## Decision

For the MVP we will support **two ingestion paths only**:

1. **Manual entry** — the user adds a holding by entering a ticker symbol and share quantity
   (user story US-1; requirement FR-1).
2. **CSV / brokerage-export upload** — the user uploads a file; the system validates it and
   reports any rows it cannot parse (user stories US-2/US-3; requirements FR-2, FR-3, FR-4).

**Automated brokerage connection is deferred** to the stretch backlog and will not be built
unless the core finishes early and it is explicitly prioritized.

## Consequences

- **Positive:** Both MVP paths use only free/public data and local processing — no third-party
  aggregator, no OAuth, no per-user financial-account credentials to secure, no vendor lock-in.
- **Positive:** Manual entry gives the fastest possible end-to-end slice for Sprint 1; CSV
  upload covers realistic portfolios without new external dependencies.
- **Positive:** Keeps effort on the graded risk core rather than on integration plumbing.
- **Cost:** Users must enter or export their holdings themselves rather than syncing
  automatically; portfolios can go stale between manual updates. Accepted for the MVP.
- **Cost:** CSV ingestion must handle messy real-world exports (varying columns/headers) and
  report unparseable rows clearly (FR-3).

## Alternatives Considered

- **Automated brokerage connection (Plaid/SnapTrade) for the MVP:** best user experience, but
  it is a stretch-tier feature that adds cost, security burden, and lock-in for no benefit to
  the graded core. Deferred, not adopted.
- **Manual entry only (no CSV):** simplest, but real portfolios have many positions; typing them
  all in is impractical, so CSV upload is included in the MVP.
