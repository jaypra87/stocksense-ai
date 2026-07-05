"use client";

import { ArrowRight, Star } from "lucide-react";
import Link from "next/link";

import { Reveal } from "@/components/shared/Reveal";
import { TickerLogo } from "@/components/shared/TickerLogo";
import { Skeleton } from "@/components/ui/Skeleton";
import { useWatchlist } from "@/lib/hooks/useWatchlist";

// Dashboard snapshot of saved tickers, linking through to the full watchlist.
export function WatchlistPreview() {
  const { data, isLoading } = useWatchlist();

  return (
    <section aria-labelledby="watchlist-preview-heading">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2
          id="watchlist-preview-heading"
          className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
        >
          Your watchlist
        </h2>
        <Link
          href="/watchlist"
          className="flex items-center gap-1 text-sm font-medium text-accent underline-offset-4 hover:underline"
        >
          View all <ArrowRight className="h-3.5 w-3.5" aria-hidden />
        </Link>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <div className="flex items-center gap-3 rounded-xl border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">
          <Star className="h-4 w-4 shrink-0" aria-hidden />
          Nothing saved yet — open a stock and tap “Add to watchlist”.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {data.slice(0, 6).map((item, i) => (
            <Reveal key={item.ticker} delay={i * 50}>
              <Link
                href={`/stocks/${item.ticker}`}
                className="hover-lift flex items-center gap-2.5 rounded-xl border border-border bg-card p-3.5 shadow-sm transition-colors hover:border-accent/50 dark:shadow-none"
              >
                <TickerLogo ticker={item.ticker} size="md" />
                <div className="min-w-0">
                  <div className="font-bold">{item.ticker}</div>
                  <div className="truncate text-xs text-muted-foreground">
                    {item.company_name ?? "—"}
                  </div>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      )}
    </section>
  );
}
