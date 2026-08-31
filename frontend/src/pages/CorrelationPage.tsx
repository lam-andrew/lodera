import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CorrelationCard } from "@/features/risk/CorrelationCard";
import type { PortfolioData } from "@/hooks/usePortfolio";

/** Full-width correlation view (US-6), where a large matrix has room to breathe. */
export function CorrelationPage({ data }: { data: PortfolioData }) {
  if (data.correlation === null || data.correlation.tickers.length < 2) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Not enough holdings</CardTitle>
          <CardDescription>
            Correlation needs at least two holdings with price history.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }
  return <CorrelationCard correlation={data.correlation} />;
}
