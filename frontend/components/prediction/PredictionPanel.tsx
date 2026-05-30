"use client";

import { Sparkles, TrendingDown, TrendingUp, Minus } from "lucide-react";
import { useState } from "react";

import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { usePrediction } from "@/lib/hooks/useStocks";
import { fmtCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Horizon } from "@/types/prediction";

const HORIZONS: Horizon[] = ["1d", "7d", "30d"];

const TREND_STYLE = {
  bullish: { color: "text-bullish", bg: "bg-bullish/15", Icon: TrendingUp, label: "Bullish" },
  bearish: { color: "text-bearish", bg: "bg-bearish/15", Icon: TrendingDown, label: "Bearish" },
  neutral: { color: "text-neutral", bg: "bg-muted", Icon: Minus, label: "Neutral" },
} as const;

export function PredictionPanel({ ticker, currency = "USD" }: { ticker: string; currency?: string }) {
  const [horizon, setHorizon] = useState<Horizon>("7d");
  const { data, isLoading, isError, error } = usePrediction(ticker, horizon);

  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-accent" /> AI Forecast
        </CardTitle>
        <div className="flex gap-1">
          {HORIZONS.map((h) => (
            <button
              key={h}
              onClick={() => setHorizon(h)}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-semibold uppercase transition-colors",
                h === horizon
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              {h}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-48" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : isError ? (
        <p className="text-sm text-muted-foreground">
          {String((error as { status?: number })?.status) === "503"
            ? "No trained model available yet. Run the training script to enable forecasts."
            : "Couldn't generate a forecast right now."}
        </p>
      ) : data ? (
        <Forecast data={data} currency={currency} />
      ) : null}
    </Card>
  );
}

function Forecast({
  data,
  currency,
}: {
  data: NonNullable<ReturnType<typeof usePrediction>["data"]>;
  currency: string;
}) {
  const style = TREND_STYLE[data.trend];
  const confidencePct = Math.round(data.confidence * 100);

  return (
    <div className="space-y-4">
      {/* Trend + confidence */}
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={cn(
            "flex items-center gap-2 rounded-lg px-3 py-1.5 text-lg font-bold",
            style.bg,
            style.color,
          )}
        >
          <style.Icon className="h-5 w-5" /> {style.label}
        </span>
        <div className="flex-1 min-w-[140px]">
          <div className="mb-1 flex justify-between text-xs text-muted-foreground">
            <span>Confidence</span>
            <span className="tabular-nums">{confidencePct}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div className={cn("h-full rounded-full", style.bg.replace("/15", ""))} style={{ width: `${confidencePct}%` }} />
          </div>
        </div>
      </div>

      {/* Expected range + model risk */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-border p-3">
          <div className="text-xs text-muted-foreground">Expected price range ({data.horizon})</div>
          <div className="text-xl font-semibold tabular-nums">
            {fmtCurrency(data.expected_low, currency)} – {fmtCurrency(data.expected_high, currency)}
          </div>
          <div className="text-xs text-muted-foreground">
            from last close {fmtCurrency(data.last_close, currency)}
          </div>
        </div>
        <div className="rounded-lg border border-border p-3">
          <div className="text-xs text-muted-foreground">Forecast risk</div>
          <div className="text-xl font-semibold tabular-nums">
            {data.risk_score != null ? Math.round(data.risk_score) : "—"}
            <span className="text-sm text-muted-foreground"> / 100</span>
          </div>
          <div className="text-xs capitalize text-muted-foreground">
            {data.risk_level?.replace("_", " ") ?? ""} · incl. model uncertainty
          </div>
        </div>
      </div>

      {/* Top factors */}
      <div>
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Why this forecast
        </div>
        <ul className="space-y-1.5">
          {data.top_factors.map((f) => (
            <li key={f.feature} className="flex items-start gap-2 text-sm">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              <span>{f.description}</span>
            </li>
          ))}
        </ul>
      </div>

      <p className="border-t border-border pt-3 text-xs text-muted-foreground">
        {data.notes}
        <br />
        <span className="font-semibold">{data.disclaimer}</span> · model {data.model_version}
      </p>
    </div>
  );
}
