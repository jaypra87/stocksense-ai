"use client";

import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types/risk";

const LEVEL_META: Record<RiskLevel, { label: string; color: string }> = {
  low: { label: "Low", color: "text-bullish" },
  medium: { label: "Medium", color: "text-warning" },
  high: { label: "High", color: "text-warning" },
  very_high: { label: "Very High", color: "text-bearish" },
};

export function RiskGauge({ score, level }: { score: number; level: RiskLevel }) {
  const meta = LEVEL_META[level];
  const clamped = Math.min(100, Math.max(0, score));

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
      <div
        role="meter"
        aria-label="Composite risk score"
        aria-valuenow={Math.round(clamped)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuetext={`${Math.round(score)} out of 100 — ${meta.label} risk`}
        className="relative h-2 rounded-full bg-gradient-to-r from-bullish via-warning to-bearish"
      >
        <div
          className="absolute top-1/2 h-4 w-1 -translate-y-1/2 rounded-full bg-foreground ring-2 ring-background"
          style={{ left: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
