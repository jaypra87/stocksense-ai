import { apiFetch } from "@/lib/api/client";
import type { Portfolio, Trade, TradeOrder } from "@/types/portfolio";

export function getPortfolio(): Promise<Portfolio> {
  return apiFetch<Portfolio>("/portfolio");
}

export function placeTrade(order: TradeOrder): Promise<Trade> {
  // Decimals cross the wire as strings so the ledger never sees float noise.
  const body = {
    ticker: order.ticker,
    side: order.side,
    ...(order.quantity != null ? { quantity: String(order.quantity) } : {}),
    ...(order.amount != null ? { amount: order.amount.toFixed(2) } : {}),
  };
  return apiFetch<Trade>("/portfolio/trades", { method: "POST", body });
}

export function getTrades(limit = 50): Promise<Trade[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiFetch<Trade[]>(`/portfolio/trades?${params}`);
}

export function resetPortfolio(): Promise<Portfolio> {
  return apiFetch<Portfolio>("/portfolio/reset", { method: "POST" });
}
