/** Display formatting for portfolio figures. Values arrive as decimal strings from the
 *  API (exact), and are only converted to Number at the point of display. */

export function formatShares(quantity: string): string {
  const value = Number(quantity);
  if (Number.isNaN(value)) return quantity;
  return value.toLocaleString(undefined, { maximumFractionDigits: 6 });
}

export function formatCurrency(amount: string | null): string {
  if (amount === null) return "—";
  const value = Number(amount);
  if (Number.isNaN(value)) return "—";
  return value.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  });
}

export function formatPercent(pct: string | null): string {
  if (pct === null) return "—";
  const value = Number(pct);
  if (Number.isNaN(value)) return "—";
  return `${value.toFixed(1)}%`;
}
