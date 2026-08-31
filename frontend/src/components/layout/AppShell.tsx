import { useEffect, useState, type ReactNode } from "react";

import { getHealth } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Sidebar } from "./Sidebar";

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
  const dot = ok === null ? "bg-faint" : ok ? "bg-up" : "bg-down";

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs text-muted-foreground">
      <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
      {label}
    </span>
  );
}

interface AppShellProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}

/** Sidebar + main column. The sidebar is fixed on desktop and collapses to a toggle on
 *  narrow screens, so the dashboard grid never has to compete with it for width. */
export function AppShell({ title, subtitle, actions, children }: AppShellProps) {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[236px_1fr]">
      <aside className="hidden border-r border-border bg-surface lg:sticky lg:top-0 lg:block lg:h-screen">
        <Sidebar />
      </aside>

      {navOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            className="absolute inset-0 bg-black/50"
            aria-label="Close navigation"
            onClick={() => setNavOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full w-64 border-r border-border bg-surface">
            <Sidebar onNavigate={() => setNavOpen(false)} />
          </div>
        </div>
      )}

      <main className="min-w-0 px-5 py-6 sm:px-7 lg:px-8">
        <header className="mb-6 flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <Button
              variant="outline"
              size="icon"
              className="lg:hidden"
              aria-label="Open navigation"
              onClick={() => setNavOpen(true)}
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="h-4 w-4"
              >
                <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
              </svg>
            </Button>
            <div>
              <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
              {subtitle !== undefined && (
                <p className="mt-0.5 text-[13px] text-muted-foreground">{subtitle}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {actions}
            <BackendStatus />
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
