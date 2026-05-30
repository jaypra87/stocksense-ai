import { apiFetch } from "@/lib/api/client";
import type { WatchlistItem } from "@/types/watchlist";

export function getWatchlist(): Promise<WatchlistItem[]> {
  return apiFetch<WatchlistItem[]>("/watchlist");
}

export function addToWatchlist(ticker: string): Promise<WatchlistItem[]> {
  return apiFetch<WatchlistItem[]>(`/watchlist/${encodeURIComponent(ticker)}`, { method: "POST" });
}

export function removeFromWatchlist(ticker: string): Promise<WatchlistItem[]> {
  return apiFetch<WatchlistItem[]>(`/watchlist/${encodeURIComponent(ticker)}`, {
    method: "DELETE",
  });
}
