import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";
import { APP_NAME } from "@/config/branding";

import App from "./App";

const health = {
  status: "ok" as const,
  service: "Orbit API",
  version: "0.1.0",
  environment: "test",
  database: "connected" as const,
  market_data: "configured" as const,
};

const positions = [
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
    ticker: "BND",
    quantity: "30.000000",
    latest_price: "72.31",
    market_value: "2169.30",
    weight_pct: "40.00",
    price_as_of: "2026-08-28",
  },
];

const risk = {
  holdings: [
    { id: 1, ticker: "AAPL", volatility_pct: "25.16", band: "high" as const, observations: 249 },
    { id: 2, ticker: "BND", volatility_pct: "3.69", band: "low" as const, observations: 249 },
  ],
  portfolio_volatility_pct: "17.94",
  portfolio_band: "moderate" as const,
  undiversified_volatility_pct: "20.91",
  diversification_benefit_pct: "2.97",
  window_days: 365,
  observations: 249,
};

const correlation = {
  tickers: ["AAPL", "BND"],
  matrix: [
    ["1.00", "0.14"],
    ["0.14", "1.00"],
  ],
  most_correlated: [{ a: "AAPL", b: "BND", correlation: "0.14" }],
  least_correlated: [{ a: "AAPL", b: "BND", correlation: "0.14" }],
  average_correlation: "0.14",
  window_days: 365,
  observations: 249,
  high_threshold: "0.75",
  low_threshold: "0.30",
};

const history = {
  points: [
    { date: "2026-08-24", value: "5100.00" },
    { date: "2026-08-25", value: "5200.00" },
    { date: "2026-08-28", value: "5366.30" },
  ],
  start: "2026-08-24",
  end: "2026-08-28",
};

const concentration = {
  hhi: "0.35",
  effective_holdings: "2.88",
  holdings_count: 2,
  top_1_pct: "60.00",
  top_3_pct: "100.00",
  top_5_pct: "100.00",
  overweight: [{ ticker: "AAPL", weight_pct: "60.00", times_equal_weight: "1.20" }],
  overlaps: [{ tickers: ["QQQ", "VOO"], combined_weight_pct: "25.15", min_correlation: "0.92" }],
  overweight_multiple: "2",
  overlap_threshold: "0.75",
};

const drawdown = {
  max_drawdown_pct: "-24.43",
  current_drawdown_pct: "-14.90",
  episodes: [
    {
      depth_pct: "-24.43",
      peak_date: "2025-12-22",
      trough_date: "2026-07-29",
      recovery_date: null,
      decline_days: 149,
      recovery_days: null,
      recovered: false,
    },
    {
      depth_pct: "-12.33",
      peak_date: "2025-11-03",
      trough_date: "2025-11-21",
      recovery_date: "2025-12-15",
      decline_days: 14,
      recovery_days: 15,
      recovered: true,
    },
  ],
  series: [
    { date: "2026-08-24", drawdown_pct: "0.00" },
    { date: "2026-08-25", drawdown_pct: "-5.00" },
    { date: "2026-08-28", drawdown_pct: "-14.90" },
  ],
  window_days: 365,
  observations: 249,
};

function mockAll(overrides: { positions?: typeof positions } = {}) {
  vi.spyOn(client, "getHealth").mockResolvedValue(health);
  vi.spyOn(client, "getPortfolioSummary").mockResolvedValue({
    positions: overrides.positions ?? positions,
    total_value: "5366.30",
    priced: true,
  });
  vi.spyOn(client, "getPortfolioRisk").mockResolvedValue(risk);
  vi.spyOn(client, "getPortfolioCorrelation").mockResolvedValue(correlation);
  vi.spyOn(client, "getPortfolioHistory").mockResolvedValue(history);
  vi.spyOn(client, "getPortfolioConcentration").mockResolvedValue(concentration);
  vi.spyOn(client, "getPortfolioDrawdown").mockResolvedValue(drawdown);
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("Dashboard (US-10)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockAll();
  });

  it("shows the brand and the risk overview heading", async () => {
    renderAt("/");
    expect(await screen.findByRole("heading", { name: /risk overview/i })).toBeInTheDocument();
    expect(screen.getAllByText(APP_NAME).length).toBeGreaterThan(0);
  });

  it("presents summary tiles before the detail", async () => {
    renderAt("/");

    expect(await screen.findByText("Portfolio value")).toBeInTheDocument();
    // The total appears in the tile and again in the table footer.
    expect(screen.getAllByText("$5,366.30").length).toBeGreaterThan(0);

    // "Volatility" is both a tile label and a table column header.
    expect(screen.getAllByText("Volatility").length).toBeGreaterThan(0);
    expect(screen.getByText("17.9%")).toBeInTheDocument();
    expect(screen.getByText("Moderate")).toBeInTheDocument();

    expect(screen.getByText("Average correlation")).toBeInTheDocument();
    expect(screen.getByText("Effective holdings")).toBeInTheDocument();
    // 2.88 effective appears in the tile and in the concentration card below.
    expect(screen.getAllByText("2.9").length).toBeGreaterThan(0);
    // "Worst decline" labels both the tile and the drawdown card.
    expect(screen.getAllByText("Worst decline").length).toBeGreaterThan(0);
  });

  it("renders a value sparkline as a labelled image", async () => {
    renderAt("/");
    expect(
      await screen.findByRole("img", { name: /portfolio value over time/i }),
    ).toBeInTheDocument();
  });

  it("shows holdings and the correlation matrix on the overview", async () => {
    renderAt("/");
    await screen.findByText("Portfolio value");

    const table = screen.getAllByRole("table")[0];
    expect(within(table).getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText(/how your holdings move relative/i)).toBeInTheDocument();
  });

  it("prompts to add holdings when the portfolio is empty", async () => {
    vi.restoreAllMocks();
    mockAll({ positions: [] });
    renderAt("/");
    expect(await screen.findByText(/no holdings yet/i)).toBeInTheDocument();
  });
});

