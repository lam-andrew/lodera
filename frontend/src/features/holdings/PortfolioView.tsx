import { useCallback, useEffect, useState } from "react";

import { getHoldings, toErrorMessage, type Holding } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { AddHoldingForm } from "./AddHoldingForm";
import { HoldingsTable } from "./HoldingsTable";

type LoadState = { kind: "loading" } | { kind: "ready" } | { kind: "error"; message: string };

/** The portfolio screen for US-1: lists holdings and lets the user add one. */
export function PortfolioView() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [load, setLoad] = useState<LoadState>({ kind: "loading" });

  // Re-fetch the list (used after a successful add).
  const refresh = useCallback(async () => {
    try {
      setHoldings(await getHoldings());
      setLoad({ kind: "ready" });
    } catch (err) {
      setLoad({ kind: "error", message: toErrorMessage(err) });
    }
  }, []);

  // Initial load. State is set only inside the async callbacks, never synchronously.
  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const data = await getHoldings();
        if (active) {
          setHoldings(data);
          setLoad({ kind: "ready" });
        }
      } catch (err) {
        if (active) setLoad({ kind: "error", message: toErrorMessage(err) });
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <div className="flex items-baseline justify-between gap-3">
            <CardTitle>Holdings</CardTitle>
            <span className="font-mono text-xs text-faint">
              {holdings.length} {holdings.length === 1 ? "position" : "positions"}
            </span>
          </div>
          <CardDescription>Your portfolio positions.</CardDescription>
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
          {load.kind === "ready" && <HoldingsTable holdings={holdings} />}
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
