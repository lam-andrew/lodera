import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { APP_NAME } from "@/config/branding";

import App from "./App";

const okHealth = {
  status: "ok" as const,
  service: "Orbit API",
  version: "0.1.0",
  environment: "test",
  database: "connected" as const,
  market_data: "configured" as const,
};

describe("App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(client, "getHealth").mockResolvedValue(okHealth);
  });

  it("renders the brand heading", async () => {
    vi.spyOn(client, "getHoldings").mockResolvedValue([]);
    render(<App />);
    expect(screen.getByRole("heading", { level: 1, name: APP_NAME })).toBeInTheDocument();
    expect(await screen.findByText(/no holdings yet/i)).toBeInTheDocument();
  });

  it("lists holdings returned by the API", async () => {
    vi.spyOn(client, "getHoldings").mockResolvedValue([
      { id: 1, ticker: "AAPL", quantity: "10.000000" },
      { id: 2, ticker: "NVDA", quantity: "2.500000" },
    ]);
    render(<App />);
    expect(await screen.findByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText("2.5")).toBeInTheDocument();
  });
});
