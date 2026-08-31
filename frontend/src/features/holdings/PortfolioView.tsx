import { useCallback, useEffect, useState } from "react";

import { getPortfolioSummary, toErrorMessage, type PortfolioSummary } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { AddHoldingForm } from "./AddHoldingForm";
import { HoldingsTable } from "./HoldingsTable";

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; summary: PortfolioSummary }
  | { kind: "error"; message: string };

/** The portfolio screen: holdings with live prices (US-1, US-3, US-4). */
export function PortfolioView() {
  const [load, setLoad] = useState<LoadState>({ kind: "loading" });

  const refresh = useCallback(async () => {
    try {
      setLoad({ kind: "ready", summary: await getPortfolioSummary() });
    } catch (err) {
      setLoad({ kind: "error", message: toErrorMessage(err) });
    }
  }, []);

  // Initial load. State is set only inside the async callbacks, never synchronously.
  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const summary = await getPortfolioSummary();
        if (active) setLoad({ kind: "ready", summary });
      } catch (err) {
        if (active) setLoad({ kind: "error", message: toErrorMessage(err) });
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const positions = load.kind === "ready" ? load.summary.positions : [];

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <div className="flex items-baseline justify-between gap-3">
            <CardTitle>Holdings</CardTitle>
            <span className="font-mono text-xs text-faint">
              {positions.length} {positions.length === 1 ? "position" : "positions"}
            </span>
          </div>
          <CardDescription>Your positions, priced with end-of-day market data.</CardDescription>
        </CardHeader>
        <CardContent>
          {load.kind === "loading" && (
            <p role="status" className="py-8 text-center text-sm text-faint">
              Loading holdings…
            </p>
          )}
          {load.kind === "error" && (
            <p role="alert" className="py-8 text-center text-sm text-down">
              {load.message}
            </p>
          )}
          {load.kind === "ready" && (
            <HoldingsTable
              positions={load.summary.positions}
              totalValue={load.summary.total_value}
              onChanged={() => void refresh()}
            />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add a holding</CardTitle>
          <CardDescription>Enter a ticker and the number of shares you hold.</CardDescription>
        </CardHeader>
        <CardContent>
          <AddHoldingForm onAdded={() => void refresh()} />
        </CardContent>
      </Card>
    </div>
  );
}
