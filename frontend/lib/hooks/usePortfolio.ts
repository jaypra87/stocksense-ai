"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getPortfolio, getTrades, placeTrade, resetPortfolio } from "@/lib/api/portfolio";

const PORTFOLIO_KEY = ["portfolio"];
const TRADES_KEY = ["portfolio", "trades"];

export function usePortfolio() {
  return useQuery({
    queryKey: PORTFOLIO_KEY,
    queryFn: getPortfolio,
    refetchInterval: 30 * 1000, // positions are marked at the live quote, same cadence as useQuote
  });
}

export function useTrades(limit = 50) {
  return useQuery({ queryKey: [...TRADES_KEY, limit], queryFn: () => getTrades(limit) });
}

export function usePortfolioMutations() {
  const qc = useQueryClient();
  const refresh = () => {
    void qc.invalidateQueries({ queryKey: PORTFOLIO_KEY });
  };
  const trade = useMutation({ mutationFn: placeTrade, onSuccess: refresh });
  const reset = useMutation({
    mutationFn: resetPortfolio,
    onSuccess: (data) => {
      qc.setQueryData(PORTFOLIO_KEY, data);
      void qc.invalidateQueries({ queryKey: TRADES_KEY });
    },
  });
  return { trade, reset };
}
