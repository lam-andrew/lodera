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

const emptyRisk = {
  holdings: [],
  portfolio_volatility_pct: null,
  portfolio_band: null,
  undiversified_volatility_pct: null,
  diversification_benefit_pct: null,
  window_days: 365,
  observations: 0,
};

describe("App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(client, "getHealth").mockResolvedValue(okHealth);
    vi.spyOn(client, "getPortfolioRisk").mockResolvedValue(emptyRisk);
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

describe("Volatility (US-5)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(client, "getHealth").mockResolvedValue(okHealth);
    vi.spyOn(client, "getPortfolioSummary").mockResolvedValue({
      positions: [
        {
          id: 1,
          ticker: "AAPL",
          quantity: "10.000000",
          latest_price: "319.70",
          market_value: "3197.00",
          weight_pct: "100.00",
          price_as_of: "2026-08-28",
        },
      ],
      total_value: "3197.00",
      priced: true,
    });
  });

  it("shows volatility for the holding and for the portfolio", async () => {
    vi.spyOn(client, "getPortfolioRisk").mockResolvedValue({
      holdings: [
        { id: 1, ticker: "AAPL", volatility_pct: "25.16", band: "high", observations: 249 },
      ],
      portfolio_volatility_pct: "17.94",
      portfolio_band: "moderate",
      undiversified_volatility_pct: "20.91",
      diversification_benefit_pct: "2.97",
      window_days: 365,
      observations: 249,
    });

    render(<App />);

    // portfolio figure + band
    expect(await screen.findByText("17.9%")).toBeInTheDocument();
    expect(screen.getByText("Moderate")).toBeInTheDocument();
    // per-holding figure + band
    expect(screen.getByText("25.2%")).toBeInTheDocument();
    expect(screen.getByText("Elevated")).toBeInTheDocument();
    // diversification comparison
    expect(screen.getByText("20.9%")).toBeInTheDocument();
    expect(screen.getByText("−3.0%")).toBeInTheDocument();
  });

  it("still shows holdings when the risk call fails", async () => {
    vi.spyOn(client, "getPortfolioRisk").mockRejectedValue(new Error("risk down"));
    render(<App />);
    expect(await screen.findByText("AAPL")).toBeInTheDocument();
    // (the single position's value also appears as the portfolio total)
    expect(screen.getAllByText("$3,197.00").length).toBeGreaterThan(0);
  });
});
