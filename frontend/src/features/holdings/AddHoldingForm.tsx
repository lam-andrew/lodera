import { useState, type FormEvent } from "react";

import { addHolding, toErrorMessage, type Holding } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AddHoldingFormProps {
  onAdded: (holding: Holding) => void;
}

/** Form to add a holding by ticker + share quantity (US-1). Shows a clear inline error and
 *  adds nothing when the backend rejects the input. */
export function AddHoldingForm({ onAdded }: AddHoldingFormProps) {
  const [ticker, setTicker] = useState("");
  const [quantity, setQuantity] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const holding = await addHolding(ticker.trim(), quantity.trim());
      onAdded(holding);
      setTicker("");
      setQuantity("");
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  const canSubmit = ticker.trim() !== "" && quantity.trim() !== "" && !submitting;

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <div className="flex flex-1 flex-col gap-1.5">
          <Label htmlFor="ticker">Ticker</Label>
          <Input
            id="ticker"
            name="ticker"
            placeholder="e.g. AAPL"
            autoComplete="off"
            autoCapitalize="characters"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            aria-invalid={error != null}
          />
        </div>
        <div className="flex flex-1 flex-col gap-1.5">
          <Label htmlFor="quantity">Shares</Label>
          <Input
            id="quantity"
            name="quantity"
            type="number"
            inputMode="decimal"
            min="0"
            step="any"
            placeholder="e.g. 10"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            aria-invalid={error != null}
          />
        </div>
        <Button type="submit" disabled={!canSubmit} className="sm:w-auto">
          {submitting ? "Adding…" : "Add holding"}
        </Button>
      </div>

      {error != null && (
        <p role="alert" className="text-sm text-down">
          {error}
        </p>
      )}
    </form>
  );
}
