"use client";

import { Star } from "lucide-react";

import { useToggleWatchlist, useWatchlist } from "@/lib/hooks/useWatchlist";
import { cn } from "@/lib/utils";

export function WatchlistButton({ ticker }: { ticker: string }) {
  const { data } = useWatchlist();
  const { add, remove } = useToggleWatchlist();
  const saved = data?.some((w) => w.ticker === ticker) ?? false;
  const busy = add.isPending || remove.isPending;

  return (
    <button
      onClick={() => (saved ? remove.mutate(ticker) : add.mutate(ticker))}
      disabled={busy}
      className={cn(
        "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50",
        saved
          ? "border-accent bg-accent/10 text-accent"
          : "border-border text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
    >
      <Star className={cn("h-4 w-4", saved && "fill-current")} />
      {saved ? "In watchlist" : "Add to watchlist"}
    </button>
  );
}
