import type { PortfolioCorrelation } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

/** Diverging scale for a correlation cell.
 *
 *  Per docs/design/ui-direction.md: blue = moves opposite (diversifying), neutral grey = no
 *  relationship, red = moves together (concentration). A diverging scale is the correct form
 *  because 0 is a meaningful midpoint, not merely the low end — a sequential ramp would hide
 *  the difference between "unrelated" and "hedged". Colour is always paired with the printed
 *  number, so the value is never conveyed by hue alone. */
function cellStyle(value: number, dark: boolean): { background: string; color: string } {
  const magnitude = Math.min(Math.abs(value), 1);
  const neutral = dark ? [43, 52, 66] : [237, 239, 242];
  const pole =
    value >= 0 ? (dark ? [230, 103, 103] : [227, 73, 72]) : dark ? [57, 135, 229] : [42, 120, 214];

  const mix = neutral.map((c, i) => Math.round(c + (pole[i] - c) * magnitude));
  const luminance = (0.299 * mix[0] + 0.587 * mix[1] + 0.114 * mix[2]) / 255;

  return {
    background: `rgb(${mix[0]},${mix[1]},${mix[2]})`,
    color: luminance > 0.6 ? "#101620" : "#ffffff",
  };
}

function fmt(value: string | null): string {
  if (value === null) return "—";
  const n = Number(value);
  return Number.isNaN(n) ? "—" : n.toFixed(2);
}

interface CorrelationCardProps {
  correlation: PortfolioCorrelation;
}

/** Correlation among holdings (US-6): a heatmap plus the pairs that matter. */
export function CorrelationCard({ correlation }: CorrelationCardProps) {
  const { tickers, matrix } = correlation;
  const dark =
    typeof document !== "undefined" && document.documentElement.classList.contains("dark");

  if (tickers.length < 2) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Correlation</CardTitle>
          <CardDescription>How your holdings move relative to each other.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="py-6 text-center text-sm text-faint">
            Add at least two holdings with price history to see how they move together.
          </p>
        </CardContent>
      </Card>
    );
  }

  const high = Number(correlation.high_threshold);
  const top = correlation.most_correlated[0];
  const bottom = correlation.least_correlated[0];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-baseline justify-between gap-3">
          <CardTitle>Correlation</CardTitle>
          <span className="font-mono text-xs text-faint">
            {correlation.observations} trading days
          </span>
        </div>
        <CardDescription>
          How your holdings move relative to each other. Highly correlated positions behave like one
          bet, even when they look diversified.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-5">
          <div className="overflow-x-auto">
            <table className="border-separate border-spacing-[3px]">
              <thead>
                <tr>
                  <th />
                  {tickers.map((ticker) => (
                    <th
                      key={ticker}
                      scope="col"
                      className="px-1 pb-1 font-mono text-[10.5px] font-medium text-faint"
                    >
                      {ticker}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tickers.map((rowTicker, i) => (
                  <tr key={rowTicker}>
                    <th
                      scope="row"
                      className="pr-2 text-right font-mono text-[10.5px] font-medium text-faint"
                    >
                      {rowTicker}
                    </th>
                    {tickers.map((colTicker, j) => {
                      const raw = matrix[i]?.[j] ?? null;
                      const value = raw === null ? null : Number(raw);
                      const style =
                        value === null
                          ? { background: "var(--surface-2)", color: "var(--faint)" }
                          : cellStyle(value, dark);
                      return (
                        <td
                          key={colTicker}
                          title={`${rowTicker} / ${colTicker}: ${fmt(raw)}`}
                          style={style}
                          className="h-9 w-[52px] rounded-md text-center font-mono text-[11px] tabular-nums"
                        >
                          {fmt(raw)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center gap-3 text-[11px] text-faint">
            <span>−1.0</span>
            <span
              className="h-2 max-w-[200px] flex-1 rounded-full"
              style={{
                background: `linear-gradient(90deg, ${cellStyle(-1, dark).background}, ${cellStyle(0, dark).background}, ${cellStyle(1, dark).background})`,
              }}
            />
            <span>+1.0</span>
            <span className="ml-1">diversifying → moves together</span>
          </div>

          <dl className="grid gap-x-6 gap-y-1 border-t border-border pt-4 text-sm sm:grid-cols-2">
            {top !== undefined && (
              <>
                <dt className="text-muted-foreground">
                  Most correlated
                  {Number(top.correlation) >= high && (
                    <span className="ml-2 text-xs text-down">behaves like one position</span>
                  )}
                </dt>
                <dd className="font-mono tabular-nums sm:text-right">
                  {top.a} / {top.b} · {fmt(top.correlation)}
                </dd>
              </>
            )}
            {bottom !== undefined && (
              <>
                <dt className="text-muted-foreground">Least correlated</dt>
                <dd className="font-mono tabular-nums sm:text-right">
                  {bottom.a} / {bottom.b} · {fmt(bottom.correlation)}
                </dd>
              </>
            )}
            {correlation.average_correlation !== null && (
              <>
                <dt className="text-muted-foreground">Average pair</dt>
                <dd className="font-mono tabular-nums sm:text-right">
                  {fmt(correlation.average_correlation)}
                </dd>
              </>
            )}
          </dl>
        </div>
      </CardContent>
    </Card>
  );
}
