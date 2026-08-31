import { cn } from "@/lib/utils";

type Band = "low" | "moderate" | "high" | null;

const LABELS = { low: "Low", moderate: "Moderate", high: "Elevated" } as const;
const TEXT = { low: "text-up", moderate: "text-warn", high: "text-down" } as const;
const DOT = { low: "bg-up", moderate: "bg-warn", high: "bg-down" } as const;

/** Descriptive volatility band. Colour is always paired with a text label, never alone. */
export function RiskBadge({ band, className }: { band: Band; className?: string }) {
  if (band === null) return null;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-border px-2.5 py-0.5 text-xs font-medium",
        TEXT[band],
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", DOT[band])} aria-hidden="true" />
      {LABELS[band]}
    </span>
  );
}
