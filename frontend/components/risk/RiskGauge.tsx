"use client";

import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types/risk";

const LEVEL_META: Record<RiskLevel, { label: string; color: string }> = {
  low: { label: "Low", color: "text-bullish" },
  medium: { label: "Medium", color: "text-yellow-500" },
  high: { label: "High", color: "text-orange-500" },
  very_high: { label: "Very High", color: "text-bearish" },
};

export function RiskGauge({ score, level }: { score: number; level: RiskLevel }) {
  const meta = LEVEL_META[level];
  return (
    <div className="space-y-2">
      <div className="flex items-baseline gap-2">
        <span className={cn("text-4xl font-bold tabular-nums", meta.color)}>
          {Math.round(score)}
        </span>
        <span className="text-sm text-muted-foreground">/ 100</span>
        <span className={cn("ml-auto text-sm font-semibold uppercase", meta.color)}>
          {meta.label} risk
        </span>
      </div>
      {/* Gradient track (green → red) with a marker at the score. */}
      <div className="relative h-2 rounded-full bg-gradient-to-r from-bullish via-yellow-500 to-bearish">
        <div
          className="absolute top-1/2 h-4 w-1 -translate-y-1/2 rounded-full bg-foreground ring-2 ring-background"
          style={{ left: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
    </div>
  );
}
