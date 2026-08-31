/**
 * Application routes and shell (US-10).
 *
 * Portfolio data is loaded once here and shared across pages, so navigating between the
 * overview and holdings does not refetch prices, risk and correlation each time.
 */
import { Route, Routes } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { usePortfolio, type PortfolioData, type PortfolioState } from "@/hooks/usePortfolio";
import { ConcentrationPage } from "@/pages/ConcentrationPage";
import { CorrelationPage } from "@/pages/CorrelationPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { DrawdownPage } from "@/pages/DrawdownPage";
import { HoldingsPage } from "@/pages/HoldingsPage";

function Loading() {
  return (
    <p role="status" className="py-16 text-center text-sm text-faint">
      Loading portfolio…
    </p>
  );
}

function LoadError({ message }: { message: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Could not load your portfolio</CardTitle>
        <CardDescription>{message}</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Check that the backend is running, then reload the page.
        </p>
      </CardContent>
    </Card>
  );
}

/** Renders its children only once portfolio data is available, showing the shared loading
 *  and error states otherwise — so each page can assume it has data. */
function Loaded({
  state,
  children,
}: {
  state: PortfolioState;
  children: (data: PortfolioData) => JSX.Element;
}) {
  if (state.kind === "loading") return <Loading />;
  if (state.kind === "error") return <LoadError message={state.message} />;
  return children(state.data);
}

export default function App() {
  const { state, refresh } = usePortfolio();
  const positions = state.kind === "ready" ? state.data.summary.positions.length : 0;

  return (
    <Routes>
      <Route
        path="/"
        element={
          <AppShell
            title="Risk overview"
            subtitle={`Personal portfolio · ${positions} ${positions === 1 ? "position" : "positions"}`}
          >
            <Loaded state={state}>
              {(data) => <DashboardPage data={data} onChanged={refresh} />}
            </Loaded>
          </AppShell>
        }
      />
      <Route
        path="/holdings"
        element={
          <AppShell title="Holdings" subtitle="Add, edit, import and remove positions">
            <Loaded state={state}>
              {(data) => <HoldingsPage data={data} onChanged={refresh} />}
            </Loaded>
          </AppShell>
        }
      />
      <Route
        path="/correlation"
        element={
          <AppShell title="Correlation" subtitle="How your holdings move relative to each other">
            <Loaded state={state}>{(data) => <CorrelationPage data={data} />}</Loaded>
          </AppShell>
        }
      />
      <Route
        path="/concentration"
        element={
          <AppShell title="Concentration" subtitle="Where the portfolio is overexposed">
            <Loaded state={state}>{(data) => <ConcentrationPage data={data} />}</Loaded>
          </AppShell>
        }
      />
      <Route
        path="/drawdown"
        element={
          <AppShell title="Drawdown" subtitle="The portfolio's worst historical declines">
            <Loaded state={state}>{(data) => <DrawdownPage data={data} />}</Loaded>
          </AppShell>
        }
      />
      <Route
        path="*"
        element={
          <AppShell title="Page not found">
            <Card>
              <CardHeader>
                <CardTitle>That page doesn&apos;t exist</CardTitle>
                <CardDescription>Pick a destination from the sidebar.</CardDescription>
              </CardHeader>
            </Card>
          </AppShell>
        }
      />
    </Routes>
  );
}
