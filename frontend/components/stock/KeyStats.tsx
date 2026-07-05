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

  const lo = quote.fifty_two_week_low;
  const hi = quote.fifty_two_week_high;
  const rangePos =
    lo != null && hi != null && hi > lo
      ? Math.min(1, Math.max(0, (quote.price - lo) / (hi - lo)))
      : null;

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

      {rangePos !== null && (
        <div className="border-t border-border pt-3">
          <div className="flex items-baseline justify-between text-xs text-muted-foreground">
            <span>52-week range</span>
            <span className="tabular-nums">{Math.round(rangePos * 100)}% of range</span>
          </div>
          <div className="relative mt-2 h-1.5 rounded-full bg-muted">
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-accent/25"
              style={{ width: `${rangePos * 100}%` }}
            />
            <span
              aria-hidden
              className="absolute top-1/2 h-3 w-[3px] -translate-y-1/2 rounded-full bg-accent"
              style={{ left: `calc(${rangePos * 100}% - 1.5px)` }}
            />
          </div>
          <div className="mt-1.5 flex justify-between text-xs tabular-nums text-muted-foreground">
            <span>{fmtCurrency(lo, ccy)}</span>
            <span>{fmtCurrency(hi, ccy)}</span>
          </div>
        </div>
      )}
    </Card>
  );
}
