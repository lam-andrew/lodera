# Software Testing Report — Orbit

**Project:** Orbit (repository: `portfolio-risk-intelligence`)
**Course:** SWENG 894 — Penn State MSE Capstone
**Status:** Living document. Created Week 2; updated as test coverage grows.

> Initial version. This document grows with the test suite; the final version is a Week 14
> deliverable, but it is maintained continuously rather than assembled at the end.

---

## 1. Test strategy

Testing is organized as a pyramid, weighted toward fast, deterministic tests at the bottom.

| Level | Tool | What it covers | Speed |
|---|---|---|---|
| **Unit — engine** | pytest | Risk math in isolation: volatility, correlation, concentration, drawdown. Pure functions, no I/O. | Milliseconds |
| **Unit — frontend** | Vitest + React Testing Library | Component rendering, formatting, interaction, empty/error states. | Seconds |
| **Integration — API** | pytest + FastAPI `TestClient` | Full request/response cycle through real routes, real persistence, real caching, with a fake market-data provider. | Seconds |
| **Integration — stack** | Docker Compose in CI | The whole stack boots and services communicate. | Minutes |
| **Manual / exploratory** | Postman, browser | API contract exploration; visual verification against live market data. | Ad hoc |

### Guiding principles

1. **The algorithmic core is tested against independently known answers**, not against its own
   output. Correlation results are cross-checked against NumPy's `corrcoef`; the Herfindahl
   index is checked against a hand-computed value. A test that only asserts the code does what
   the code does would pass even if the mathematics were wrong.
2. **No network in the automated suite.** A fake market-data provider is injected, so tests are
   deterministic, run without an API key, and do not consume the provider's rate-limited quota.
3. **Bugs become regression tests.** Every defect found in manual verification is reproduced as
   a failing test before it is fixed, and the fix is confirmed by that test passing.
4. **A regression test must be shown to fail.** For concurrency and caching defects in
   particular, a test is only trusted once it has been observed failing against the unfixed
   code. A concurrency test that passes for the wrong reason is worse than no test.

---

## 2. What the automated suite covers today

As of 2026-09-02: **228 automated tests** (182 backend, 46 frontend), all passing, all run in CI
on every push and pull request.

| Requirement | Covered by |
|---|---|
| FR-1 (add holding) | API tests for valid input, unrecognized ticker, duplicate ticker, invalid quantity |
| FR-2, FR-3 (CSV import + validation) | Parser tests against per-brokerage fixtures (Fidelity, Schwab, Vanguard), plus preamble rows, ranked header aliases, currency formatting, structural total rows, per-row error reporting |
| FR-4 (manage holdings) | API CRUD tests; frontend interaction tests for inline edit and confirm-before-delete |
| FR-5, FR-6 (retrieve + cache) | Cache freshness (TTL), cache coverage (a narrow earlier fetch must not satisfy a wider request), provider-failure degradation, single-flight concurrent fetch |
| FR-7 (volatility) | Engine unit tests against hand-computed values; portfolio volatility via covariance; diversification benefit |
| FR-8 (correlation) | Engine unit tests cross-checked against NumPy; most/least correlated pairs; identical-series and constant-series edge cases |
| FR-9 (concentration) | Hand-computed Herfindahl index and effective holdings; overweight detection; overlapping-exposure grouping |
| FR-10 (drawdown) | Synthetic peak/trough/recovery series; unrecovered episodes reported rather than dropped |
| FR-12 (dashboard) | Frontend component and routing tests; loading, empty, and error states |
| FR-15 (authenticate) | Unauthenticated rejection on every portfolio route; session lifecycle; logout revocation; ownership isolation; uniform response for unknown email vs wrong password |
| AR-1 (containerized) | CI integration job boots the full Compose stack and asserts services communicate |
| AR-2 (decoupled engines) | Engine modules import no database, HTTP, or provider code — checked directly |

### Not yet covered

FR-11 (stress testing), FR-13 (filing ingestion), and FR-14 (grounded Q&A) are Sprint 3 stories.
Their tests will be written with the features. FR-14 in particular needs a **grounding test**:
every claim in an answer must be traceable to retrieved source text, which is a correctness
property, not a style preference.

---

## 3. Quality gates in CI

Every push and pull request runs, and must pass before merge:

| Gate | Tool | Enforces |
|---|---|---|
| Backend lint | Ruff | Style and common defect patterns |
| Backend types | mypy (strict) | Type correctness |
| Backend tests | pytest | Behavior |
| Frontend lint | ESLint | Style and defect patterns |
| Frontend format | Prettier | Consistent formatting |
| Frontend types | tsc | Type correctness |
| Frontend tests | Vitest | Behavior |
| Frontend build | Vite | The app actually builds |
| Stack integration | Docker Compose | The system boots and communicates |
| Static analysis | CodeQL | Security defects in code |
| Secret scanning | gitleaks | Credentials never enter history |
| Dependency audit | pip-audit, npm audit | Known vulnerabilities in dependencies |
| Filesystem scan | Trivy | Vulnerabilities in the image surface |

Gates also run locally through pre-commit hooks, so failures are usually caught before a push.
Rationale and the decision to adopt these gates are in
[ADR 0007](adr/0007-quality-gates-and-security-scanning.md).

---

## 4. Verifying the risk mathematics

The risk engine is the graded algorithmic component, so its correctness is established three
independent ways rather than by unit tests alone:

1. **Mathematical properties.** A series correlated with itself is exactly 1.0; a correlation
   matrix is symmetric with a unit diagonal; portfolio volatility computed from the covariance
   matrix never exceeds the weighted average of individual volatilities unless every pair is
   perfectly correlated.
2. **Independent implementations.** Results are compared against NumPy's own routines and
   against values computed by hand, not against previously recorded output of the same code.
3. **Financial plausibility.** Metrics are checked against real market data for ordering that
   must hold in reality: a bond fund must show lower volatility than a broad equity index,
   which must show lower volatility than a single speculative stock. This catches whole
   classes of error that unit tests on synthetic data cannot, such as a wrong annualization
   factor.

Methodological conventions being tested against are fixed in
[ADR 0012](adr/0012-risk-methodology.md).

---

## 5. Change log

| Date | Change |
|---|---|
| 2026-09-02 | Initial testing report created as a living document. |
