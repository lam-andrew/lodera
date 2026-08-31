import type { ReactNode } from "react";

/** Shared building blocks for explanatory pages.
 *
 *  These mirror the structure of the reasoning itself: a formula block, a chosen-vs-rejected
 *  pairing, and a caveat. Keeping them as named components stops the methodology page from
 *  becoming an undifferentiated wall of prose. */

export function Formula({ lines, where }: { lines: string[]; where?: ReactNode }) {
  return (
    <div className="flex flex-col gap-2.5 overflow-x-auto rounded-lg border border-border bg-surface-2 px-5 py-4">
      {lines.map((line, i) => (
        <code
          key={line}
          className={`whitespace-nowrap font-mono text-[15px] font-medium ${i > 0 ? "text-accent" : "text-foreground"}`}
        >
          {line}
        </code>
      ))}
      {where !== undefined && (
        <div className="flex flex-col gap-0.5 text-[13px] text-muted-foreground">{where}</div>
      )}
    </div>
  );
}

/** What was chosen and what was rejected — the rejected option is often the more
 *  informative half, because it says what the number is *not*. */
export function TradeOff({
  chosen,
  chosenLabel,
  rejected,
  rejectedLabel,
}: {
  chosenLabel: string;
  chosen: ReactNode;
  rejectedLabel: string;
  rejected: ReactNode;
}) {
  return (
    <div className="grid gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-2">
      <div className="flex flex-col gap-1.5 bg-surface p-4">
        <span className="font-mono text-[10px] font-medium uppercase tracking-[0.1em] text-up">
          Used · {chosenLabel}
        </span>
        <p className="text-[13.5px] leading-relaxed text-muted-foreground">{chosen}</p>
      </div>
      <div className="flex flex-col gap-1.5 bg-surface p-4">
        <span className="font-mono text-[10px] font-medium uppercase tracking-[0.1em] text-down">
          Rejected · {rejectedLabel}
        </span>
        <p className="text-[13.5px] leading-relaxed text-muted-foreground">{rejected}</p>
      </div>
    </div>
  );
}

export function Caveat({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-r-lg border-l-2 border-accent bg-accent/10 px-4 py-3 text-[14px] leading-relaxed text-muted-foreground">
      {children}
    </div>
  );
}

/** A figure drawn from the reader's own portfolio, so the explanation is about their data. */
export function YourFigure({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-baseline gap-1.5 rounded-md border border-border bg-surface-2 px-2 py-0.5 align-middle">
      <span className="font-mono text-[10px] uppercase tracking-wider text-faint">{label}</span>
      <span className="font-mono text-[13px] font-medium tabular-nums">{value}</span>
    </span>
  );
}

export function Section({
  id,
  index,
  title,
  children,
}: {
  id: string;
  index: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="flex scroll-mt-6 flex-col gap-4">
      <div className="flex items-baseline gap-4">
        <span className="font-mono text-[13px] font-medium text-accent">{index}</span>
        <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
      </div>
      {children}
    </section>
  );
}

export function Prose({ children }: { children: ReactNode }) {
  return (
    <div className="flex max-w-[66ch] flex-col gap-3.5 text-[15px] leading-relaxed text-muted-foreground">
      {children}
    </div>
  );
}
