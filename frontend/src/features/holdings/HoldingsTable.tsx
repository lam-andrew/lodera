import type { Holding } from "@/api/client";

function formatShares(quantity: string): string {
  const value = Number(quantity);
  if (Number.isNaN(value)) return quantity;
  return value.toLocaleString(undefined, { maximumFractionDigits: 6 });
}

interface HoldingsTableProps {
  holdings: Holding[];
}

/** Renders the portfolio's holdings, or an empty-state prompt when there are none. */
export function HoldingsTable({ holdings }: HoldingsTableProps) {
  if (holdings.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-faint">
        No holdings yet. Add your first position below.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left">
            <th className="px-2 py-2 font-mono text-[10.5px] font-medium uppercase tracking-wider text-faint">
              Ticker
            </th>
            <th className="px-2 py-2 text-right font-mono text-[10.5px] font-medium uppercase tracking-wider text-faint">
              Shares
            </th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding) => (
            <tr key={holding.id} className="border-b border-border/60 last:border-0">
              <td className="px-2 py-3 font-medium text-foreground">{holding.ticker}</td>
              <td className="px-2 py-3 text-right font-mono tabular-nums text-foreground">
                {formatShares(holding.quantity)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
