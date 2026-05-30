// Mirrors backend/app/schemas/risk.py

export type RiskLevel = "low" | "medium" | "high" | "very_high";

export interface RiskFactor {
  name: string;
  score: number; // 0-100 sub-score
  weight: number;
  points: number | null; // contribution to final score
  description: string;
}

export interface Risk {
  ticker: string;
  risk_score: number;
  risk_level: RiskLevel;
  factors: RiskFactor[];
  as_of: string;
  note: string;
}
