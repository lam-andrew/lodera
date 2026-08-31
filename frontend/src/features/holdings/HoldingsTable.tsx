import type { HoldingRisk, Position } from "@/api/client";

import { formatCurrency } from "./format";
import { HoldingRow } from "./HoldingRow";

interface HoldingsTableProps {
  positions: Position[];
  totalValue: string | null;
  riskByTicker?: Record<string, HoldingRisk>;
  onChanged: () => void;
}

const numericHeader =
  "px-2 py-2 text-right font-mono text-[10.5px] font-medium uppercase tracking-wider text-faint";

/** Holdings with market data (US-1 view, US-3 manage, US-4 prices), or an empty state. */
export function HoldingsTable({
  positions,
  totalValue,
  riskByTicker,
  onChanged,
}: HoldingsTableProps) {
  if (positions.length === 0) {
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
            <th className={numericHeader}>Shares</th>
            <th className={numericHeader}>Price</th>
            <th className={numericHeader}>Value</th>
            <th className={numericHeader}>Weight</th>
            <th className={numericHeader}>Volatility</th>
            <th className="px-2 py-2 text-right">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {positions.map((position) => (
            <HoldingRow
              key={position.id}
              position={position}
              risk={riskByTicker?.[position.ticker]}
              onChanged={onChanged}
            />
          ))}
        </tbody>
        {totalValue !== null && (
          <tfoot>
            <tr className="border-t border-border">
              <td className="px-2 py-3 font-mono text-[10.5px] uppercase tracking-wider text-faint">
                Total
              </td>
              <td />
              <td />
              <td className="px-2 py-3 text-right font-mono tabular-nums font-medium text-foreground">
                {formatCurrency(totalValue)}
              </td>
              <td />
              <td />
              <td />
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  );
}
