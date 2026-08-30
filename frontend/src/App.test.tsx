import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as client from "./api/client";
import { APP_NAME } from "./config/branding";

describe("App", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the product heading", () => {
    vi.spyOn(client, "getHealth").mockReturnValue(new Promise(() => {}));
    render(<App />);
    expect(screen.getByRole("heading", { level: 1, name: APP_NAME })).toBeInTheDocument();
  });

  it("shows backend health once the /health call resolves", async () => {
    vi.spyOn(client, "getHealth").mockResolvedValue({
      status: "ok",
      service: "Orbit API",
      version: "0.1.0",
      environment: "test",
      database: "connected",
    });

    render(<App />);

    expect(await screen.findByText("Orbit API")).toBeInTheDocument();
    expect(screen.getByText("connected")).toBeInTheDocument();
  });

  it("surfaces an error when the backend is unreachable", async () => {
    vi.spyOn(client, "getHealth").mockRejectedValue(new Error("Network Error"));

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent(/cannot reach backend/i);
  });
});
