import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AxiosError } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";

import { AddHoldingForm } from "./AddHoldingForm";

describe("AddHoldingForm", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  function fill(ticker: string, shares: string) {
    fireEvent.change(screen.getByLabelText(/ticker/i), { target: { value: ticker } });
    fireEvent.change(screen.getByLabelText(/shares/i), { target: { value: shares } });
  }

  it("submits the ticker and quantity and reports the new holding", async () => {
    const holding = { id: 1, ticker: "AAPL", quantity: "10.000000" };
    const addHolding = vi.spyOn(client, "addHolding").mockResolvedValue(holding);
    const onAdded = vi.fn();

    render(<AddHoldingForm onAdded={onAdded} />);
    fill("AAPL", "10");
    fireEvent.click(screen.getByRole("button", { name: /add holding/i }));

    await waitFor(() => expect(onAdded).toHaveBeenCalledWith(holding));
    expect(addHolding).toHaveBeenCalledWith("AAPL", "10");
    // inputs cleared after a successful add
    expect((screen.getByLabelText(/ticker/i) as HTMLInputElement).value).toBe("");
  });

  it("shows a clear error and adds nothing when the backend rejects the ticker", async () => {
    const error = new AxiosError("Request failed");
    error.response = {
      data: { detail: "Unrecognized ticker 'ZZZZ'. Check the symbol and try again." },
      status: 422,
      statusText: "Unprocessable Content",
      headers: {},
      config: { headers: {} } as never,
    };
    vi.spyOn(client, "addHolding").mockRejectedValue(error);
    const onAdded = vi.fn();

    render(<AddHoldingForm onAdded={onAdded} />);
    fill("ZZZZ", "5");
    fireEvent.click(screen.getByRole("button", { name: /add holding/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/unrecognized ticker/i);
    expect(onAdded).not.toHaveBeenCalled();
  });
});
