"use client";

import { GitCompare, Plus } from "lucide-react";
import { useState } from "react";

import { CompareChart } from "@/components/compare/CompareChart";
import { CompareRow } from "@/components/compare/CompareRow";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";

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
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Compare</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Compare tickers by price, daily change, risk, sentiment, and rebased returns.
        </p>
      </div>

      <form onSubmit={add} className="flex items-end gap-2">
        <div className="w-56">
          <Input
            label={`Add a ticker (up to ${MAX})`}
            placeholder="e.g. AMZN"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={tickers.length >= MAX}
          />
        </div>
        <Button type="submit" disabled={tickers.length >= MAX}>
          <Plus className="h-4 w-4" aria-hidden /> Add
        </Button>
      </form>

      {tickers.length === 0 ? (
        <EmptyState
          icon={GitCompare}
          title="Nothing to compare yet"
          description="Add a few tickers to compare them side by side."
        />
      ) : (
        <>
          <Card className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">Side-by-side ticker comparison</caption>
              <thead className="text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Ticker</th>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Price</th>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Change</th>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Risk</th>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Sentiment</th>
                  <th scope="col" className="py-1.5">
                    <span className="sr-only">Actions</span>
                  </th>
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
