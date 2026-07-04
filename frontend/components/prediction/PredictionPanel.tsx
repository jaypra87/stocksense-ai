"use client";

import { Minus, Sparkles, TrendingDown, TrendingUp } from "lucide-react";
import { useState } from "react";

import { Card, CardTitle } from "@/components/ui/Card";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatTile } from "@/components/ui/StatTile";
import { ApiError } from "@/lib/api/client";
import { fmtCurrency } from "@/lib/format";
import { usePrediction } from "@/lib/hooks/useStocks";
import { cn } from "@/lib/utils";
import type { Horizon } from "@/types/prediction";

const HORIZONS: readonly Horizon[] = ["1d", "7d", "30d"];

const TREND_STYLE = {
  bullish: {
    color: "text-bullish",
    chipBg: "bg-bullish/15",
    barBg: "bg-bullish",
    Icon: TrendingUp,
    label: "Bullish",
  },
  bearish: {
    color: "text-bearish",
    chipBg: "bg-bearish/15",
    barBg: "bg-bearish",
    Icon: TrendingDown,
    label: "Bearish",
  },
  neutral: {
    color: "text-neutral",
    chipBg: "bg-muted",
    barBg: "bg-neutral",
    Icon: Minus,
    label: "Neutral",
  },
} as const;

export function PredictionPanel({
  ticker,
  currency = "USD",
}: {
  ticker: string;
  currency?: string;
}) {
  const [horizon, setHorizon] = useState<Horizon>("7d");
  const { data, isLoading, isError, error } = usePrediction(ticker, horizon);

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-accent" aria-hidden /> AI Forecast
        </CardTitle>
        <SegmentedControl
          options={HORIZONS}
          value={horizon}
          onChange={setHorizon}
          label="Forecast horizon"
        />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-48" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : isError ? (
        <p className="text-sm text-muted-foreground">
          {error instanceof ApiError && error.status === 503
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
            style.chipBg,
            style.color,
          )}
        >
          <style.Icon className="h-5 w-5" aria-hidden /> {style.label}
        </span>
        <div className="min-w-[140px] flex-1">
          <div className="mb-1 flex justify-between text-xs text-muted-foreground">
            <span>Confidence</span>
            <span className="tabular-nums">{confidencePct}%</span>
          </div>
          <div
            role="progressbar"
            aria-label="Forecast confidence"
            aria-valuenow={confidencePct}
            aria-valuemin={0}
            aria-valuemax={100}
            className="h-2 overflow-hidden rounded-full bg-muted"
          >
            <div
              className={cn("h-full rounded-full", style.barBg)}
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Expected range + model risk */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <StatTile
          label={`Expected price range (${data.horizon})`}
          value={`${fmtCurrency(data.expected_low, currency)} – ${fmtCurrency(data.expected_high, currency)}`}
          sub={`from last close ${fmtCurrency(data.last_close, currency)}`}
        />
        <StatTile
          label="Forecast risk"
          value={
            <>
              {data.risk_score != null ? Math.round(data.risk_score) : "—"}
              <span className="text-sm text-muted-foreground"> / 100</span>
            </>
          }
          sub={`${data.risk_level?.replace("_", " ") ?? ""} · incl. model uncertainty`}
        />
      </div>

      {/* Top factors */}
      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Why this forecast
        </h3>
        <ul className="space-y-1.5">
          {data.top_factors.map((f) => (
            <li key={f.feature} className="flex items-start gap-2 text-sm">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" aria-hidden />
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
