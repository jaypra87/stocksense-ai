"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { addToWatchlist, getWatchlist, removeFromWatchlist } from "@/lib/api/watchlist";
import type { WatchlistItem } from "@/types/watchlist";

const KEY = ["watchlist"];

export function useWatchlist() {
  return useQuery({ queryKey: KEY, queryFn: getWatchlist });
}

export function useToggleWatchlist() {
  const qc = useQueryClient();
  const onSuccess = (data: WatchlistItem[]) => qc.setQueryData(KEY, data);
  const add = useMutation({ mutationFn: addToWatchlist, onSuccess });
  const remove = useMutation({ mutationFn: removeFromWatchlist, onSuccess });
  return { add, remove };
}
