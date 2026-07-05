"use client";

import { Star, Trash2 } from "lucide-react";
import Link from "next/link";

import { Reveal } from "@/components/shared/Reveal";
import { TickerLogo } from "@/components/shared/TickerLogo";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";
import { useToggleWatchlist, useWatchlist } from "@/lib/hooks/useWatchlist";

export default function WatchlistPage() {
  const { data, isLoading } = useWatchlist();
  const { remove } = useToggleWatchlist();
  const { toast } = useToast();

  function onRemove(ticker: string) {
    remove.mutate(ticker, {
      onSuccess: () => toast(`${ticker} removed from watchlist`),
      onError: () => toast(`Couldn't remove ${ticker}`, "error"),
    });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Watchlist</h1>
        <p className="mt-1 text-sm text-muted-foreground">Your saved tickers.</p>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState
          icon={Star}
          title="No saved tickers yet"
          description="Search for a stock and tap “Add to watchlist”."
        />
      ) : (
        <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
          {data.map((item, i) => (
            <Reveal
              as="li"
              key={item.ticker}
              delay={i * 40}
              className="flex items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-card-hover"
            >
              <Link href={`/stocks/${item.ticker}`} className="flex flex-1 items-center gap-3">
                <TickerLogo ticker={item.ticker} size="sm" />
                <span>
                  <span className="font-semibold">{item.ticker}</span>
                  {item.company_name && (
                    <span className="ml-2 text-sm text-muted-foreground">{item.company_name}</span>
                  )}
                </span>
              </Link>
              <button
                onClick={() => onRemove(item.ticker)}
                aria-label={`Remove ${item.ticker} from watchlist`}
                className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-bearish"
              >
                <Trash2 className="h-4 w-4" aria-hidden />
              </button>
            </Reveal>
          ))}
        </ul>
      )}
    </div>
  );
}
