import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DrawdownCard } from "@/features/risk/DrawdownCard";
import type { PortfolioData } from "@/hooks/usePortfolio";

/** Historical drawdown (US-8). */
export function DrawdownPage({ data }: { data: PortfolioData }) {
  if (data.drawdown === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Drawdown unavailable</CardTitle>
          <CardDescription>Add holdings with price history to see declines.</CardDescription>
        </CardHeader>
      </Card>
    );
  }
  return <DrawdownCard data={data.drawdown} />;
}
