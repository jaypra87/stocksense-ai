import { apiFetch } from "@/lib/api/client";
import type { Indicators } from "@/types/indicator";
import type { Horizon, Prediction } from "@/types/prediction";
import type { Risk } from "@/types/risk";
import type { Sentiment } from "@/types/sentiment";
import type { History, Quote, Range, SearchResult, Stock } from "@/types/stock";

export function searchStocks(query: string, limit = 10): Promise<SearchResult[]> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return apiFetch<SearchResult[]>(`/stocks/search?${params}`);
}

export function getStock(ticker: string): Promise<Stock> {
  return apiFetch<Stock>(`/stocks/${encodeURIComponent(ticker)}`);
}

export function getQuote(ticker: string): Promise<Quote> {
  return apiFetch<Quote>(`/stocks/${encodeURIComponent(ticker)}/quote`);
}

export function getHistory(ticker: string, range: Range): Promise<History> {
  const params = new URLSearchParams({ range });
  return apiFetch<History>(`/stocks/${encodeURIComponent(ticker)}/history?${params}`);
}

export function getIndicators(ticker: string, range: Range): Promise<Indicators> {
  const params = new URLSearchParams({ range });
  return apiFetch<Indicators>(`/stocks/${encodeURIComponent(ticker)}/indicators?${params}`);
}

export function createPrediction(ticker: string, horizon: Horizon): Promise<Prediction> {
  const params = new URLSearchParams({ horizon });
  return apiFetch<Prediction>(`/predictions/${encodeURIComponent(ticker)}?${params}`, {
    method: "POST",
  });
}

export function getRisk(ticker: string): Promise<Risk> {
  return apiFetch<Risk>(`/stocks/${encodeURIComponent(ticker)}/risk`);
}

export function getSentiment(ticker: string): Promise<Sentiment> {
  return apiFetch<Sentiment>(`/stocks/${encodeURIComponent(ticker)}/sentiment`);
}
