"use client";

import { Badge } from "@/components/ui/Badge";
import type { BadgeTone } from "@/components/ui/Badge";
import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatTile } from "@/components/ui/StatTile";
import { fmtCurrency, fmtNumber, fmtPctValue } from "@/lib/format";
import type { Indicators } from "@/types/indicator";

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

  const rsiTone: BadgeTone =
    signals.rsi_zone === "overbought"
      ? "bear"
      : signals.rsi_zone === "oversold"
        ? "bull"
        : "neutral";

  const aboveBadge = (above: boolean | null) =>
    above == null ? undefined : (
      <Badge tone={above ? "bull" : "bear"}>{above ? "above" : "below"}</Badge>
    );

  return (
    <Card className="space-y-3">
      <CardTitle>Technical Indicators</CardTitle>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile
          label="RSI (14)"
          value={fmtNumber(latest.rsi_14, 1)}
          badge={signals.rsi_zone ? <Badge tone={rsiTone}>{signals.rsi_zone}</Badge> : undefined}
        />
        <StatTile
          label="MACD"
          value={fmtNumber(latest.macd, 3)}
          badge={
            signals.macd_bullish == null ? undefined : (
              <Badge tone={signals.macd_bullish ? "bull" : "bear"}>
                {signals.macd_bullish ? "bullish" : "bearish"}
              </Badge>
            )
          }
          sub={`signal ${fmtNumber(latest.macd_signal, 3)}`}
        />
        <StatTile label="Volatility (30d ann.)" value={fmtPctValue(latest.volatility_30)} />
        <StatTile
          label="Drawdown"
          value={fmtPctValue(latest.drawdown)}
          sub={`max ${fmtPctValue(latest.max_drawdown)}`}
        />
        <StatTile
          label="SMA 30"
          value={fmtCurrency(latest.sma_30, currency)}
          badge={aboveBadge(signals.above_sma_30)}
        />
        <StatTile
          label="SMA 100"
          value={fmtCurrency(latest.sma_100, currency)}
          badge={aboveBadge(signals.above_sma_100)}
        />
        <StatTile label="EMA 20" value={fmtCurrency(latest.ema_20, currency)} />
        <StatTile
          label="Rel. volume"
          value={`${fmtNumber(latest.relative_volume, 2)}×`}
          badge={signals.volume_spike ? <Badge tone="warning">spike</Badge> : undefined}
        />
      </div>
    </Card>
  );
}
