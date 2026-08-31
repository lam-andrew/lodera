import type { Holding } from "@/api/client";

import { HoldingRow } from "./HoldingRow";

interface HoldingsTableProps {
  holdings: Holding[];
  onChanged: () => void;
}

/** Renders the portfolio's holdings with edit/delete controls (US-1 view, US-3 manage),
 *  or an empty-state prompt when there are none. */
export function HoldingsTable({ holdings, onChanged }: HoldingsTableProps) {
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
            <th className="px-2 py-2 text-right">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((holding) => (
            <HoldingRow key={holding.id} holding={holding} onChanged={onChanged} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
