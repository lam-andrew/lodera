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
