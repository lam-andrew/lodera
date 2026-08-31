import type { PortfolioConcentration } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ExplainLink } from "@/features/methodology/ExplainLink";

function pct(value: string | null): string {
  if (value === null) return "—";
  const n = Number(value);
  return Number.isNaN(n) ? "—" : `${n.toFixed(1)}%`;
}

/** Concentration and exposure (US-7).
 *
 *  Leads with effective holdings rather than raw weights: "11 positions behaving like 2.9"
 *  states the problem in one line, where a column of percentages leaves the reader to infer
 *  it. Overlap groups follow, because that is the concentration a holdings table hides. */
export function ConcentrationCard({ data }: { data: PortfolioConcentration }) {
  if (data.effective_holdings === null || data.holdings_count === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Concentration</CardTitle>
          <CardDescription>Add priced holdings to see where you are overexposed.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const effective = Number(data.effective_holdings);
  const count = data.holdings_count;
  // Concentrated when the portfolio behaves like less than half its holding count.
  const concentrated = effective < count / 2;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-baseline justify-between gap-3">
          <CardTitle>Concentration</CardTitle>
          <ExplainLink anchor="concentration" />
          <span className="font-mono text-xs text-faint">HHI {data.hhi}</span>
        </div>
        <CardDescription>How much of the portfolio depends on any single thing.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-5">
          <div>
            <div className="flex items-end gap-2.5">
              <span className="font-mono text-4xl font-medium leading-none tabular-nums tracking-tight">
                {effective.toFixed(1)}
              </span>
              <span className="mb-0.5 text-sm text-muted-foreground">
                effective holdings, from {count}
              </span>
            </div>
            <p className="mt-2 text-[13px] text-muted-foreground">
              {concentrated
                ? `Your ${count} positions behave like about ${effective.toFixed(1)} equally-weighted ones.`
                : `Your positions are spread fairly evenly across ${count} holdings.`}
            </p>
          </div>

          <dl className="grid grid-cols-3 gap-3 border-t border-border pt-4">
            {(
              [
                ["Largest", data.top_1_pct],
                ["Top 3", data.top_3_pct],
                ["Top 5", data.top_5_pct],
              ] as const
            ).map(([label, value]) => (
              <div key={label} className="flex flex-col gap-0.5">
                <dt className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                  {label}
                </dt>
                <dd className="font-mono text-lg tabular-nums">{pct(value)}</dd>
              </div>
            ))}
          </dl>

          {data.overweight.length > 0 && (
            <div className="flex flex-col gap-2 border-t border-border pt-4">
              <h3 className="text-sm font-medium">
                Overweight positions
                <span className="ml-2 font-normal text-xs text-faint">
                  more than {Number(data.overweight_multiple).toFixed(0)}× an equal share
                </span>
              </h3>
              <ul className="flex flex-col gap-1.5">
                {data.overweight.map((position) => (
                  <li key={position.ticker} className="flex items-center gap-3 text-sm">
                    <span className="font-mono font-medium">{position.ticker}</span>
                    <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-surface-2">
                      <span
                        className="block h-full rounded-full bg-down"
                        style={{ width: `${Math.min(Number(position.weight_pct), 100)}%` }}
                      />
                    </span>
                    <span className="font-mono tabular-nums text-muted-foreground">
                      {pct(position.weight_pct)}
                    </span>
                    <span className="w-14 text-right font-mono text-xs tabular-nums text-down">
                      {Number(position.times_equal_weight).toFixed(1)}×
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.overlaps.length > 0 && (
            <div className="flex flex-col gap-2 border-t border-border pt-4">
              <h3 className="text-sm font-medium">
                Overlapping exposure
                <span className="ml-2 font-normal text-xs text-faint">
                  move together above ρ {data.overlap_threshold}
                </span>
              </h3>
              <ul className="flex flex-col gap-2">
                {data.overlaps.map((group) => (
                  <li key={group.tickers.join("-")} className="flex flex-col gap-0.5">
                    <div className="flex items-baseline justify-between gap-3 text-sm">
                      <span className="font-mono font-medium">{group.tickers.join(" + ")}</span>
                      <span className="font-mono tabular-nums">
                        {pct(group.combined_weight_pct)}
                      </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      Behaves like one {pct(group.combined_weight_pct)} position (lowest pair ρ{" "}
                      {group.min_correlation})
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
