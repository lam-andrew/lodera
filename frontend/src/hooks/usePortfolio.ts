import { useCallback, useEffect, useState } from "react";

import {
  getPortfolioConcentration,
  getPortfolioCorrelation,
  getPortfolioDrawdown,
  getPortfolioHistory,
  getPortfolioRisk,
  getPortfolioSummary,
  toErrorMessage,
  type HoldingRisk,
  type PortfolioConcentration,
  type PortfolioCorrelation,
  type PortfolioDrawdown,
  type PortfolioHistory,
  type PortfolioRisk,
  type PortfolioSummary,
} from "@/api/client";

export interface PortfolioData {
  summary: PortfolioSummary;
  risk: PortfolioRisk | null;
  correlation: PortfolioCorrelation | null;
  history: PortfolioHistory | null;
  concentration: PortfolioConcentration | null;
  drawdown: PortfolioDrawdown | null;
}

export type PortfolioState =
  { kind: "loading" } | { kind: "ready"; data: PortfolioData } | { kind: "error"; message: string };

/** Load holdings, prices, risk, correlation and value history together.
 *
 *  Only the summary is required: the analytical calls are allowed to fail individually so a
 *  hiccup in one metric never hides the portfolio the user came to see. */
async function loadAll(): Promise<PortfolioData> {
  const [summary, risk, correlation, history, concentration, drawdown] = await Promise.all([
    getPortfolioSummary(),
    getPortfolioRisk().catch(() => null),
    getPortfolioCorrelation().catch(() => null),
    getPortfolioHistory().catch(() => null),
    getPortfolioConcentration().catch(() => null),
    getPortfolioDrawdown().catch(() => null),
  ]);
  return { summary, risk, correlation, history, concentration, drawdown };
}

/** Shared portfolio data for every page, with a refresh callback for mutations. */
export function usePortfolio(): { state: PortfolioState; refresh: () => void } {
  const [state, setState] = useState<PortfolioState>({ kind: "loading" });

  const refresh = useCallback(() => {
    void (async () => {
      try {
        setState({ kind: "ready", data: await loadAll() });
      } catch (err) {
        setState({ kind: "error", message: toErrorMessage(err) });
      }
    })();
  }, []);

  // Initial load. State is set only inside the async callback, never synchronously.
  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const data = await loadAll();
        if (active) setState({ kind: "ready", data });
      } catch (err) {
        if (active) setState({ kind: "error", message: toErrorMessage(err) });
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  return { state, refresh };
}

/** Index per-holding risk by ticker for row lookups. */
export function riskByTicker(risk: PortfolioRisk | null): Record<string, HoldingRisk> {
  if (risk === null) return {};
  return Object.fromEntries(risk.holdings.map((h) => [h.ticker, h]));
}
