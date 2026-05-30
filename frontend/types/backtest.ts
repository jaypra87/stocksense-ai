import type { Horizon } from "@/types/prediction";

export type { Horizon };

export interface BacktestMetrics {
  n_predictions: number;
  directional_accuracy: number;
  baseline_accuracy: number;
  persistence_accuracy: number;
  mae: number;
  rmse: number;
  baseline_mae: number;
  beats_baseline: boolean;
}

export interface EquityPoint {
  date: string;
  model: number;
  buy_hold: number;
}

export interface Backtest {
  id: string;
  ticker: string;
  horizon: string;
  model_version: string;
  start_date: string | null;
  end_date: string | null;
  status: string;
  metrics: BacktestMetrics;
  chart_data: {
    equity: EquityPoint[];
    cumulative_accuracy: { date: string; accuracy: number }[];
    returns: { date: string; pred_return: number; actual_return: number }[];
  };
  note: string;
  disclaimer: string;
  created_at: string | null;
}
