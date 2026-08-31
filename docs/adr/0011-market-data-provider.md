# 0011. Market data via Tiingo, behind a provider interface

- **Status:** Accepted
- **Date:** 2026-08-30

## Context

US-4 (FR-5, FR-6) requires historical daily prices for each holding so the Risk & Exposure
engine can compute volatility, correlation, drawdown, and stress results on real data. The
project constraints are free/public data only, a solo developer, and a system that must work
reliably during graded demos.

We surveyed the free tiers available in 2026:

| Provider | Free limits | Key | Notes |
|---|---|---|---|
| **Tiingo** | 50/hr, 1000/day, 500 symbols/mo, 30+ yrs history | yes | Clean, well-documented EOD data |
| Twelve Data | ~800/day, ~8/min | yes | Comfortable limits |
| Alpha Vantage | ~25/day | yes | Well known, but the daily cap is hit within minutes of development |
| yfinance | unpublished (throttled) | no | Unofficial Yahoo scraping; breaks without notice; ToS discourages automated access |

What we actually need is modest: **end-of-day daily bars**, a few years of history, for a
portfolio of roughly 10 to 30 symbols, refreshed at most once a day. We do not need
real-time quotes, intraday bars, or streaming. Because FR-6 requires local caching, live
calls are rare in steady state; rate limits mostly constrain development iteration.

## Decision

We will use **Tiingo** as the market-data provider for end-of-day historical prices, accessed
**behind a `MarketDataProvider` interface** so the concrete provider is swappable.

- The interface exposes what the risk engine needs (daily bars for a symbol over a date
  range), not Tiingo-specific shapes. No provider types leak past the data layer.
- The API key is supplied via the environment (`APP_MARKET_DATA_API_KEY`) and never
  committed; the provider is selected by `APP_MARKET_DATA_PROVIDER`.
- Retrieved prices are **cached in PostgreSQL** (FR-6) so repeated analysis does not re-fetch,
  which both respects the free tier and makes analysis fast and demo-safe.
- Tests run against a fake in-memory provider implementing the same interface, so the suite
  needs no network access and no API key.

Tiingo was chosen over the alternatives because it combines a genuinely usable free tier
(1000 requests/day is roughly 100x Alpha Vantage's) with 30+ years of clean, documented EOD
history, and unlike yfinance it is an official, keyed API that will not silently break.

## Consequences

- **Positive:** Comfortable rate limits for both development and demos; deep history supports
  meaningful volatility, correlation, and drawdown windows.
- **Positive:** The interface keeps the provider decision reversible. Swapping to Twelve Data
  or a paid feed later is a new implementation plus a config change, not a rewrite — and
  would be recorded as a superseding ADR.
- **Positive:** Caching satisfies FR-6, keeps us inside the free tier, and removes the network
  from the analysis path (fast, repeatable demos).
- **Cost:** Requires an account and an API key, so a fresh environment needs one manual setup
  step (documented in `README.md` and `.env.example`).
- **Cost / caveat:** Tiingo's free tier carries an **"internal use only"** license — it is
  intended for personal use rather than redistributing or publicly displaying the raw data.
  That fits this project's academic, non-commercial use (consistent with the project's
  free/public-data-for-research posture), and we display *derived risk metrics* rather than
  redistributing price feeds. If Orbit were ever commercialized or made publicly available,
  this licensing must be revisited (a paid tier or a differently-licensed provider) — a new
  ADR would record that change.
- **Cost:** A single external dependency for prices; if Tiingo is unavailable, analysis falls
  back to cached data (and degrades gracefully rather than failing).

## Alternatives Considered

- **yfinance (no key):** zero setup friction and popular in academia, but it scrapes an
  undocumented Yahoo endpoint, can break without notice, and Yahoo's ToS discourages automated
  access. Unacceptable risk for a graded demo and a public repository.
- **Alpha Vantage:** reputable and widely used, but ~25 requests/day is exhausted almost
  immediately during development and testing.
- **Twelve Data:** a solid runner-up with comfortable limits; Tiingo was preferred for data
  quality, documentation, and depth of history. This is the most likely swap target if Tiingo
  ever proves unsuitable.
- **A paid feed (Polygon, Databento):** better guarantees, but violates the free/public-data
  constraint and adds cost a capstone does not need.
