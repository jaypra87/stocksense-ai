"use client";

import { useMutation } from "@tanstack/react-query";

import { runBacktest } from "@/lib/api/backtests";
import type { Horizon } from "@/types/backtest";

export function useRunBacktest() {
  return useMutation({
    mutationFn: (v: { ticker: string; horizon: Horizon }) => runBacktest(v.ticker, v.horizon),
  });
}
