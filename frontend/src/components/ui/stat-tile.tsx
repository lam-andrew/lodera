import type { ReactNode } from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatTileProps {
  label: string;
  value: ReactNode;
  /** Short qualifier under the value — units, comparison, or as-of date. */
  detail?: ReactNode;
  /** A badge or chip encoding state, so status reads without parsing the number. */
  badge?: ReactNode;
  chart?: ReactNode;
  className?: string;
}

/** Summary-before-detail tile for the dashboard's top row. */
export function StatTile({ label, value, detail, badge, chart, className }: StatTileProps) {
  return (
    <Card className={cn("flex flex-col gap-2 p-5", className)}>
      <span className="font-mono text-[10.5px] font-medium uppercase tracking-[0.13em] text-faint">
        {label}
      </span>
      <div className="flex items-end justify-between gap-3">
        <span className="font-mono text-[26px] font-medium leading-none tracking-tight tabular-nums">
          {value}
        </span>
        {badge}
      </div>
      {detail !== undefined && <span className="text-xs text-muted-foreground">{detail}</span>}
      {chart !== undefined && <div className="mt-1">{chart}</div>}
    </Card>
  );
}
