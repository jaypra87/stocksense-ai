"use client";

import Link from "next/link";

import { TickerLogo } from "@/components/shared/TickerLogo";
import { fmtCurrency, fmtNumber, fmtPercent, fmtSignedCurrency, isUp } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Position } from "@/types/portfolio";

const TH = "py-1.5 pr-3 font-semibold";
const TD = "py-2.5 pr-3 tabular-nums";

export function HoldingsTable({
  positions,
  onTrade,
}: {
  positions: Position[];
  onTrade: (ticker: string) => void;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <caption className="sr-only">Open paper positions</caption>
        <thead className="text-left text-xs uppercase tracking-wide text-muted-foreground">
          <tr>
            <th scope="col" className={TH}>
              Holding
            </th>
            <th scope="col" className={cn(TH, "text-right")}>
              Shares
            </th>
            <th scope="col" className={cn(TH, "hidden text-right xl:table-cell")}>
              Avg cost
            </th>
            <th scope="col" className={cn(TH, "text-right")}>
              Price
            </th>
            <th scope="col" className={cn(TH, "hidden text-right md:table-cell")}>
              Value
            </th>
            <th scope="col" className={cn(TH, "text-right")}>
              Return
            </th>
            <th scope="col" className={cn(TH, "hidden text-right sm:table-cell")}>
              Weight
            </th>
            <th scope="col" className="py-1.5">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {positions.map((p, i) => {
            const ccy = p.currency ?? "USD";
            const up = isUp(p.unrealized_pnl);
            return (
              <tr
                key={p.ticker}
                className="animate-fade-up border-t border-border transition-colors hover:bg-card-hover"
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <td className="py-2.5 pr-3">
                  <Link href={`/stocks/${p.ticker}`} className="flex items-center gap-2.5">
                    <TickerLogo ticker={p.ticker} size="sm" />
                    <span className="min-w-0">
                      <span className="block font-semibold leading-tight">{p.ticker}</span>
                      {p.company_name && (
                        <span className="block max-w-[11rem] truncate text-xs text-muted-foreground">
                          {p.company_name}
                        </span>
                      )}
                    </span>
                  </Link>
                </td>
                <td className={cn(TD, "text-right")}>{fmtNumber(p.quantity, 4)}</td>
                <td className={cn(TD, "hidden text-right xl:table-cell")}>
                  {fmtCurrency(p.avg_cost, ccy)}
                </td>
                <td className={cn(TD, "text-right")}>
                  {fmtCurrency(p.price, ccy)}
                  {p.price_stale && (
                    <span
                      className="ml-1 text-xs text-warning"
                      title="Quote unavailable, marked at cost"
                    >
                      *
                    </span>
                  )}
                </td>
                <td className={cn(TD, "hidden text-right md:table-cell")}>
                  {fmtCurrency(p.market_value, ccy)}
                </td>
                <td className={cn(TD, "text-right", up ? "text-bullish" : "text-bearish")}>
                  <div className="font-semibold">{fmtSignedCurrency(p.unrealized_pnl, ccy)}</div>
                  <div className="text-xs">{fmtPercent(p.unrealized_pnl_pct)}</div>
                </td>
                <td className={cn(TD, "hidden text-right text-muted-foreground sm:table-cell")}>
                  {fmtNumber(p.weight, 1)}%
                </td>
                <td className="py-2.5 text-right">
                  <button
                    onClick={() => onTrade(p.ticker)}
                    className="rounded-md px-2 py-1 text-xs font-semibold text-accent transition-colors hover:bg-accent/10"
                  >
                    Trade
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
