# User Guide — Orbit

**Status:** Living document. Created Week 2; grows as features land.

> Initial version. Sections are added as each feature ships, so that the final user
> documentation is written alongside the product rather than reconstructed from it.

---

## What Orbit is

Orbit helps a self-directed investor understand the risk in their own portfolio. Enter what
you hold, and Orbit measures how much it moves, how concentrated it is, how much its holdings
overlap, and how far it has fallen in the past. Every number comes with an explanation of what
it means and how it was calculated.

**What Orbit does not do.** It does not predict prices, recommend or place trades, or give
investment advice. It measures and explains what your portfolio already is. Treat its output
as one input to your own thinking, not as a recommendation.

---

## Getting started

### 1. Create an account

Orbit requires an account because your portfolio is private to you. Sign up with an email
address and a password. Your password is stored only as an irreversible hash, and Orbit never
asks for your brokerage login.

### 2. Add your holdings

Two ways:

- **Enter them manually.** Type a ticker symbol and the number of shares. This works for any
  brokerage.
- **Import a CSV.** Export a positions file from your brokerage and upload it. Orbit
  understands the export formats used by major brokerages, including their preamble rows,
  currency formatting, and total rows. Rows it cannot read are reported individually by line
  number, so a single bad row never silently drops a position.

A note on brokerage exports: some brokerages export *transactions* rather than *positions*.
Orbit needs positions, meaning what you currently hold. If your export lists individual buys
and sells, enter your positions manually instead.

### 3. Read your risk

Once you have holdings, Orbit fetches historical prices and computes:

| Metric | The question it answers |
|---|---|
| **Volatility** | How much does this swing, in a typical year? |
| **Correlation** | Which of my holdings move together, and which are genuinely different? |
| **Concentration** | How much of my money rides on my largest positions? |
| **Drawdown** | How far has this portfolio fallen from a peak, and how long did recovery take? |

---

## Understanding the numbers

Orbit includes a **methodology page** explaining every metric: the formula, why that method was
chosen over the alternatives, and what its limitations are, worked through using your own
portfolio's figures. Each risk card links directly to the relevant section.

Two things worth knowing before you interpret anything:

- **Volatility measures dispersion, not danger.** A high figure means a wide range of outcomes,
  up as well as down. It is not a prediction of loss.
- **All of this is backward-looking.** Every metric describes how your holdings have behaved
  historically. Correlations in particular tend to rise during market stress, which is exactly
  when diversification is most needed. Past behavior constrains your expectations; it does not
  determine the future.

---

## Sections to be added

As the remaining features ship, this guide will gain:

- **Stress testing** — reading scenario results (US-9).
- **Asking questions about your holdings** — the grounded, cited Q&A over SEC filings
  (US-11, US-12).

---

## Change log

| Date | Change |
|---|---|
| 2026-09-02 | Initial user guide created as a living document. |
