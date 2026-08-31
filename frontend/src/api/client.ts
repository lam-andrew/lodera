/**
 * Backend API client.
 *
 * The frontend talks to the backend ONLY through this typed client, which targets the
 * backend's public API contract (never engine internals). The base URL comes from the
 * `VITE_API_BASE_URL` environment variable so the same build works in dev, Docker, and
 * production.
 */
import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const api = axios.create({ baseURL });

/**
 * Turn an API failure into a single human-readable message. The backend returns either a
 * string `detail` (our HTTPExceptions, e.g. unrecognized/duplicate ticker) or FastAPI's
 * validation array (bad quantity/format); both are flattened to one clear sentence.
 */
export function toErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      const field = Array.isArray(first?.loc) ? first.loc[first.loc.length - 1] : undefined;
      const msg = typeof first?.msg === "string" ? first.msg : "Invalid input";
      return field ? `${String(field)}: ${msg}` : msg;
    }
    if (!error.response) return "Cannot reach the backend. Is it running?";
  }
  return "Something went wrong. Please try again.";
}

/** Shape of `GET /health` — mirrors the backend `HealthResponse` schema. */
export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
  environment: string;
  database: "connected" | "unavailable";
  /** Whether a market-data API key is configured (US-4). */
  market_data: "configured" | "unconfigured";
}

/** Fetch backend liveness + database status. */
export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

/** A stored holding — mirrors the backend `HoldingRead` schema (quantity is a decimal string). */
export interface Holding {
  id: number;
  ticker: string;
  quantity: string;
}

/** List the holdings in the portfolio. */
export async function getHoldings(): Promise<Holding[]> {
  const { data } = await api.get<Holding[]>("/holdings");
  return data;
}

/** Add a holding by ticker and share quantity. Throws on validation/duplicate errors. */
export async function addHolding(ticker: string, quantity: string): Promise<Holding> {
  const { data } = await api.post<Holding>("/holdings", { ticker, quantity });
  return data;
}

/** A holding enriched with market data (US-4). Price fields are null when unavailable. */
export interface Position {
  id: number;
  ticker: string;
  quantity: string;
  latest_price: string | null;
  market_value: string | null;
  weight_pct: string | null;
  price_as_of: string | null;
}

export interface PortfolioSummary {
  positions: Position[];
  total_value: string | null;
  priced: boolean;
}

/** Holdings joined with latest prices and market values. */
export async function getPortfolioSummary(): Promise<PortfolioSummary> {
  const { data } = await api.get<PortfolioSummary>("/portfolio/summary");
  return data;
}

/** Update a holding's share quantity. Throws if the quantity is invalid or it's gone. */
export async function updateHolding(id: number, quantity: string): Promise<Holding> {
  const { data } = await api.patch<Holding>(`/holdings/${id}`, { quantity });
  return data;
}

/** Remove a holding from the portfolio. */
export async function deleteHolding(id: number): Promise<void> {
  await api.delete(`/holdings/${id}`);
}

/** Risk figures for one holding (US-5). Percentages come as decimal strings ("18.70"). */
export interface HoldingRisk {
  id: number;
  ticker: string;
  volatility_pct: string | null;
  band: "low" | "moderate" | "high" | null;
  observations: number;
}

export interface PortfolioRisk {
  holdings: HoldingRisk[];
  portfolio_volatility_pct: string | null;
  portfolio_band: "low" | "moderate" | "high" | null;
  undiversified_volatility_pct: string | null;
  diversification_benefit_pct: string | null;
  window_days: number;
  observations: number;
}

/** Volatility for each holding and for the portfolio. */
export async function getPortfolioRisk(): Promise<PortfolioRisk> {
  const { data } = await api.get<PortfolioRisk>("/portfolio/risk");
  return data;
}
