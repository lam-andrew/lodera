import { useState } from "react";

import { deleteHolding, toErrorMessage, updateHolding, type Holding } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** What the row is currently doing. Delete requires an explicit confirm step (US-3). */
type RowMode = "view" | "editing" | "confirmDelete";

function formatShares(quantity: string): string {
  const value = Number(quantity);
  if (Number.isNaN(value)) return quantity;
  return value.toLocaleString(undefined, { maximumFractionDigits: 6 });
}

interface HoldingRowProps {
  holding: Holding;
  onChanged: () => void;
}

export function HoldingRow({ holding, onChanged }: HoldingRowProps) {
  const [mode, setMode] = useState<RowMode>("view");
  const [draft, setDraft] = useState(holding.quantity);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function startEditing() {
    setDraft(String(Number(holding.quantity)));
    setError(null);
    setMode("editing");
  }

  function cancel() {
    setError(null);
    setMode("view");
  }

  async function save() {
    setBusy(true);
    setError(null);
    try {
      await updateHolding(holding.id, draft.trim());
      setMode("view");
      onChanged();
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function confirmDelete() {
    setBusy(true);
    setError(null);
    try {
      await deleteHolding(holding.id);
      onChanged();
    } catch (err) {
      setError(toErrorMessage(err));
      setBusy(false);
      setMode("view");
    }
  }

  return (
    <>
      <tr className="border-b border-border/60 last:border-0">
        <td className="px-2 py-3 font-medium text-foreground">{holding.ticker}</td>
        <td className="px-2 py-3 text-right">
          {mode === "editing" ? (
            <Input
              aria-label={`Shares of ${holding.ticker}`}
              type="number"
              min="0"
              step="any"
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              className="ml-auto h-8 w-28 text-right font-mono tabular-nums"
            />
          ) : (
            <span className="font-mono tabular-nums text-foreground">
              {formatShares(holding.quantity)}
            </span>
          )}
        </td>
        <td className="px-2 py-3">
          <div className="flex items-center justify-end gap-1.5">
            {mode === "view" && (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={startEditing}
                  aria-label={`Edit ${holding.ticker}`}
                >
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setMode("confirmDelete")}
                  aria-label={`Delete ${holding.ticker}`}
                  className="text-down hover:bg-down/10"
                >
                  Delete
                </Button>
              </>
            )}

            {mode === "editing" && (
              <>
                <Button
                  size="sm"
                  onClick={() => void save()}
                  disabled={busy || draft.trim() === ""}
                >
                  {busy ? "Saving…" : "Save"}
                </Button>
                <Button variant="ghost" size="sm" onClick={cancel} disabled={busy}>
                  Cancel
                </Button>
              </>
            )}

            {mode === "confirmDelete" && (
              <>
                <span className="mr-1 text-xs text-muted-foreground">Remove {holding.ticker}?</span>
                <Button
                  size="sm"
                  onClick={() => void confirmDelete()}
                  disabled={busy}
                  aria-label={`Confirm delete ${holding.ticker}`}
                  className="bg-down text-white hover:opacity-90"
                >
                  {busy ? "Removing…" : "Confirm"}
                </Button>
                <Button variant="ghost" size="sm" onClick={cancel} disabled={busy}>
                  Cancel
                </Button>
              </>
            )}
          </div>
        </td>
      </tr>

      {error != null && (
        <tr>
          <td colSpan={3} className="px-2 pb-3 text-right text-sm text-down" role="alert">
            {error}
          </td>
        </tr>
      )}
    </>
  );
}
