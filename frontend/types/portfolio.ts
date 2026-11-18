// Mirrors backend/app/schemas/portfolio.py.

export type TradeSide = "buy" | "sell";

export interface Trade {
  id: string;
  ticker: string;
  side: TradeSide;
  quantity: number;
  price: number;
  total: number;
  realized_pnl: number | null;
  executed_at: string | null;
}

export interface Position {
  ticker: string;
  company_name: string | null;
  currency: string | null;
  quantity: number;
  avg_cost: number;
  price: number;
  price_stale: boolean;
  cost_basis: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  day_change: number | null;
  day_change_pct: number | null;
  weight: number;
}

export interface Portfolio {
  cash: number;
  starting_cash: number;
  equity: number;
  market_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  total_return: number;
  total_return_pct: number;
  day_change: number;
  day_change_pct: number;
  positions: Position[];
  as_of: string;
  reset_at: string | null;
  disclaimer: string;
}

/** An order sized in shares or in money, never both. */
export type TradeOrder = { ticker: string; side: TradeSide } & (
  | { quantity: number; amount?: never }
  | { amount: number; quantity?: never }
);
