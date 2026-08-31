import { Link } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkline } from "@/components/ui/sparkline";
import { StatTile } from "@/components/ui/stat-tile";
import { formatCurrency } from "@/features/holdings/format";
import { HoldingsTable } from "@/features/holdings/HoldingsTable";
import { ConcentrationCard } from "@/features/risk/ConcentrationCard";
import { CorrelationCard } from "@/features/risk/CorrelationCard";
import { DrawdownCard } from "@/features/risk/DrawdownCard";
import { RiskBadge } from "@/features/risk/RiskBadge";
import { riskByTicker, type PortfolioData } from "@/hooks/usePortfolio";

function pct(value: string | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const n = Number(value);
  return Number.isNaN(n) ? "—" : `${n.toFixed(1)}%`;
}

interface DashboardPageProps {
  data: PortfolioData;
  onChanged: () => void;
}

/** Risk overview (US-10): summary tiles first, then the supporting detail. */
export function DashboardPage({ data, onChanged }: DashboardPageProps) {
  const { summary, risk, correlation, history, concentration, drawdown } = data;

  if (summary.positions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No holdings yet</CardTitle>
          <CardDescription>
            Add a position or import a brokerage export to see your risk profile.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link to="/holdings" className="text-sm text-accent underline-offset-4 hover:underline">
            Go to holdings →
          </Link>
        </CardContent>
      </Card>
    );
  }

  const values = (history?.points ?? []).map((p) => Number(p.value));
  const first = values[0];
  const last = values[values.length - 1];
  const changePct = first !== undefined && first !== 0 ? ((last - first) / first) * 100 : null;
  const rising = changePct !== null && changePct >= 0;

  const topWeight = [...summary.positions].sort(
    (a, b) => Number(b.weight_pct ?? 0) - Number(a.weight_pct ?? 0),
  )[0];

  return (
    <div className="flex flex-col gap-4">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
        <StatTile
          label="Portfolio value"
          value={formatCurrency(summary.total_value)}
          detail={
            changePct === null ? (
              `${summary.positions.length} positions`
            ) : (
              <span className={rising ? "text-up" : "text-down"}>
                {rising ? "+" : ""}
                {changePct.toFixed(1)}% over the window
              </span>
            )
          }
          chart={
            values.length > 1 ? (
              <Sparkline
                values={values}
                color={rising ? "var(--up)" : "var(--down)"}
                label="Portfolio value over time"
              />
            ) : undefined
          }
        />

        <StatTile
          label="Volatility"
          value={pct(risk?.portfolio_volatility_pct)}
          badge={<RiskBadge band={risk?.portfolio_band ?? null} />}
          detail={
            risk?.diversification_benefit_pct != null
              ? `${pct(risk.undiversified_volatility_pct)} without diversification`
              : "Annualized"
          }
        />

        <StatTile
          label="Average correlation"
          value={correlation?.average_correlation ?? "—"}
          detail={
            correlation?.most_correlated[0] !== undefined
              ? `Closest pair ${correlation.most_correlated[0].a}/${correlation.most_correlated[0].b} · ${correlation.most_correlated[0].correlation}`
              : "Across all pairs"
          }
        />

        <StatTile
          label="Effective holdings"
          value={
            concentration?.effective_holdings !== null &&
            concentration?.effective_holdings !== undefined
              ? Number(concentration.effective_holdings).toFixed(1)
              : "—"
          }
          detail={
            concentration !== null
              ? `from ${concentration.holdings_count} positions${topWeight !== undefined ? ` · ${topWeight.ticker} is ${pct(topWeight.weight_pct)}` : ""}`
              : "Concentration"
          }
        />

        <StatTile
          label="Worst decline"
          value={pct(drawdown?.max_drawdown_pct)}
          detail={
            drawdown?.current_drawdown_pct != null && Number(drawdown.current_drawdown_pct) < -0.05
              ? `currently ${pct(drawdown.current_drawdown_pct)} below peak`
              : "recovered to peak"
          }
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <div className="flex items-baseline justify-between gap-3">
              <CardTitle>Holdings</CardTitle>
              <Link
                to="/holdings"
                className="text-xs text-accent underline-offset-4 hover:underline"
              >
                Manage
              </Link>
            </div>
            <CardDescription>Priced with end-of-day market data.</CardDescription>
          </CardHeader>
          <CardContent>
            <HoldingsTable
              positions={summary.positions}
              totalValue={summary.total_value}
              riskByTicker={riskByTicker(risk)}
              onChanged={onChanged}
            />
          </CardContent>
        </Card>

        {correlation !== null && summary.positions.length > 1 ? (
          <CorrelationCard correlation={correlation} />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Correlation</CardTitle>
              <CardDescription>
                Add a second holding to see how your positions move together.
              </CardDescription>
            </CardHeader>
          </Card>
        )}
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        {concentration !== null && <ConcentrationCard data={concentration} />}
        {drawdown !== null && <DrawdownCard data={drawdown} />}
      </section>
    </div>
  );
}
