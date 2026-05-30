"use client";

import { Star, Trash2 } from "lucide-react";
import Link from "next/link";

import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToggleWatchlist, useWatchlist } from "@/lib/hooks/useWatchlist";

export default function WatchlistPage() {
  const { data, isLoading } = useWatchlist();
  const { remove } = useToggleWatchlist();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Watchlist</h1>
        <p className="text-sm text-muted-foreground">Your saved tickers.</p>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : !data || data.length === 0 ? (
        <Card className="flex flex-col items-center gap-2 py-10 text-center">
          <Star className="h-6 w-6 text-muted-foreground" />
          <p className="font-medium">No saved tickers yet</p>
          <p className="text-sm text-muted-foreground">
            Search for a stock and tap “Add to watchlist”.
          </p>
        </Card>
      ) : (
        <div className="divide-y divide-border overflow-hidden rounded-xl border border-border">
          {data.map((item) => (
            <div key={item.ticker} className="flex items-center justify-between gap-3 px-4 py-3">
              <Link href={`/stocks/${item.ticker}`} className="flex-1">
                <span className="font-semibold">{item.ticker}</span>
                {item.company_name && (
                  <span className="ml-2 text-sm text-muted-foreground">{item.company_name}</span>
                )}
              </Link>
              <button
                onClick={() => remove.mutate(item.ticker)}
                className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-bearish"
                title="Remove"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
