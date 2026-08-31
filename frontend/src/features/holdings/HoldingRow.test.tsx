import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AxiosError } from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as client from "@/api/client";

import { HoldingRow } from "./HoldingRow";

const position = {
  id: 7,
  ticker: "AAPL",
  quantity: "10.000000",
  latest_price: "150.00",
  market_value: "1500.00",
  weight_pct: "100.00",
  price_as_of: "2026-08-28",
};

function renderRow(onChanged = vi.fn()) {
  render(
    <table>
      <tbody>
        <HoldingRow position={position} onChanged={onChanged} />
      </tbody>
    </table>,
  );
  return onChanged;
}

describe("HoldingRow (US-3)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("saves an edited quantity", async () => {
    const update = vi
      .spyOn(client, "updateHolding")
      .mockResolvedValue({ id: 7, ticker: "AAPL", quantity: "12.5" });
    const onChanged = renderRow();

    fireEvent.click(screen.getByRole("button", { name: /edit aapl/i }));
    fireEvent.change(screen.getByLabelText(/shares of aapl/i), { target: { value: "12.5" } });
    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => expect(update).toHaveBeenCalledWith(7, "12.5"));
    expect(onChanged).toHaveBeenCalled();
  });

  it("can cancel an edit without saving", () => {
    const update = vi.spyOn(client, "updateHolding");
    renderRow();

    fireEvent.click(screen.getByRole("button", { name: /edit aapl/i }));
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(update).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /edit aapl/i })).toBeInTheDocument();
  });

  it("shows an error and keeps the row when saving is rejected", async () => {
    const error = new AxiosError("Request failed");
    error.response = {
      data: { detail: [{ loc: ["body", "quantity"], msg: "Input should be greater than 0" }] },
      status: 422,
      statusText: "Unprocessable Content",
      headers: {},
      config: { headers: {} } as never,
    };
    vi.spyOn(client, "updateHolding").mockRejectedValue(error);
    const onChanged = renderRow();

    fireEvent.click(screen.getByRole("button", { name: /edit aapl/i }));
    fireEvent.change(screen.getByLabelText(/shares of aapl/i), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: /^save$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/greater than 0/i);
    expect(onChanged).not.toHaveBeenCalled();
  });

  it("requires confirmation before deleting", async () => {
    const remove = vi.spyOn(client, "deleteHolding").mockResolvedValue(undefined);
    const onChanged = renderRow();

    // First click only asks for confirmation.
    fireEvent.click(screen.getByRole("button", { name: /delete aapl/i }));
    expect(remove).not.toHaveBeenCalled();
    expect(screen.getByText(/remove aapl\?/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /confirm delete aapl/i }));
    await waitFor(() => expect(remove).toHaveBeenCalledWith(7));
    expect(onChanged).toHaveBeenCalled();
  });

  it("can cancel a delete", () => {
    const remove = vi.spyOn(client, "deleteHolding");
    renderRow();

    fireEvent.click(screen.getByRole("button", { name: /delete aapl/i }));
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(remove).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /delete aapl/i })).toBeInTheDocument();
  });
});
