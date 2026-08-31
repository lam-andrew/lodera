import { Link } from "react-router-dom";

/** Sends the reader to the part of the methodology that explains this metric.
 *
 *  Placed on each risk card so the explanation is reachable at the moment of confusion,
 *  rather than only from the sidebar. */
export function ExplainLink({
  anchor,
  label = "How this is calculated",
}: {
  anchor: string;
  label?: string;
}) {
  return (
    <Link
      to={`/methodology#${anchor}`}
      className="whitespace-nowrap text-xs text-muted-foreground underline-offset-4 hover:text-accent hover:underline"
    >
      {label}
    </Link>
  );
}
