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
