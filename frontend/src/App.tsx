/**
 * Root application component — the US-1 portfolio screen: a header with a live backend-status
 * pill, the holdings list, and the add-holding form.
 */
import { useEffect, useState } from "react";

import { getHealth } from "@/api/client";
import { APP_NAME, APP_TAGLINE } from "@/config/branding";
import { PortfolioView } from "@/features/holdings/PortfolioView";

function BackendStatus() {
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((health) => active && setOk(health.database === "connected"))
      .catch(() => active && setOk(false));
    return () => {
      active = false;
    };
  }, []);

  const label = ok === null ? "Checking…" : ok ? "Connected" : "Offline";
  const dot = ok ? "bg-up" : ok === false ? "bg-down" : "bg-faint";

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs text-muted-foreground">
      <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
      {label}
    </span>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-3xl px-5 py-10">
        <header className="mb-8 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{APP_NAME}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{APP_TAGLINE}</p>
          </div>
          <BackendStatus />
        </header>
        <PortfolioView />
      </div>
    </div>
  );
}
