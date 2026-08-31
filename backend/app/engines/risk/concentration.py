"""Concentration and exposure (US-7, FR-9).

Concentration asks a different question again. Volatility says how much the portfolio
swings; correlation says whether holdings swing together; concentration asks how much of
the portfolio depends on any single thing. A portfolio can be concentrated in two distinct
ways, and this module measures both:

* **Position concentration** — one holding is simply a large share of the total.
* **Overlapping exposure** — several holdings are individually modest but move as one,
  so their combined weight behaves like a single, much larger position. This is the
  concentration that hides: nothing in a holdings table reveals it.

The headline measure is the **Herfindahl-Hirschman Index** (HHI), the sum of squared
weights. It is the standard concentration measure in economics and antitrust, and it has a
property that makes it unusually explainable: its reciprocal is the **effective number of
holdings** — the count of equally-weighted positions that would be just as concentrated.
Eleven holdings with an effective number of three is a far more useful statement than
eleven raw weights.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

#: A position is called overweight above this multiple of an equal-weight share.
#: Relative rather than absolute (a flat "10%" rule is meaningless for a 3-holding
#: portfolio and far too strict for a 50-holding one). It is a framing heuristic, not a
#: rule with any regulatory standing.
OVERWEIGHT_MULTIPLE = 2.0

#: Pairs at or above this correlation are treated as overlapping exposure.
OVERLAP_CORRELATION = 0.75


@dataclass(frozen=True, slots=True)
class Position:
    """A holding reduced to what concentration math needs."""

    ticker: str
    weight: float  # fraction of portfolio value, 0..1


@dataclass(frozen=True, slots=True)
class OverlapGroup:
    """Holdings that move together closely enough to act as one position."""

    tickers: list[str]
    combined_weight: float
    #: Lowest pairwise correlation inside the group — how tightly it actually coheres.
    min_correlation: float


def herfindahl_index(weights: Sequence[float]) -> float | None:
    """Sum of squared weights, on weights normalized to sum to 1.

    Ranges from ``1/n`` (perfectly equal) to ``1`` (everything in one holding).
    """
    total = sum(weights)
    if not weights or total <= 0:
        return None
    return sum((w / total) ** 2 for w in weights)


def effective_holdings(weights: Sequence[float]) -> float | None:
    """``1 / HHI`` — the number of equally-weighted positions that would be as concentrated.

    Ten holdings where one dominates might have an effective count near 1; ten equal
    holdings have exactly 10. This is the most legible single statement of concentration.
    """
    hhi = herfindahl_index(weights)
    if hhi is None or hhi <= 0:
        return None
    return 1.0 / hhi


def top_n_weight(weights: Sequence[float], n: int) -> float | None:
    """Combined share of the ``n`` largest positions, on normalized weights."""
    total = sum(weights)
    if not weights or total <= 0 or n <= 0:
        return None
    ordered = sorted((w / total for w in weights), reverse=True)
    return sum(ordered[:n])


def overweight_positions(
    positions: Sequence[Position], *, multiple: float = OVERWEIGHT_MULTIPLE
) -> list[Position]:
    """Positions exceeding ``multiple`` times an equal-weight share of the portfolio."""
    if len(positions) < 2:
        return []
    equal_weight = 1.0 / len(positions)
    threshold = equal_weight * multiple
    return sorted(
        (p for p in positions if p.weight > threshold), key=lambda p: p.weight, reverse=True
    )


def overlapping_exposure(
    positions: Sequence[Position],
    tickers: Sequence[str],
    matrix: Sequence[Sequence[float | None]],
    *,
    threshold: float = OVERLAP_CORRELATION,
) -> list[OverlapGroup]:
    """Group holdings that all move together, and report their combined weight.

    Grouping is transitive-by-linkage: a holding joins a group when it correlates at or
    above ``threshold`` with **every** member already in it. Requiring agreement with the
    whole group (rather than just one member) prevents a chain of loosely-related holdings
    from being reported as a single tight cluster.

    Only groups of two or more are returned, ordered by combined weight — the biggest
    hidden position first.
    """
    weight_by_ticker = {p.ticker: p.weight for p in positions}
    index = {t: i for i, t in enumerate(tickers)}

    def rho(a: str, b: str) -> float | None:
        ia, ib = index.get(a), index.get(b)
        if ia is None or ib is None:
            return None
        return matrix[ia][ib]

    # Largest holdings seed groups first, so a group forms around what matters most.
    ordered = sorted(
        (t for t in tickers if t in weight_by_ticker),
        key=lambda t: weight_by_ticker[t],
        reverse=True,
    )

    groups: list[list[str]] = []
    assigned: set[str] = set()
    for ticker in ordered:
        if ticker in assigned:
            continue
        group = [ticker]
        for candidate in ordered:
            if candidate in assigned or candidate == ticker:
                continue
            correlations = [rho(candidate, member) for member in group]
            if all(c is not None and c >= threshold for c in correlations):
                group.append(candidate)
                assigned.add(candidate)
        assigned.add(ticker)
        if len(group) > 1:
            groups.append(group)

    result: list[OverlapGroup] = []
    for group in groups:
        pairs = [rho(a, b) for i, a in enumerate(group) for b in group[i + 1 :]]
        defined = [p for p in pairs if p is not None]
        result.append(
            OverlapGroup(
                tickers=sorted(group),
                combined_weight=sum(weight_by_ticker[t] for t in group),
                min_correlation=min(defined) if defined else threshold,
            )
        )

    return sorted(result, key=lambda g: g.combined_weight, reverse=True)
