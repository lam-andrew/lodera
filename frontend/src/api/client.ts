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

// withCredentials is required for the session cookie to travel: the frontend and API are
// different origins in development, and cookies are not sent cross-origin without it.
export const api = axios.create({ baseURL, withCredentials: true });

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

/** A CSV row that could not be imported (US-2, FR-3). */
export interface ImportProblem {
  row: number;
  reason: string;
  content: string;
}

export interface ImportResult {
  added: string[];
  updated: string[];
  problems: ImportProblem[];
  skipped: number;
  ticker_column: string | null;
  quantity_column: string | null;
}

/** Upload a CSV / brokerage positions export. */
export async function importHoldings(file: File): Promise<ImportResult> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<ImportResult>("/holdings/import", form);
  return data;
}

/** Two holdings and how closely they move together (US-6). */
export interface CorrelationPair {
  a: string;
  b: string;
  correlation: string;
}

export interface PortfolioCorrelation {
  tickers: string[];
  /** matrix[i][j] = correlation between tickers[i] and tickers[j]; null when undefined. */
  matrix: (string | null)[][];
  most_correlated: CorrelationPair[];
  least_correlated: CorrelationPair[];
  average_correlation: string | null;
  window_days: number;
  observations: number;
  high_threshold: string;
  low_threshold: string;
}

/** Correlation structure among the portfolio's holdings. */
export async function getPortfolioCorrelation(): Promise<PortfolioCorrelation> {
  const { data } = await api.get<PortfolioCorrelation>("/portfolio/correlation");
  return data;
}

/** One point on the portfolio value series (US-10). */
export interface ValuePoint {
  date: string;
  value: string;
}

export interface PortfolioHistory {
  points: ValuePoint[];
  start: string | null;
  end: string | null;
}

/** Portfolio market value over time, at today's share quantities. */
export async function getPortfolioHistory(): Promise<PortfolioHistory> {
  const { data } = await api.get<PortfolioHistory>("/portfolio/history");
  return data;
}

/** A position larger than its equal-weight share (US-7). */
export interface OverweightPosition {
  ticker: string;
  weight_pct: string;
  times_equal_weight: string;
}

/** Holdings that move together closely enough to act as one position (US-7). */
export interface OverlapGroup {
  tickers: string[];
  combined_weight_pct: string;
  min_correlation: string;
}

export interface PortfolioConcentration {
  hhi: string | null;
  effective_holdings: string | null;
  holdings_count: number;
  top_1_pct: string | null;
  top_3_pct: string | null;
  top_5_pct: string | null;
  overweight: OverweightPosition[];
  overlaps: OverlapGroup[];
  overweight_multiple: string;
  overlap_threshold: string;
}

/** Where the portfolio is overexposed. */
export async function getPortfolioConcentration(): Promise<PortfolioConcentration> {
  const { data } = await api.get<PortfolioConcentration>("/portfolio/concentration");
  return data;
}

/** One peak-to-trough decline (US-8). */
export interface DrawdownEpisode {
  depth_pct: string;
  peak_date: string;
  trough_date: string;
  recovery_date: string | null;
  decline_days: number;
  recovery_days: number | null;
  recovered: boolean;
}

export interface DrawdownPoint {
  date: string;
  drawdown_pct: string;
}

export interface PortfolioDrawdown {
  max_drawdown_pct: string | null;
  current_drawdown_pct: string | null;
  episodes: DrawdownEpisode[];
  series: DrawdownPoint[];
  window_days: number;
  observations: number;
}

/** The portfolio's worst historical declines. */
export async function getPortfolioDrawdown(): Promise<PortfolioDrawdown> {
  const { data } = await api.get<PortfolioDrawdown>("/portfolio/drawdown");
  return data;
}

/** The signed-in account (US-13). Never carries a password or hash. */
export interface User {
  id: number;
  email: string;
}

/** Whoever is signed in, or null when there is no valid session. */
export async function getCurrentUser(): Promise<User | null> {
  try {
    const { data } = await api.get<User>("/auth/me");
    return data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 401) return null;
    throw error;
  }
}

export async function register(email: string, password: string): Promise<User> {
  const { data } = await api.post<User>("/auth/register", { email, password });
  return data;
}

export async function login(email: string, password: string): Promise<User> {
  const { data } = await api.post<User>("/auth/login", { email, password });
  return data;
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}
