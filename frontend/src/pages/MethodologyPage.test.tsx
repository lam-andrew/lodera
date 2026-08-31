import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import type { PortfolioData } from "@/hooks/usePortfolio";

import { MethodologyPage } from "./MethodologyPage";

const full: PortfolioData = {
  summary: { positions: [], total_value: "5000.00", priced: true },
  risk: {
    holdings: [],
    portfolio_volatility_pct: "30.20",
    portfolio_band: "high",
    undiversified_volatility_pct: "34.89",
    diversification_benefit_pct: "4.70",
    window_days: 365,
    observations: 249,
  },
  correlation: {
    tickers: ["VOO", "VTI"],
    matrix: [
      ["1.00", "1.00"],
      ["1.00", "1.00"],
    ],
    most_correlated: [{ a: "VOO", b: "VTI", correlation: "1.00" }],
    least_correlated: [],
    average_correlation: "0.35",
    window_days: 365,
    observations: 249,
    high_threshold: "0.75",
    low_threshold: "0.30",
  },
  history: null,
  concentration: {
    hhi: "0.35",
    effective_holdings: "2.88",
    holdings_count: 11,
    top_1_pct: "55.93",
    top_3_pct: "76.55",
    top_5_pct: "89.95",
    overweight: [],
    overlaps: [],
    overweight_multiple: "2",
    overlap_threshold: "0.75",
  },
  drawdown: {
    max_drawdown_pct: "-24.43",
    current_drawdown_pct: "-14.90",
    episodes: [],
    series: [],
    window_days: 365,
    observations: 249,
  },
};

const empty: PortfolioData = {
  summary: { positions: [], total_value: null, priced: false },
  risk: null,
  correlation: null,
  history: null,
  concentration: null,
  drawdown: null,
};

function renderPage(data: PortfolioData) {
  return render(
    <MemoryRouter>
      <MethodologyPage data={data} />
    </MemoryRouter>,
  );
}

describe("MethodologyPage (US-19)", () => {
  it("explains every metric with its formula", () => {
    renderPage(full);

    // Level 2 = section headings. Some titles ("Drawdown") also appear as h3 in the
    // limitations list, so the level keeps the query unambiguous.
    for (const heading of [
      /the price series/i,
      /from prices to returns/i,
      /volatility of one holding/i,
      /volatility of the whole portfolio/i,
      /correlation between holdings/i,
      /concentration and overlap/i,
      /^drawdown$/i,
      /what to scrutinize/i,
    ]) {
      expect(screen.getByRole("heading", { level: 2, name: heading })).toBeInTheDocument();
    }

    expect(screen.getByText(/r\(t\) = P\(t\) \/ P\(t−1\) − 1/)).toBeInTheDocument();
    expect(screen.getByText(/σₚ = √\( wᵀ Σ w \) × √252/)).toBeInTheDocument();
    expect(screen.getByText(/ρ\(i,j\) = Cov\(i,j\) \/ \( σᵢ × σⱼ \)/)).toBeInTheDocument();
    expect(screen.getByText(/HHI = Σ wᵢ²/)).toBeInTheDocument();
    expect(
      screen.getByText(/drawdown\(t\) = value\(t\) \/ running_peak\(t\) − 1/),
    ).toBeInTheDocument();
  });

  it("uses the reader's own figures as the worked examples", () => {
    renderPage(full);

    expect(screen.getByText("34.9%")).toBeInTheDocument(); // undiversified
    expect(screen.getByText("30.2%")).toBeInTheDocument(); // actual
    expect(screen.getByText("2.88")).toBeInTheDocument(); // effective holdings
    expect(screen.getByText("11")).toBeInTheDocument(); // holdings count
    expect(screen.getByText("-24.4%")).toBeInTheDocument(); // worst decline
    expect(screen.getByText("249")).toBeInTheDocument(); // observations
    expect(screen.getByText("VOO / VTI")).toBeInTheDocument();
  });

  it("still explains the method when there is no portfolio yet", () => {
    renderPage(empty);

    expect(
      screen.getByRole("heading", { name: /correlation between holdings/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/HHI = Σ wᵢ²/)).toBeInTheDocument();
    // No fabricated figures.
    expect(screen.queryByText("2.88")).not.toBeInTheDocument();
  });

  it("states the limitations rather than omitting them", () => {
    renderPage(full);

    const section = screen
      .getByRole("heading", { level: 2, name: /what to scrutinize/i })
      .closest("section");
    expect(section).not.toBeNull();
    const scoped = within(section as HTMLElement);

    expect(scoped.getByText(/correlations rise in crises/i)).toBeInTheDocument();
    expect(scoped.getByText(/no concept of sector/i)).toBeInTheDocument();
    expect(scoped.getByText(/backtest of today's holdings/i)).toBeInTheDocument();
    expect(scoped.getByText(/stress testing/i)).toBeInTheDocument();
    expect(
      scoped.getByText(/not investment advice|nothing it reports is investment advice/i),
    ).toBeInTheDocument();
  });

  it("offers in-page navigation to each section", () => {
    renderPage(full);
    const contents = screen.getByRole("navigation", { name: /contents/i });
    expect(within(contents).getByRole("link", { name: /drawdown/i })).toHaveAttribute(
      "href",
      "#drawdown",
    );
  });
});
