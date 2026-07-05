import { apiFetch } from "@/lib/api/client";
import type { Backtest, Horizon } from "@/types/backtest";

export function runBacktest(ticker: string, horizon: Horizon): Promise<Backtest> {
  const params = new URLSearchParams({ horizon });
  return apiFetch<Backtest>(`/backtests/${encodeURIComponent(ticker)}?${params}`, {
    method: "POST",
  });
}
