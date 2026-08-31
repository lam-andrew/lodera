import type { PortfolioRisk } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ExplainLink } from "@/features/methodology/ExplainLink";

import { RiskBadge } from "./RiskBadge";

function pct(value: string | null): string {
  if (value === null) return "—";
  const n = Number(value);
  return Number.isNaN(n) ? "—" : `${n.toFixed(1)}%`;
}

/** Portfolio-level volatility (US-5), with the diversification comparison. */
export function RiskCard({ risk }: { risk: PortfolioRisk }) {
  const hasFigure = risk.portfolio_volatility_pct !== null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-baseline justify-between gap-3">
          <CardTitle>Portfolio volatility</CardTitle>
          <span className="flex items-baseline gap-3">
            <span className="font-mono text-xs text-faint">
              {risk.observations > 0 ? `${risk.observations} trading days` : "—"}
            </span>
            <ExplainLink anchor="portfolio-volatility" />
          </span>
        </div>
        <CardDescription>
          Annualized standard deviation of daily returns — how much the portfolio swings.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!hasFigure ? (
          <p className="py-6 text-center text-sm text-faint">
            Not enough price history yet to measure volatility.
          </p>
        ) : (
          <div className="flex flex-col gap-5">
            <div className="flex items-end gap-3">
              <span className="font-mono text-4xl font-medium tabular-nums tracking-tight">
                {pct(risk.portfolio_volatility_pct)}
              </span>
              <RiskBadge band={risk.portfolio_band} className="mb-1.5" />
            </div>

            {risk.diversification_benefit_pct !== null && (
              <dl className="grid grid-cols-2 gap-x-6 gap-y-1 border-t border-border pt-4 text-sm">
                <dt className="text-muted-foreground">If holdings moved together</dt>
                <dd className="text-right font-mono tabular-nums">
                  {pct(risk.undiversified_volatility_pct)}
                </dd>
                <dt className="text-muted-foreground">Reduced by diversification</dt>
                <dd className="text-right font-mono tabular-nums text-up">
                  −{pct(risk.diversification_benefit_pct)}
                </dd>
              </dl>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
