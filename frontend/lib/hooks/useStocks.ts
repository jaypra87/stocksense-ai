"use client";

import { useQuery } from "@tanstack/react-query";

import {
  createPrediction,
  getHistory,
  getIndicators,
  getQuote,
  getRisk,
  getSentiment,
  getStock,
  searchStocks,
} from "@/lib/api/stocks";
import type { Horizon } from "@/types/prediction";
import type { Range } from "@/types/stock";

export function useSearch(query: string) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: () => searchStocks(query),
    enabled: query.trim().length >= 1,
    staleTime: 60 * 60 * 1000, // matches backend's 1h search cache
  });
}

export function useStock(ticker: string) {
  return useQuery({
    queryKey: ["stock", ticker],
    queryFn: () => getStock(ticker),
    enabled: ticker.length > 0,
  });
}

export function useQuote(ticker: string) {
  return useQuery({
    queryKey: ["quote", ticker],
    queryFn: () => getQuote(ticker),
    enabled: ticker.length > 0,
    refetchInterval: 30 * 1000, // re-poll every 30s for a "live" feel
  });
}

export function useHistory(ticker: string, range: Range) {
  return useQuery({
    queryKey: ["history", ticker, range],
    queryFn: () => getHistory(ticker, range),
    enabled: ticker.length > 0,
  });
}

export function useIndicators(ticker: string, range: Range) {
  return useQuery({
    queryKey: ["indicators", ticker, range],
    queryFn: () => getIndicators(ticker, range),
    enabled: ticker.length > 0,
  });
}

export function useRisk(ticker: string) {
  return useQuery({
    queryKey: ["risk", ticker],
    queryFn: () => getRisk(ticker),
    enabled: ticker.length > 0,
  });
}

export function useSentiment(ticker: string) {
  return useQuery({
    queryKey: ["sentiment", ticker],
    queryFn: () => getSentiment(ticker),
    enabled: ticker.length > 0,
    staleTime: 15 * 60 * 1000, // matches backend's 15min cache
  });
}

export function usePrediction(ticker: string, horizon: Horizon) {
  // A prediction is a POST (it logs a row to history), but we drive it via
  // useQuery so it loads on view and caches. High staleTime avoids re-running
  // it on every render/focus.
  return useQuery({
    queryKey: ["prediction", ticker, horizon],
    queryFn: () => createPrediction(ticker, horizon),
    enabled: ticker.length > 0,
    staleTime: 5 * 60 * 1000,
    retry: 0, // a 503 (no model trained) shouldn't be retried
  });
}
