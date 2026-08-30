# 0009. UI styling: Tailwind + shadcn/ui + Tremor

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Orbit's value is largely conveyed through its interface: a risk dashboard with dense but
readable metrics (volatility, concentration, correlation, drawdown), a holdings table, and
later a filings Q&A view. The product should be visually appealing and trustworthy, and the
styling should be consistent, maintainable, accessible, and theme-aware. As a solo project we
also want to avoid re-inventing common components (tables, dialogs, tabs, charts) and avoid
lock-in to a heavy framework we cannot easily leave.

We surveyed the current React styling landscape and a set of fintech/analytics dashboard
templates for inspiration (recorded in `docs/design/ui-direction.md`). The consistent pattern
in the strongest references is a Tailwind base with shadcn/ui primitives, plus a dedicated
charting layer for the analytics widgets.

## Decision

We will style the frontend with **Tailwind CSS** as the styling engine, **shadcn/ui** for the
component primitives, and **Tremor** for charts and KPI tiles. The UI is **theme-aware
(dark-first, with a fully designed light theme)**.

- **Tailwind CSS** — utility-first styling, small production output, design tokens expressed as
  CSS variables so the palette and themes live in one place.
- **shadcn/ui** — accessible components built on Radix primitives that are **copied into our
  repo** (we own the source; no runtime dependency lock-in), which fits our provider-agnostic
  stance (see [ADR 0003](0003-docker-compose-provider-agnostic.md)).
- **Tremor** — analytics-focused chart and KPI components (bar/line/area, donut, KPI cards)
  that cover the risk dashboard's visualizations with far less bespoke SVG.
- All three are MIT licensed and free for commercial use.

The concrete visual direction (palette, typography, layout, and the feature-to-component
mapping) is documented in `docs/design/ui-direction.md`, with a rendered mockup for reference.

This stack is wired into the frontend when the first real UI ships (US-1). It is compatible
with our current React 18 + Vite setup and with the planned React 19 upgrade.

## Consequences

- **Positive:** A consistent, accessible, good-looking UI with most components and charts
  available off the shelf, so effort goes into the risk features rather than into building
  primitives.
- **Positive:** Owning the shadcn/ui component source means no version lock-in and full
  freedom to restyle; the theme lives in CSS variables, so a rebrand or palette change is
  localized.
- **Positive:** Tremor's chart set maps almost one-to-one onto our risk visuals (volatility,
  concentration, correlation, drawdown).
- **Cost:** Tailwind, shadcn/ui, and Tremor each add setup and a learning curve, and shadcn/ui
  components, being copied in, are maintained by us rather than upgraded via a package.
- **Cost:** Tremor is a real dependency to track for React-version compatibility (relevant to
  the planned React 19 / Vite 8 upgrade).

## Alternatives Considered

- **MUI (Material UI):** the most comprehensive component set with strong data-grid/charts, but
  a heavier bundle and a strong Material look that is harder to make feel bespoke. Better suited
  to enterprise admin tools than to a distinctive consumer-facing risk product.
- **Chakra UI / Mantine:** good DX and batteries-included, but they are runtime component
  libraries (less ownership than shadcn/ui) and still need a separate charting story.
- **Plain CSS / CSS Modules, hand-built components and charts:** maximum control and zero
  dependencies, but far more work to reach a polished, accessible result as a solo developer.
- **A paid dashboard template:** fastest visual start, but licensing cost, lock-in to its
  structure, and usually a Next.js base that does not match our React + Vite stack.
