"use client";

import { Badge } from "@/components/ui/Badge";
import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { fmtCurrency, fmtNumber, fmtSignedCurrency, isUp } from "@/lib/format";
import { useTrades } from "@/lib/hooks/usePortfolio";
import { cn } from "@/lib/utils";

export function TradeHistory() {
  const trades = useTrades(50);

  return (
    <Card className="space-y-3">
      <CardTitle>Trade history</CardTitle>
      {trades.isLoading ? (
        <Skeleton className="h-16 w-full" />
      ) : !trades.data || trades.data.length === 0 ? (
        <p className="text-sm text-muted-foreground">No fills yet.</p>
      ) : (
        <ul className="divide-y divide-border">
          {trades.data.map((t) => (
            <li key={t.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
              <div className="flex items-center gap-2.5">
                <Badge
                  tone={t.side === "buy" ? "accent" : "neutral"}
                  className="w-12 justify-center"
                >
                  {t.side === "buy" ? "Buy" : "Sell"}
                </Badge>
                <span>
                  <span className="font-semibold">{t.ticker}</span>
                  <span className="ml-2 tabular-nums text-muted-foreground">
                    {fmtNumber(t.quantity, 4)} @ {fmtCurrency(t.price)}
                  </span>
                </span>
              </div>
              <div className="text-right tabular-nums">
                <div className="font-medium">{fmtCurrency(t.total)}</div>
                {t.realized_pnl != null ? (
                  <div
                    className={cn(
                      "text-xs",
                      isUp(t.realized_pnl) ? "text-bullish" : "text-bearish",
                    )}
                  >
                    {fmtSignedCurrency(t.realized_pnl)} realized
                  </div>
                ) : (
                  t.executed_at && (
                    <div className="text-xs text-muted-foreground">
                      {new Date(t.executed_at).toLocaleString()}
                    </div>
                  )
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
