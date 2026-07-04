// Mirrors the backend Pydantic schemas in backend/app/schemas/stock.py.
// Keeping these in sync is manual for now; a future phase could codegen them
// from the OpenAPI spec FastAPI already exposes at /openapi.json.

export const RANGES = ["1d", "5d", "1m", "6m", "ytd", "1y", "5y"] as const;
export type Range = (typeof RANGES)[number];

export interface SearchResult {
  symbol: string;
  name: string | null;
  exchange: string | null;
  type: string | null;
}

export interface Stock {
  ticker: string;
  company_name: string | null;
  exchange: string | null;
  sector: string | null;
  currency: string | null;
  metadata: Record<string, unknown>;
  updated_at: string | null;
}

export interface Quote {
  ticker: string;
  price: number;
  previous_close: number | null;
  change: number | null;
  change_percent: number | null;
  open: number | null;
  day_high: number | null;
  day_low: number | null;
  volume: number | null;
  market_cap: number | null;
  fifty_two_week_high: number | null;
  fifty_two_week_low: number | null;
  currency: string | null;
  exchange: string | null;
  as_of: string;
}

export interface Candle {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close: number | null;
  volume: number | null;
}

export interface History {
  ticker: string;
  range: Range;
  interval: string;
  candles: Candle[];
}
