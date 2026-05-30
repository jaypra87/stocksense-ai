"use client";

import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { fmtCompact, fmtCurrency } from "@/lib/format";
import type { Quote } from "@/types/stock";

export function KeyStats({ quote, isLoading }: { quote?: Quote; isLoading: boolean }) {
  if (isLoading || !quote) {
    return (
      <Card className="space-y-3">
        <CardTitle>Key stats</CardTitle>
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-5 w-full" />
        ))}
      </Card>
    );
  }

  const ccy = quote.currency ?? "USD";
  const rows: [string, string][] = [
    ["Open", fmtCurrency(quote.open, ccy)],
    ["Day high", fmtCurrency(quote.day_high, ccy)],
    ["Day low", fmtCurrency(quote.day_low, ccy)],
    ["Prev close", fmtCurrency(quote.previous_close, ccy)],
    ["Volume", fmtCompact(quote.volume)],
    ["Market cap", fmtCompact(quote.market_cap)],
    ["52w high", fmtCurrency(quote.fifty_two_week_high, ccy)],
    ["52w low", fmtCurrency(quote.fifty_two_week_low, ccy)],
  ];

  return (
    <Card className="space-y-3">
      <CardTitle>Key stats</CardTitle>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-2">
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="font-medium tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}
