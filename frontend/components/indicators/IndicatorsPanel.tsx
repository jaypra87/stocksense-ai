"use client";

import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { fmtCurrency, fmtNumber, fmtPctValue } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { Indicators } from "@/types/indicator";

type Tone = "bull" | "bear" | "neutral";

function Badge({ label, tone }: { label: string; tone: Tone }) {
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
        tone === "bull" && "bg-bullish/15 text-bullish",
        tone === "bear" && "bg-bearish/15 text-bearish",
        tone === "neutral" && "bg-muted text-muted-foreground",
      )}
    >
      {label}
    </span>
  );
}

function Tile({
  label,
  value,
  badge,
  sub,
}: {
  label: string;
  value: string;
  badge?: React.ReactNode;
  sub?: string;
}) {
  return (
    <div className="rounded-lg border border-border p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">{label}</span>
        {badge}
      </div>
      <div className="mt-1 text-lg font-semibold tabular-nums">{value}</div>
      {sub && <div className="text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

export function IndicatorsPanel({
  data,
  isLoading,
  currency = "USD",
}: {
  data?: Indicators;
  isLoading: boolean;
  currency?: string;
}) {
  if (isLoading || !data) {
    return (
      <Card className="space-y-3">
        <CardTitle>Technical Indicators</CardTitle>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      </Card>
    );
  }

  const { latest, signals } = data;

  const rsiTone: Tone =
    signals.rsi_zone === "overbought" ? "bear" : signals.rsi_zone === "oversold" ? "bull" : "neutral";

  const aboveBadge = (above: boolean | null) =>
    above == null ? undefined : (
      <Badge label={above ? "above" : "below"} tone={above ? "bull" : "bear"} />
    );

  return (
    <Card className="space-y-3">
      <CardTitle>Technical Indicators</CardTitle>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Tile
          label="RSI (14)"
          value={fmtNumber(latest.rsi_14, 1)}
          badge={signals.rsi_zone ? <Badge label={signals.rsi_zone} tone={rsiTone} /> : undefined}
        />
        <Tile
          label="MACD"
          value={fmtNumber(latest.macd, 3)}
          badge={
            signals.macd_bullish == null ? undefined : (
              <Badge
                label={signals.macd_bullish ? "bullish" : "bearish"}
                tone={signals.macd_bullish ? "bull" : "bear"}
              />
            )
          }
          sub={`signal ${fmtNumber(latest.macd_signal, 3)}`}
        />
        <Tile label="Volatility (30d ann.)" value={fmtPctValue(latest.volatility_30)} />
        <Tile
          label="Drawdown"
          value={fmtPctValue(latest.drawdown)}
          sub={`max ${fmtPctValue(latest.max_drawdown)}`}
        />
        <Tile
          label="SMA 30"
          value={fmtCurrency(latest.sma_30, currency)}
          badge={aboveBadge(signals.above_sma_30)}
        />
        <Tile
          label="SMA 100"
          value={fmtCurrency(latest.sma_100, currency)}
          badge={aboveBadge(signals.above_sma_100)}
        />
        <Tile label="EMA 20" value={fmtCurrency(latest.ema_20, currency)} />
        <Tile
          label="Rel. volume"
          value={`${fmtNumber(latest.relative_volume, 2)}×`}
          badge={signals.volume_spike ? <Badge label="spike" tone="bear" /> : undefined}
        />
      </div>
    </Card>
  );
}
