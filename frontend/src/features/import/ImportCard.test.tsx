import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";

import { ImportCard } from "./ImportCard";

function selectFile(contents = "Symbol,Quantity\nAAPL,10\n") {
  const file = new File([contents], "positions.csv", { type: "text/csv" });
  const input = screen.getByLabelText(/portfolio csv file/i);
  fireEvent.change(input, { target: { files: [file] } });
  return file;
}

describe("ImportCard (US-2)", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("uploads the file and reports what was imported", async () => {
    const importHoldings = vi.spyOn(client, "importHoldings").mockResolvedValue({
      added: ["AAPL", "MSFT"],
      updated: [],
      problems: [],
      skipped: 2,
      ticker_column: "Symbol",
      quantity_column: "Quantity",
    });
    const onImported = vi.fn();

    render(<ImportCard onImported={onImported} />);
    selectFile();

    await waitFor(() => expect(importHoldings).toHaveBeenCalled());
    expect(await screen.findByText(/imported 2 positions/i)).toBeInTheDocument();
    expect(screen.getByText(/2 rows ignored/i)).toBeInTheDocument();
    expect(onImported).toHaveBeenCalled();
  });

  it("lists every row that could not be imported, with its line number", async () => {
    vi.spyOn(client, "importHoldings").mockResolvedValue({
      added: ["AAPL"],
      updated: [],
      problems: [
        { row: 3, reason: "'NOT A TICKER' is not a valid ticker symbol.", content: "NOT A TICKER" },
        { row: 5, reason: "Could not read a share quantity from 'abc'.", content: "abc" },
      ],
      skipped: 0,
      ticker_column: "Symbol",
      quantity_column: "Quantity",
    });

    render(<ImportCard onImported={vi.fn()} />);
    selectFile();

    expect(await screen.findByText(/2 rows could not be imported/i)).toBeInTheDocument();
    expect(screen.getByText(/line 3/i)).toBeInTheDocument();
    expect(screen.getByText(/not a valid ticker symbol/i)).toBeInTheDocument();
    expect(screen.getByText(/line 5/i)).toBeInTheDocument();
    // the good row still imported
    expect(screen.getByText(/imported 1 position/i)).toBeInTheDocument();
  });

  it("shows which columns the parser matched", async () => {
    vi.spyOn(client, "importHoldings").mockResolvedValue({
      added: ["VTI"],
      updated: [],
      problems: [],
      skipped: 0,
      ticker_column: "Symbol",
      quantity_column: "Shares",
    });

    render(<ImportCard onImported={vi.fn()} />);
    selectFile();

    expect(await screen.findByText(/read .Symbol. as the ticker/i)).toBeInTheDocument();
  });

  it("surfaces an upload failure", async () => {
    vi.spyOn(client, "importHoldings").mockRejectedValue(new Error("boom"));
    render(<ImportCard onImported={vi.fn()} />);
    selectFile();
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
