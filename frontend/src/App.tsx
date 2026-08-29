/**
 * Root application component.
 *
 * For the Sprint 1 skeleton this simply proves the end-to-end slice: the frontend calls the
 * backend's `/health` contract and renders the result. Feature UI (portfolio entry, risk
 * dashboard, Q&A) replaces this as their user stories land.
 */
import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "./api/client";
import { APP_NAME, APP_TAGLINE } from "./config/branding";

type Status =
  | { kind: "loading" }
  | { kind: "ready"; health: HealthResponse }
  | { kind: "error"; message: string };

export default function App() {
  const [status, setStatus] = useState<Status>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    getHealth()
      .then((health) => active && setStatus({ kind: "ready", health }))
      .catch(
        (err: unknown) =>
          active &&
          setStatus({
            kind: "error",
            message: err instanceof Error ? err.message : "Unknown error",
          }),
      );
    return () => {
      active = false;
    };
  }, []);

  return (
    <main
      style={{
        fontFamily: "system-ui, sans-serif",
        maxWidth: 640,
        margin: "4rem auto",
        padding: "0 1rem",
      }}
    >
      <h1>{APP_NAME}</h1>
      <p style={{ color: "#555" }}>{APP_TAGLINE}</p>

      <section aria-label="Backend status" style={{ marginTop: "2rem" }}>
        <h2
          style={{
            fontSize: "1rem",
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#888",
          }}
        >
          Backend status
        </h2>
        {status.kind === "loading" && <p role="status">Checking backend…</p>}
        {status.kind === "error" && (
          <p role="alert" style={{ color: "#b00020" }}>
            Cannot reach backend: {status.message}
          </p>
        )}
        {status.kind === "ready" && (
          <dl
            style={{ display: "grid", gridTemplateColumns: "max-content 1fr", gap: "0.25rem 1rem" }}
          >
            <dt>Service</dt>
            <dd>{status.health.service}</dd>
            <dt>Status</dt>
            <dd>{status.health.status}</dd>
            <dt>Version</dt>
            <dd>{status.health.version}</dd>
            <dt>Environment</dt>
            <dd>{status.health.environment}</dd>
            <dt>Database</dt>
            <dd>{status.health.database}</dd>
          </dl>
        )}
      </section>
    </main>
  );
}
