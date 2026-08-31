# 0012. Risk engine methodology and conventions

- **Status:** Accepted
- **Date:** 2026-08-30

## Context

US-5 introduces the first metric in the Risk & Exposure engine — the graded algorithmic core
of the project. Volatility looks like a one-line formula, but several choices materially
change the answer, and every later metric (correlation US-6, concentration US-7, drawdown
US-8, stress testing US-9) has to make the *same* choices or the numbers stop being
comparable with one another. Fixing these conventions once, in writing, is what keeps the
engine coherent as it grows.

## Decision

The following conventions apply to every metric in `app/engines/risk/`.

**1. Adjusted close is the input series.** Raw close jumps discontinuously across splits and
dividends; a 4-for-1 split would otherwise register as a -75% daily return and dominate any
volatility estimate. We use the provider's split/dividend-adjusted series.

**2. Simple (arithmetic) returns**, `r_t = P_t / P_{t-1} - 1`, not log returns. A portfolio's
simple return is *exactly* the weighted sum of its holdings' simple returns, which is the
identity that makes portfolio-level covariance math correct. That identity holds only
approximately for log returns.

**3. Sample statistics (`ddof=1`).** We hold a sample of history, not the population.

**4. Annualize by `sqrt(252)`.** Variance scales linearly with time, so standard deviation
scales with its square root; 252 is the conventional count of US trading days per year.

**5. Portfolio risk uses the full covariance matrix**, `sigma_p = sqrt(wT Σ w)` — never a
weighted average of individual volatilities. The weighted average implicitly assumes every
holding moves in lockstep and therefore overstates risk. The gap between the two *is* the
diversification effect, and we surface it explicitly rather than hiding it.

**6. Refuse to answer on thin data.** Below 20 observations an estimate is returned as
`None` rather than as a falsely precise number.

**7. The engine is pure.** Modules under `app/engines/risk/` import nothing from the API,
database, or provider layers: they take plain sequences and return plain numbers. Callers
reach them only through the API layer (ADR 0004), which is what lets the math be unit-tested
against independently computed values.

**8. `Decimal` for money, `float` for statistics.** Prices are exact (`Decimal`) end to end
through storage. They convert to `float` at the engine boundary, because a volatility
estimate is inherently approximate and `Decimal` would imply a precision the number does not
have.

**9. Bands are descriptive, not advice.** `low` / `moderate` / `high` (<15%, 15-25%, >25%
annualized) exist so a bare number can be framed in words. They are conventional reference
points, not thresholds with regulatory meaning, and never a recommendation — consistent with
the product rule that Orbit measures and explains but does not advise.

## Consequences

- **Positive:** Later metrics inherit a settled return convention and data source, so
  correlation, drawdown, and stress results are mutually consistent by construction.
- **Positive:** Engine purity makes the graded algorithmic component directly testable; the
  volatility tests check output against an independently computed covariance formula and
  against known properties (perfectly correlated holdings get no diversification benefit;
  two equal uncorrelated holdings approach `sigma / sqrt(2)`).
- **Positive:** Surfacing the undiversified comparison turns a bare number into an
  explanation, which is the product's stated purpose.
- **Cost:** Requiring adjusted close means the engine depends on the provider supplying one
  (Tiingo does; a future provider without it would need adjustment applied upstream).
- **Cost:** `sqrt(252)` annualization assumes returns are serially uncorrelated. Real returns
  exhibit mild autocorrelation and volatility clustering, so the figure is an estimate, not a
  guarantee. Accepted as the standard industry convention; a future ADR could introduce
  EWMA or GARCH weighting if the simple estimate proves inadequate.

## Alternatives Considered

- **Log returns:** additive across time and common in academic work, but they break the exact
  portfolio-aggregation identity that the covariance approach depends on.
- **Weighted-average volatility for the portfolio:** far simpler, but it ignores correlation
  entirely and would systematically overstate portfolio risk — it would also make US-6
  (correlation) pointless, since diversification would never show up in the numbers.
- **Exponentially weighted (EWMA) volatility:** more responsive to recent regime changes, but
  it adds a decay parameter to justify and obscures the simple, explainable definition that
  suits a tool whose purpose is to *explain* risk. Revisit if responsiveness becomes a
  requirement.
