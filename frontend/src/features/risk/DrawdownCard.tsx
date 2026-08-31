import type { PortfolioDrawdown } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

function pct(value: string | null): string {
  if (value === null) return "—";
  const n = Number(value);
  return Number.isNaN(n) ? "—" : `${n.toFixed(1)}%`;
}

function shortDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "2-digit" });
}

/** Underwater plot: distance below the running peak, always ≤ 0.
 *
 *  Drawn downward from a zero baseline because that is the quantity's actual shape — a
 *  drawdown can never be positive, so a chart centred on zero would waste half its space and
 *  imply gains it cannot show. */
function Underwater({ series }: { series: PortfolioDrawdown["series"] }) {
  if (series.length < 2) return null;

  const width = 560;
  const height = 150;
  const padY = 10;
  const values = series.map((p) => Number(p.drawdown_pct));
  const worst = Math.min(...values, -1);

  const x = (i: number) => (i / (series.length - 1)) * width;
  const y = (v: number) => padY + (v / worst) * (height - padY * 2);

  const line = values
    .map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)} ${y(v).toFixed(1)}`)
    .join(" ");
  const area = `${line} L${width} ${y(0)} L0 ${y(0)} Z`;
  const troughIndex = values.indexOf(Math.min(...values));

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((f) => f * worst);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full"
      style={{ height: 150 }}
      role="img"
      aria-label={`Portfolio drawdown over time, deepest ${pct(String(worst))}`}
    >
      <defs>
        <linearGradient id="dd-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--down)" stopOpacity="0.05" />
          <stop offset="1" stopColor="var(--down)" stopOpacity="0.3" />
        </linearGradient>
      </defs>

      {gridLines.map((v) => (
        <g key={v}>
          <line x1="0" x2={width} y1={y(v)} y2={y(v)} stroke="var(--border)" strokeWidth="1" />
          <text
            x={width - 2}
            y={y(v) - 3}
            textAnchor="end"
            fill="var(--faint)"
            fontSize="9"
            fontFamily="IBM Plex Mono, monospace"
          >
            {v === 0 ? "0%" : `${v.toFixed(0)}%`}
          </text>
        </g>
      ))}

      <path d={area} fill="url(#dd-fill)" />
      <path d={line} fill="none" stroke="var(--down)" strokeWidth="1.6" strokeLinejoin="round" />
      <circle cx={x(troughIndex)} cy={y(values[troughIndex])} r="3" fill="var(--down)" />
    </svg>
  );
}

/** Historical drawdown (US-8): how far the portfolio fell, and whether it came back. */
export function DrawdownCard({ data }: { data: PortfolioDrawdown }) {
  if (data.series.length === 0 || data.max_drawdown_pct === null) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Drawdown</CardTitle>
          <CardDescription>
            Add holdings with price history to see the portfolio&apos;s worst declines.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const current = Number(data.current_drawdown_pct ?? 0);
  const underwater = current < -0.05;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-baseline justify-between gap-3">
          <CardTitle>Drawdown</CardTitle>
          <span className="font-mono text-xs text-faint">{data.observations} trading days</span>
        </div>
        <CardDescription>
          How far the portfolio fell from a high, and whether it recovered.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-5">
          <div className="flex flex-wrap items-end gap-x-8 gap-y-3">
            <div className="flex flex-col gap-1">
              <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                Worst decline
              </span>
              <span className="font-mono text-3xl font-medium leading-none tabular-nums text-down">
                {pct(data.max_drawdown_pct)}
              </span>
            </div>
            <div className="flex flex-col gap-1">
              <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                Currently
              </span>
              <span
                className={`font-mono text-3xl font-medium leading-none tabular-nums ${underwater ? "text-down" : "text-up"}`}
              >
                {underwater ? pct(data.current_drawdown_pct) : "At peak"}
              </span>
            </div>
          </div>

          <Underwater series={data.series} />

          {data.episodes.length > 0 && (
            <div className="flex flex-col gap-2 border-t border-border pt-4">
              <h3 className="text-sm font-medium">Largest declines</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left">
                      {["Depth", "Peak", "Trough", "Recovery"].map((h) => (
                        <th
                          key={h}
                          className="pb-1.5 font-mono text-[10px] uppercase tracking-wider text-faint last:text-right"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.episodes.map((episode) => (
                      <tr key={`${episode.peak_date}-${episode.trough_date}`}>
                        <td className="py-1.5 pr-4 font-mono tabular-nums text-down">
                          {pct(episode.depth_pct)}
                        </td>
                        <td className="py-1.5 pr-4 font-mono text-xs tabular-nums text-muted-foreground">
                          {shortDate(episode.peak_date)}
                        </td>
                        <td className="py-1.5 pr-4 font-mono text-xs tabular-nums text-muted-foreground">
                          {shortDate(episode.trough_date)} · {episode.decline_days}d
                        </td>
                        <td className="py-1.5 text-right font-mono text-xs tabular-nums">
                          {episode.recovered ? (
                            <span className="text-up">
                              {shortDate(episode.recovery_date ?? "")} · {episode.recovery_days}d
                            </span>
                          ) : (
                            <span className="text-down">not recovered</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
