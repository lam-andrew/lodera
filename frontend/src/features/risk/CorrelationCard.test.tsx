import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { PortfolioCorrelation } from "@/api/client";

import { CorrelationCard } from "./CorrelationCard";

const base: PortfolioCorrelation = {
  tickers: ["AAPL", "MSFT", "BND"],
  matrix: [
    ["1.00", "0.82", "-0.15"],
    ["0.82", "1.00", "-0.10"],
    ["-0.15", "-0.10", "1.00"],
  ],
  most_correlated: [{ a: "AAPL", b: "MSFT", correlation: "0.82" }],
  least_correlated: [{ a: "AAPL", b: "BND", correlation: "-0.15" }],
  average_correlation: "0.19",
  window_days: 365,
  observations: 249,
  high_threshold: "0.75",
  low_threshold: "0.30",
};

describe("CorrelationCard (US-6)", () => {
  it("renders the full matrix with headers", () => {
    render(<CorrelationCard correlation={base} />);

    const table = screen.getByRole("table");
    // Row and column header for each ticker.
    for (const ticker of base.tickers) {
      expect(within(table).getAllByText(ticker).length).toBeGreaterThanOrEqual(2);
    }
    // 3x3 grid of value cells.
    expect(within(table).getAllByText("1.00")).toHaveLength(3);
    expect(within(table).getAllByText("0.82")).toHaveLength(2); // symmetric
    expect(within(table).getAllByText("-0.15")).toHaveLength(2);
  });

  it("surfaces the most and least correlated pairs", () => {
    render(<CorrelationCard correlation={base} />);
    expect(screen.getByText(/AAPL \/ MSFT · 0\.82/)).toBeInTheDocument();
    expect(screen.getByText(/AAPL \/ BND · -0\.15/)).toBeInTheDocument();
    expect(screen.getByText("0.19")).toBeInTheDocument();
  });

  it("flags a pair above the high threshold as behaving like one position", () => {
    render(<CorrelationCard correlation={base} />);
    expect(screen.getByText(/behaves like one position/i)).toBeInTheDocument();
  });

  it("does not flag pairs below the threshold", () => {
    render(
      <CorrelationCard
        correlation={{
          ...base,
          most_correlated: [{ a: "AAPL", b: "BND", correlation: "0.20" }],
        }}
      />,
    );
    expect(screen.queryByText(/behaves like one position/i)).not.toBeInTheDocument();
  });

  it("renders undefined cells as a dash rather than zero", () => {
    render(
      <CorrelationCard
        correlation={{
          ...base,
          tickers: ["AAPL", "FLAT"],
          matrix: [
            ["1.00", null],
            [null, "1.00"],
          ],
          most_correlated: [],
          least_correlated: [],
        }}
      />,
    );
    expect(screen.getAllByText("—").length).toBe(2);
  });

  it("prompts for more holdings when there are fewer than two", () => {
    render(
      <CorrelationCard
        correlation={{
          ...base,
          tickers: [],
          matrix: [],
          most_correlated: [],
          least_correlated: [],
        }}
      />,
    );
    expect(screen.getByText(/at least two holdings/i)).toBeInTheDocument();
  });
});
