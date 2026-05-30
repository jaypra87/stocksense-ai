// Mirrors backend/app/schemas/sentiment.py

export type SentimentLabel = "positive" | "negative" | "neutral" | "mixed";

export interface SentimentItem {
  title: string;
  publisher: string | null;
  url: string | null;
  published_at: string | null;
  label: "positive" | "negative" | "neutral";
  score: number;
}

export interface Sentiment {
  ticker: string;
  overall_label: SentimentLabel;
  overall_score: number;
  headline_count: number;
  counts: { positive: number; negative: number; neutral: number };
  summary: string;
  items: SentimentItem[];
  note: string;
}
