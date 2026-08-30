# Orbit UI direction

The visual direction for Orbit's interface, the research behind it, and the design tokens to
build against. The component/styling stack decision lives in
[ADR 0009](../adr/0009-ui-styling-tailwind-shadcn-tremor.md); this document is the richer
reference for *how it should look and feel*.

> A rendered mockup of the risk dashboard in this direction (dark and light, live charts) is
> published as an artifact:
> **https://claude.ai/code/artifact/33ddf929-526b-4e84-b457-fe74ce0eda03**
>
> The mockup is **directional**, not the final UI. Real screens are built per user story and
> will refine it; the tokens and principles below are the durable part.

## Direction in one line

Dark-first, data-dense but calm. Monochrome, cool-charcoal surfaces with color reserved
strictly for financial state (gain/loss and risk level). Tabular figures everywhere. One hero
metric per card. "Show the data, hide the chrome."

Why this fits Orbit specifically: risk tools easily provoke anxiety. The strongest financial
dashboards counter that with restraint, whitespace, and softer alerting, so the interface reads
as a calm analyst rather than a flashing monitor. Visual calm reads as trust.

## Principles

1. **Color encodes state, not decoration.** A single azure accent for brand/interactive; green
   for gains, red for losses, and a low/moderate/high ramp for risk level. Nothing else is
   colored for its own sake.
2. **Numbers are the interface.** Monospaced, tabular figures with consistent precision, aligned
   in columns. Financial data should scan like a terminal, cleanly.
3. **Summary before detail.** KPI tiles at the top answer "how much risk?" at a glance; tables
   and charts below provide the breakdown.
4. **State reads at a glance.** Encode status in form as well as number: risk chips, delta pills,
   weight bars, a severity dot.
5. **Both themes are designed.** Dark is the default (and the star), but light is a full,
   legible design, not an inversion. Theme values live in CSS variables.
6. **Accessible and honest.** Legends plus direct labels (never color alone), visible focus,
   and copy that never implies prediction or advice, only measurement and explanation.

## Design tokens

Colors are expressed as CSS variables so the whole palette (and both themes) swap in one place.
Semantic colors are separate from the accent. Chart palettes are the validated categorical and
diverging sets from the data-viz method.

### Neutrals and accent

| Role | Dark | Light |
|---|---|---|
| Page ground | `#090c11` | `#f5f6f9` |
| Surface (cards) | `#111620` | `#ffffff` |
| Surface raised / hover | `#171d28` | `#eef1f5` |
| Hairline / border | `#212a36` | `#e7eaef` |
| Primary ink | `#eaeef4` | `#101620` |
| Secondary ink | `#a7b1c0` | `#4a525e` |
| Muted (labels/axes) | `#6c7686` | `#7a838f` |
| Accent (brand/interactive) | `#4a93f0` | `#2a78d6` |

The neutrals carry a slight cool/blue bias (a chosen neutral, not a default grey).

### Semantic (state)

| Role | Dark | Light |
|---|---|---|
| Gain / positive | `#3ec38a` | `#0f8a3c` |
| Loss / negative | `#f0655f` | `#d03b3b` |
| Risk: low | `#2fbf6b` | `#0ca30c` |
| Risk: moderate | `#e0a13a` | `#b9791a` |
| Risk: high | `#f0655f` | `#d03b3b` |

### Chart palettes (validated)

- **Categorical** (concentration donut, holding swatches), fixed order:
  blue `#3987e5`, orange `#d95926`, aqua `#199e70`, yellow `#c98500`, magenta `#d55181`,
  violet `#9085e9`, green, then fold the rest into "Other" (dark steps shown; light steps are
  the same hues stepped for the light surface).
- **Diverging** (correlation heatmap): blue (negative / diversifying) to grey (zero) to red
  (positive / moves together). Never a rainbow; grey neutral at the midpoint.
- **Sequential** (single-hue magnitude, when needed): one blue ramp, light to dark.

### Typography

- **UI / text:** IBM Plex Sans. Professional and slightly technical; deliberately not the Inter
  default.
- **Figures / data / eyebrows:** IBM Plex Mono, with `font-variant-numeric: tabular-nums` for
  any column of digits. This gives the calm "financial terminal" feel.
- Both load from Google Fonts. Keep a real fallback stack (`system-ui, sans-serif`).

### Layout

App shell: a fixed left sidebar (brand + grouped nav: Portfolio / Risk & Exposure / Insights)
and a main column with a top bar (page title, portfolio selector, data-source status, time
range). Content is a KPI tile row, then cards on a 12-column-ish grid. Cards are quiet: hairline
border, generous padding, a small radius, one job each.

## Feature to component mapping

How the risk stories render in this system (Tremor covers most charts):

| Story | Metric | UI |
|---|---|---|
| US-1 / US-3 | Holdings | Table: ticker + name, shares, price, market value, weight bar, 30D vol |
| US-5 | Volatility | KPI tile with a risk chip + sparkline; per-holding column in the table |
| US-7 | Concentration / exposure | Donut by position with a center "top-N %" and a legend |
| US-6 | Correlation | Diverging heatmap of holding-vs-holding correlation |
| US-8 | Drawdown | Underwater area plot (percent from prior peak) with the trough marked |
| US-10 | Risk dashboard | The composition of the above on the Overview screen |
| US-12 | Filings Q&A | Later; a grounded-answer view with citations (kept visually calm) |

## Inspiration (all MIT / free)

Researched Aug 2026. Used for inspiration only; we build our own on shadcn/ui + Tremor.

- **Shadcn Fintech** — the primary reference for the aesthetic (dark, calm, data-first).
  Live: https://shadcn-fintech.vercel.app/dashboard · Repo (MIT):
  https://github.com/abderrahimghazali/shadcn-fintech
- **Tremor** — analytics chart/KPI components (MIT), our charting layer. https://tremor.so
- **shadcn/ui** — component primitives we copy into the repo (MIT). https://ui.shadcn.com
- **Vault** (Robinhood-inspired investment dashboard) — domain inspiration.
  https://vault.dashboardpack.com
- Galleries: Dribbble `finance-dashboard`, Muzli dashboard inspiration, and the 2026 dark-mode
  dashboard guides.

## Status

Direction accepted; stack recorded in [ADR 0009](../adr/0009-ui-styling-tailwind-shadcn-tremor.md).
Wired into the frontend when the first UI ships (US-1). This document is updated as the design
system firms up during the dashboard stories.
