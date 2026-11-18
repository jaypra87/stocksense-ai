"use client";

import { ArrowRight, Briefcase } from "lucide-react";
import Link from "next/link";

import { Reveal } from "@/components/shared/Reveal";
import { TickerLogo } from "@/components/shared/TickerLogo";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { fmtCurrency, fmtPercent, fmtSignedCurrency, isUp } from "@/lib/format";
import { usePortfolio } from "@/lib/hooks/usePortfolio";
import { cn } from "@/lib/utils";

// Dashboard snapshot of the paper account, linking through to the full page.
export function PortfolioPreview() {
  const { data, isLoading } = usePortfolio();

  return (
    <section aria-labelledby="portfolio-preview-heading">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2
          id="portfolio-preview-heading"
          className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
        >
          Paper portfolio
        </h2>
        <Link
          href="/portfolio"
          className="flex items-center gap-1 text-sm font-medium text-accent underline-offset-4 hover:underline"
        >
          Open portfolio <ArrowRight className="h-3.5 w-3.5" aria-hidden />
        </Link>
      </div>

      {isLoading || !data ? (
        <Skeleton className="h-24 w-full" />
      ) : (
        <Reveal>
          <div className="hover-lift flex flex-col gap-4 rounded-xl border border-border bg-card p-4 shadow-sm dark:shadow-none sm:flex-row sm:items-center">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-accent/15 text-accent">
                <Briefcase className="h-5 w-5" aria-hidden />
              </div>
              <div>
                <div className="text-2xl font-bold tabular-nums">{fmtCurrency(data.equity)}</div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span
                    className={cn(
                      "font-semibold tabular-nums",
                      isUp(data.total_return) ? "text-bullish" : "text-bearish",
                    )}
                  >
                    {fmtSignedCurrency(data.total_return)} ({fmtPercent(data.total_return_pct)})
                  </span>
                  all time
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 sm:ml-auto">
              {data.positions.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  {fmtCurrency(data.cash)} of paper money, ready to invest.
                </p>
              ) : (
                data.positions.slice(0, 4).map((p) => (
                  <Link
                    key={p.ticker}
                    href={`/stocks/${p.ticker}`}
                    className="flex items-center gap-1.5 rounded-full border border-border py-1 pl-1 pr-2.5 text-xs font-semibold transition-colors hover:bg-muted"
                  >
                    <TickerLogo ticker={p.ticker} size="sm" />
                    {p.ticker}
                    <Badge tone={isUp(p.unrealized_pnl) ? "bull" : "bear"}>
                      {fmtPercent(p.unrealized_pnl_pct)}
                    </Badge>
                  </Link>
                ))
              )}
            </div>
          </div>
        </Reveal>
      )}
    </section>
  );
}
