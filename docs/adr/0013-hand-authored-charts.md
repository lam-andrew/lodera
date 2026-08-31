# 0013. Hand-authored SVG charts instead of a charting library

- **Status:** Accepted
- **Supersedes:** the charting portion of [0009](0009-ui-styling-tailwind-shadcn-tremor.md)
  (Tailwind and shadcn/ui from that ADR remain in force)
- **Date:** 2026-08-30

## Context

ADR 0009 chose **Tremor** as the charting layer, decided before any chart had been built.
Having now built the correlation heatmap (US-6), the value sparkline (US-10), and needing a
concentration breakdown and an underwater drawdown plot (US-7, US-8), the actual requirement
is clearer than it was at the time.

Two things changed the picture:

1. **The charts we need are simple.** An underwater area plot, weight bars, and a sparkline
   are each a path or a few rectangles. None needs a legend engine, axis auto-scaling, zoom,
   or a plugin system.
2. **Tremor's theming works against ours.** Tremor v3 styles itself through `tremor-*` colour
   keys registered in `tailwind.config`. Orbit's design system
   (`docs/design/ui-direction.md`) is built on semantic CSS custom properties that retheme
   for light and dark at the token level. Adopting Tremor means maintaining a second,
   parallel colour vocabulary and reconciling the two on every theme change.

Tremor 3.18.7 is compatible with our React 18, so this is not a compatibility failure — it
is a fit judgement made with information we did not have when 0009 was written.

## Decision

We will **author charts as inline SVG components** in `frontend/src/components/ui/` and
`frontend/src/features/risk/`, and **not** adopt Tremor or another charting library.

- Charts read the same CSS custom properties as the rest of the interface, so they retheme
  automatically with no parallel palette.
- Each chart is a small, readable component: a path builder plus tokens.
- Accessibility is explicit — charts carry `role="img"` with a label, and every figure
  rendered graphically is also available as text.

If a future story genuinely needs axis machinery — zoomable time series, brushing, a
candlestick view — this decision should be revisited with a superseding ADR rather than
stretched.

## Consequences

- **Positive:** No dependency, no bundle cost, and no second colour vocabulary to keep in
  sync with the design tokens; charts theme correctly in both modes for free.
- **Positive:** Full control over the exact marks the data-visualization guidance calls for
  (diverging scale for correlation, emphasized endpoint on sparklines, non-positive-only
  underwater fill).
- **Cost:** We implement and maintain tooltips, scaling and responsiveness ourselves. For
  the handful of chart types in scope this is a modest, bounded amount of code; it would not
  be if the chart catalogue grew substantially.
- **Cost:** Contributors write SVG rather than composing library components, which is a
  slightly higher bar. Mitigated by keeping each chart small and documented.

## Alternatives Considered

- **Adopt Tremor as originally planned:** fastest path to axis charts and tooltips, but
  requires maintaining a `tremor-*` colour scale beside our semantic tokens and accepting its
  visual defaults in a design system we deliberately specified.
- **Recharts / visx:** more flexible than Tremor and less opinionated visually, but both are
  substantially heavier than the four small charts this product needs.
- **Keep 0009 unchanged and quietly hand-roll anyway:** rejected outright — the point of
  keeping ADRs is that the recorded decision matches what the code does.
