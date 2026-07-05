"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { TickerLogo } from "@/components/shared/TickerLogo";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { fmtCurrency, fmtPercent, fmtSignedCurrency, isUp } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Quote, Stock } from "@/types/stock";

export function QuoteCard({
  quote,
  stock,
  isLoading,
}: {
  quote?: Quote;
  stock?: Stock;
  isLoading: boolean;
}) {
  if (isLoading || !quote) {
    return (
      <Card className="space-y-3">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-5 w-32" />
      </Card>
    );
  }

  const up = isUp(quote.change);
  const ccy = quote.currency ?? "USD";

  return (
    <Card className="space-y-2">
      <div className="flex items-center gap-2.5">
        <TickerLogo ticker={quote.ticker} size="md" />
        <div className="flex min-w-0 items-baseline gap-2">
          <span className="text-2xl font-bold">{quote.ticker}</span>
          <span className="truncate text-sm text-muted-foreground">
            {stock?.company_name ?? ""}
          </span>
        </div>
      </div>

      <div className="text-4xl font-bold tabular-nums">{fmtCurrency(quote.price, ccy)}</div>

      <div
        className={cn(
          "flex items-center gap-1 text-sm font-semibold",
          up ? "text-bullish" : "text-bearish",
        )}
      >
        {up ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
        <span className="tabular-nums">{fmtSignedCurrency(quote.change, ccy)}</span>
        <span className="tabular-nums">({fmtPercent(quote.change_percent)})</span>
      </div>

      <p className="pt-1 text-xs text-muted-foreground">
        {quote.exchange ? `${quote.exchange} · ` : ""}
        As of {new Date(quote.as_of).toLocaleString()}
      </p>
    </Card>
  );
}
