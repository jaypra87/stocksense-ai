"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

import { CompareChart } from "@/components/compare/CompareChart";
import { CompareRow } from "@/components/compare/CompareRow";
import { Card, CardTitle } from "@/components/ui/Card";

const MAX = 6;

export default function ComparePage() {
  const [tickers, setTickers] = useState<string[]>(["AAPL", "NVDA", "MSFT"]);
  const [input, setInput] = useState("");

  function add(e: React.FormEvent) {
    e.preventDefault();
    const t = input.trim().toUpperCase();
    if (t && !tickers.includes(t) && tickers.length < MAX) {
      setTickers([...tickers, t]);
    }
    setInput("");
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Compare</h1>
        <p className="text-sm text-muted-foreground">
          Compare tickers by price, daily change, risk, sentiment, and rebased returns.
        </p>
      </div>

      <form onSubmit={add} className="flex gap-2">
        <input
          placeholder={`Add a ticker (up to ${MAX})`}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={tickers.length >= MAX}
          className="w-48 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={tickers.length >= MAX}
          className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-sm font-semibold text-accent-foreground hover:opacity-90 disabled:opacity-50"
        >
          <Plus className="h-4 w-4" /> Add
        </button>
      </form>

      {tickers.length === 0 ? (
        <Card className="py-10 text-center text-sm text-muted-foreground">
          Add a few tickers to compare them.
        </Card>
      ) : (
        <>
          <Card className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="py-1 pr-4">Ticker</th>
                  <th className="py-1 pr-4">Price</th>
                  <th className="py-1 pr-4">Change</th>
                  <th className="py-1 pr-4">Risk</th>
                  <th className="py-1 pr-4">Sentiment</th>
                  <th className="py-1" />
                </tr>
              </thead>
              <tbody>
                {tickers.map((t) => (
                  <CompareRow
                    key={t}
                    ticker={t}
                    onRemove={() => setTickers(tickers.filter((x) => x !== t))}
                  />
                ))}
              </tbody>
            </table>
          </Card>

          <Card className="space-y-3">
            <CardTitle>Rebased returns (6M, start = 100)</CardTitle>
            <CompareChart tickers={tickers} />
          </Card>
        </>
      )}
    </div>
  );
}
