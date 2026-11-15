import { Sparkles, TrendingUp } from "lucide-react";

import { StatTile } from "@/components/ui/StatTile";
import { cn } from "@/lib/utils";

// A static example of the forecast panel for the landing hero. It mirrors the
// layout of components/prediction/PredictionPanel.tsx so the first thing a
// visitor sees is what the product looks like. The figures are illustrative,
// not a live forecast, and the card says so.

const HORIZONS = ["1D", "7D", "30D"] as const;
const ACTIVE_HORIZON = "7D";

const FACTORS = [
  "Price is above its 30-day moving average",
  "RSI is around 58 (neutral momentum)",
  "Volume is about 1.3x its recent average",
];

export function ForecastPreview() {
  const confidencePct = 63;

  return (
    <div
      aria-label="Example forecast for a stock, with confidence, expected range, risk and reasons"
      className="rounded-xl border border-border bg-card p-5 shadow-sm dark:shadow-none"
    >
      {/* Ticker row */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-lg font-bold tracking-tight">AAPL</p>
          <p className="text-xs text-muted-foreground">Apple Inc. · NASDAQ</p>
        </div>
        <span className="rounded-full border border-border px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
          Example
        </span>
      </div>

      {/* Panel title + horizon switch */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
        <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Sparkles className="h-4 w-4 text-accent" aria-hidden /> AI Forecast
        </p>
        <div className="flex rounded-lg bg-muted p-0.5" aria-hidden>
          {HORIZONS.map((h) => (
            <span
              key={h}
              className={cn(
                "rounded-md px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
                h === ACTIVE_HORIZON
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground",
              )}
            >
              {h}
            </span>
          ))}
        </div>
      </div>

      {/* Trend + confidence */}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <span className="flex items-center gap-2 rounded-lg bg-bullish/15 px-3 py-1.5 text-lg font-bold text-bullish">
          <TrendingUp className="h-5 w-5" aria-hidden /> Bullish
        </span>
        <div className="min-w-[140px] flex-1">
          <div className="mb-1 flex justify-between text-xs text-muted-foreground">
            <span>Confidence</span>
            <span className="tabular-nums">{confidencePct}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted" aria-hidden>
            <div className="h-full rounded-full bg-bullish" style={{ width: `${confidencePct}%` }} />
          </div>
        </div>
      </div>

      {/* Expected range + risk */}
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <StatTile
          label="Expected price range (7d)"
          value="$226.40 to $241.80"
          sub="from last close $231.10"
        />
        <StatTile
          label="Forecast risk"
          value={
            <>
              42<span className="text-sm text-muted-foreground"> / 100</span>
            </>
          }
          sub="medium · incl. model uncertainty"
        />
      </div>

      {/* Why */}
      <div className="mt-4">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Why this forecast
        </p>
        <ul className="space-y-1.5">
          {FACTORS.map((f) => (
            <li key={f} className="flex items-start gap-2 text-sm">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" aria-hidden />
              <span>{f}</span>
            </li>
          ))}
        </ul>
      </div>

      <p className="mt-4 border-t border-border pt-3 text-xs text-muted-foreground">
        Relatively confident, but this is still a probabilistic estimate.
      </p>
    </div>
  );
}
