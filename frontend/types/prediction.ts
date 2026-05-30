// Mirrors backend/app/schemas/prediction.py

import type { RiskFactor, RiskLevel } from "@/types/risk";

export type Horizon = "1d" | "7d" | "30d";

export interface TopFactor {
  feature: string;
  value: number;
  importance: number;
  contribution: number | null;
  direction: "elevated" | "depressed" | null;
  description: string;
}

export interface Prediction {
  ticker: string;
  horizon: string;
  trend: "bullish" | "bearish" | "neutral";
  confidence: number;
  expected_return_low: number | null;
  expected_return_high: number | null;
  expected_low: number | null;
  expected_high: number | null;
  last_close: number | null;
  risk_score: number | null;
  risk_level: RiskLevel | null;
  risk_factors: RiskFactor[];
  model_version: string;
  class_probabilities: Record<string, number>;
  top_factors: TopFactor[];
  notes: string;
  disclaimer: string;
}
