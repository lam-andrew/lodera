import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AddHoldingForm } from "@/features/holdings/AddHoldingForm";
import { HoldingsTable } from "@/features/holdings/HoldingsTable";
import { ImportCard } from "@/features/import/ImportCard";
import { riskByTicker, type PortfolioData } from "@/hooks/usePortfolio";

interface HoldingsPageProps {
  data: PortfolioData;
  onChanged: () => void;
}

/** Managing positions (US-1, US-2, US-3) — kept off the dashboard so the overview stays
 *  scannable and the editing tools stay together. */
export function HoldingsPage({ data, onChanged }: HoldingsPageProps) {
  const { summary, risk } = data;

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <div className="flex items-baseline justify-between gap-3">
            <CardTitle>Holdings</CardTitle>
            <span className="font-mono text-xs text-faint">
              {summary.positions.length} {summary.positions.length === 1 ? "position" : "positions"}
            </span>
          </div>
          <CardDescription>Edit a quantity or remove a position.</CardDescription>
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

      <div className="grid gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Add a holding</CardTitle>
            <CardDescription>Enter a ticker and the number of shares you hold.</CardDescription>
          </CardHeader>
          <CardContent>
            <AddHoldingForm onAdded={onChanged} />
          </CardContent>
        </Card>

        <ImportCard onImported={onChanged} />
      </div>
    </div>
  );
}
