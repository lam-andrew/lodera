import { useRef, useState } from "react";

import { importHoldings, toErrorMessage, type ImportResult } from "@/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface ImportCardProps {
  onImported: () => void;
}

/** Upload a CSV / brokerage positions export (US-2).
 *
 *  Reports what was added, updated, ignored, and — per FR-3 — every row that could not be
 *  parsed, with its line number, so the user can fix their file. */
export function ImportCard({ onImported }: ImportCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleFile(file: File) {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const imported = await importHoldings(file);
      setResult(imported);
      onImported();
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  const importedCount = result ? result.added.length + result.updated.length : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import from a CSV</CardTitle>
        <CardDescription>
          Upload a positions export from your brokerage (Fidelity, Schwab, Vanguard and similar), or
          any CSV with a ticker and share-quantity column.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <input
              ref={inputRef}
              id="csv-file"
              type="file"
              accept=".csv,text/csv"
              aria-label="Portfolio CSV file"
              disabled={busy}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void handleFile(file);
              }}
              className="block w-full text-sm text-muted-foreground file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-border file:bg-surface-2 file:px-3 file:py-2 file:text-sm file:font-medium file:text-foreground hover:file:bg-surface"
            />
            {busy && <span className="whitespace-nowrap text-sm text-faint">Importing…</span>}
          </div>

          {error !== null && (
            <p role="alert" className="text-sm text-down">
              {error}
            </p>
          )}

          {result !== null && (
            <div className="flex flex-col gap-3 border-t border-border pt-4">
              <p className="text-sm" role="status">
                {importedCount > 0 ? (
                  <span className="text-up">
                    Imported {importedCount} {importedCount === 1 ? "position" : "positions"}
                    {result.added.length > 0 && ` · ${result.added.length} added`}
                    {result.updated.length > 0 && ` · ${result.updated.length} updated`}
                  </span>
                ) : (
                  <span className="text-muted-foreground">No positions were imported.</span>
                )}
                {result.skipped > 0 && (
                  <span className="text-faint"> · {result.skipped} rows ignored</span>
                )}
              </p>

              {result.ticker_column !== null && (
                <p className="font-mono text-xs text-faint">
                  Read “{result.ticker_column}” as the ticker and “{result.quantity_column}” as the
                  quantity.
                </p>
              )}

              {result.problems.length > 0 && (
                <div className="flex flex-col gap-2">
                  <p className="text-sm font-medium text-down">
                    {result.problems.length} {result.problems.length === 1 ? "row" : "rows"} could
                    not be imported
                  </p>
                  <ul className="flex flex-col gap-1">
                    {result.problems.map((problem, index) => (
                      <li
                        key={`${problem.row}-${index}`}
                        className="flex gap-3 text-xs text-muted-foreground"
                      >
                        <span className="shrink-0 font-mono text-faint">Line {problem.row}</span>
                        <span>{problem.reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
