import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ConcentrationCard } from "@/features/risk/ConcentrationCard";
import type { PortfolioData } from "@/hooks/usePortfolio";

/** Concentration and exposure (US-7). */
export function ConcentrationPage({ data }: { data: PortfolioData }) {
  if (data.concentration === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Concentration unavailable</CardTitle>
          <CardDescription>Add priced holdings to measure exposure.</CardDescription>
        </CardHeader>
      </Card>
    );
  }
  return <ConcentrationCard data={data.concentration} />;
}
