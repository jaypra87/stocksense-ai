"use client";

import { Star } from "lucide-react";

import { useToast } from "@/components/ui/Toast";
import { useToggleWatchlist, useWatchlist } from "@/lib/hooks/useWatchlist";
import { cn } from "@/lib/utils";

export function WatchlistButton({ ticker }: { ticker: string }) {
  const { data } = useWatchlist();
  const { add, remove } = useToggleWatchlist();
  const { toast } = useToast();
  const saved = data?.some((w) => w.ticker === ticker) ?? false;
  const busy = add.isPending || remove.isPending;

  function onToggle() {
    const mutation = saved ? remove : add;
    mutation.mutate(ticker, {
      onSuccess: () =>
        toast(saved ? `${ticker} removed from watchlist` : `${ticker} added to watchlist`),
      onError: () => toast(`Couldn't update watchlist for ${ticker}`, "error"),
    });
  }

  return (
    <button
      onClick={onToggle}
      disabled={busy}
      aria-pressed={saved}
      className={cn(
        "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50",
        saved
          ? "border-accent bg-accent/10 text-accent"
          : "border-border text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
    >
      <Star className={cn("h-4 w-4", saved && "fill-current")} aria-hidden />
      {saved ? "In watchlist" : "Add to watchlist"}
    </button>
  );
}
