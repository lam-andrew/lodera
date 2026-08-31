import { useCallback, useEffect, useState } from "react";

import {
  getPortfolioRisk,
  getPortfolioSummary,
  toErrorMessage,
  type HoldingRisk,
  type PortfolioRisk,
  type PortfolioSummary,
} from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskCard } from "@/features/risk/RiskCard";

import { AddHoldingForm } from "./AddHoldingForm";
import { HoldingsTable } from "./HoldingsTable";

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; summary: PortfolioSummary; risk: PortfolioRisk | null }
  | { kind: "error"; message: string };

/** Loads holdings, prices, and risk together.
 *
 *  Risk is loaded alongside but is allowed to fail on its own: a volatility hiccup should
 *  never hide the holdings the user came to see. */
async function loadAll(): Promise<{ summary: PortfolioSummary; risk: PortfolioRisk | null }> {
  const [summary, risk] = await Promise.all([
    getPortfolioSummary(),
    getPortfolioRisk().catch(() => null),
  ]);
  return { summary, risk };
}

function indexRisk(risk: PortfolioRisk | null): Record<string, HoldingRisk> {
  if (risk === null) return {};
  return Object.fromEntries(risk.holdings.map((h) => [h.ticker, h]));
}

/** The portfolio screen: holdings with live prices and volatility (US-1, US-3, US-4, US-5). */
export function PortfolioView() {
  const [load, setLoad] = useState<LoadState>({ kind: "loading" });

  const refresh = useCallback(async () => {
    try {
      const { summary, risk } = await loadAll();
      setLoad({ kind: "ready", summary, risk });
    } catch (err) {
      setLoad({ kind: "error", message: toErrorMessage(err) });
    }
  }, []);

  // Initial load. State is set only inside the async callbacks, never synchronously.
  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const { summary, risk } = await loadAll();
        if (active) setLoad({ kind: "ready", summary, risk });
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
      {load.kind === "ready" && load.risk !== null && positions.length > 0 && (
        <RiskCard risk={load.risk} />
      )}

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
              riskByTicker={indexRisk(load.risk)}
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