describe("Navigation (US-10)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockAll();
  });

  it("routes to the holdings page with the editing tools", async () => {
    renderAt("/holdings");
    // Await content that only exists once data has loaded — the shell heading renders
    // immediately from the page title, so awaiting it would race the data.
    expect(await screen.findByText(/add a holding/i)).toBeInTheDocument();
    expect(screen.getByText(/import from a csv/i)).toBeInTheDocument();
    // Two "Holdings" headings exist: the shell title (h1) and the card title (h2).
    expect(screen.getByRole("heading", { level: 1, name: /^holdings$/i })).toBeInTheDocument();
  });

  it("routes to the correlation page", async () => {
    renderAt("/correlation");
    expect(await screen.findByText(/how your holdings move relative/i)).toBeInTheDocument();
  });

  it("navigates from the sidebar", async () => {
    renderAt("/");
    await screen.findByText("Portfolio value");

    fireEvent.click(screen.getByRole("link", { name: /holdings/i }));

    await waitFor(() => expect(screen.getByText(/import from a csv/i)).toBeInTheDocument());
  });

  it("shows a not-found page for an unknown route", async () => {
    renderAt("/nope");
    expect(await screen.findByText(/doesn't exist/i)).toBeInTheDocument();
  });

  it("links concentration and drawdown now that they are built", async () => {
    renderAt("/");
    expect(screen.getByRole("link", { name: /concentration/i })).toHaveAttribute(
      "href",
      "/concentration",
    );
    expect(screen.getByRole("link", { name: /drawdown/i })).toHaveAttribute("href", "/drawdown");
    // Still-unbuilt sections keep their SOON marker.
    expect(screen.getAllByText("SOON").length).toBeGreaterThan(0);
  });

  it("routes to concentration and drawdown", async () => {
    renderAt("/concentration");
    expect(await screen.findByText(/effective holdings, from/i)).toBeInTheDocument();
  });

  it("shows drawdown episodes including one that never recovered", async () => {
    renderAt("/drawdown");
    expect(await screen.findByText(/largest declines/i)).toBeInTheDocument();
    expect(screen.getByText(/not recovered/i)).toBeInTheDocument();
    expect(screen.getAllByText("-24.4%").length).toBeGreaterThan(0);
  });
});

describe("Load states", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("surfaces an error when the portfolio cannot be loaded", async () => {
    vi.spyOn(client, "getHealth").mockResolvedValue(health);
    vi.spyOn(client, "getPortfolioSummary").mockRejectedValue(new Error("down"));
    vi.spyOn(client, "getPortfolioRisk").mockResolvedValue(risk);
    vi.spyOn(client, "getPortfolioCorrelation").mockResolvedValue(correlation);
    vi.spyOn(client, "getPortfolioHistory").mockResolvedValue(history);
    vi.spyOn(client, "getPortfolioConcentration").mockResolvedValue(concentration);
    vi.spyOn(client, "getPortfolioDrawdown").mockResolvedValue(drawdown);

    renderAt("/");
    expect(await screen.findByText(/could not load your portfolio/i)).toBeInTheDocument();
  });

  it("still renders holdings when only the analytics calls fail", async () => {
    vi.spyOn(client, "getHealth").mockResolvedValue(health);
    vi.spyOn(client, "getPortfolioSummary").mockResolvedValue({
      positions,
      total_value: "5366.30",
      priced: true,
    });
    vi.spyOn(client, "getPortfolioRisk").mockRejectedValue(new Error("risk down"));
    vi.spyOn(client, "getPortfolioCorrelation").mockRejectedValue(new Error("corr down"));
    vi.spyOn(client, "getPortfolioHistory").mockRejectedValue(new Error("hist down"));
    vi.spyOn(client, "getPortfolioConcentration").mockRejectedValue(new Error("conc down"));
    vi.spyOn(client, "getPortfolioDrawdown").mockRejectedValue(new Error("dd down"));

    renderAt("/");
    expect((await screen.findAllByText("$5,366.30")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("AAPL").length).toBeGreaterThan(0);
  });
});
