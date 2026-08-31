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

  it("renders the brand heading and an empty state", async () => {
    vi.spyOn(client, "getPortfolioSummary").mockResolvedValue({
      positions: [],
      total_value: null,
      priced: false,
    });
    render(<App />);
    expect(screen.getByRole("heading", { level: 1, name: APP_NAME })).toBeInTheDocument();
    expect(await screen.findByText(/no holdings yet/i)).toBeInTheDocument();
  });

  it("lists positions with prices, values, and a total (US-4)", async () => {
    vi.spyOn(client, "getPortfolioSummary").mockResolvedValue({
      positions: [
        {
          id: 1,
          ticker: "AAPL",
          quantity: "10.000000",
          latest_price: "319.70",
          market_value: "3197.00",
          weight_pct: "60.00",
          price_as_of: "2026-08-28",
        },
        {
          id: 2,
          ticker: "NVDA",
          quantity: "2.500000",
          latest_price: "850.00",
          market_value: "2125.00",
          weight_pct: "40.00",
          price_as_of: "2026-08-28",
        },
      ],
      total_value: "5322.00",
      priced: true,
    });

    render(<App />);

    expect(await screen.findByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText("$319.70")).toBeInTheDocument();
    expect(screen.getByText("$3,197.00")).toBeInTheDocument();
    expect(screen.getByText("60.0%")).toBeInTheDocument();
    // portfolio total
    expect(screen.getByText("$5,322.00")).toBeInTheDocument();
  });

  it("shows a dash when a position could not be priced", async () => {
    vi.spyOn(client, "getPortfolioSummary").mockResolvedValue({
      positions: [
        {
          id: 1,
          ticker: "AAPL",
          quantity: "10.000000",
          latest_price: null,
          market_value: null,
          weight_pct: null,
          price_as_of: null,
        },
      ],
      total_value: null,
      priced: false,
    });

    render(<App />);

    expect(await screen.findByText("AAPL")).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });
});
