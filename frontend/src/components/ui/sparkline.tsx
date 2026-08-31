/** A compact trend line for a stat tile.
 *
 *  Hand-drawn SVG rather than a charting library: at this size there are no axes, ticks or
 *  tooltips to justify the dependency, and inline SVG inherits the design tokens directly.
 *  The last point is emphasized so the eye lands on "now". */
interface SparklineProps {
  values: number[];
  /** CSS colour (usually a token) for the line and its fade. */
  color?: string;
  className?: string;
  label?: string;
}

export function Sparkline({ values, color = "var(--accent)", className, label }: SparklineProps) {
  if (values.length < 2) return null;

  const width = 240;
  const height = 40;
  const pad = 3;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const x = (i: number) => pad + (i / (values.length - 1)) * (width - 2 * pad);
  const y = (v: number) => pad + (1 - (v - min) / range) * (height - 2 * pad);

  const line = values
    .map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)} ${y(v).toFixed(1)}`)
    .join(" ");
  const area = `${line} L${x(values.length - 1).toFixed(1)} ${height - pad} L${x(0).toFixed(1)} ${height - pad} Z`;
  const gradientId = `spark-${label?.replace(/\W/g, "") ?? "x"}-${values.length}`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className={className}
      role="img"
      aria-label={label ?? "Trend"}
      style={{ width: "100%", height: 40 }}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.22" />
          <stop offset="1" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradientId})`} />
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={x(values.length - 1)} cy={y(values[values.length - 1])} r="2.4" fill={color} />
    </svg>
  );
}
