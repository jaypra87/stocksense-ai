"use client";

import {
  Area,
  Bar,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { fmtCompact, fmtCurrency } from "@/lib/format";
import type { History, Range } from "@/types/stock";

// Range-aware tick labels: intraday shows time, short ranges show month/day,
// and long ranges show the year so labels can't be mistaken for day-of-month.
function formatAxisDate(ts: number, range: Range): string {
  const d = new Date(ts);
  switch (range) {
    case "1d":
      return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
    case "5d":
    case "1m":
    case "6m":
    case "ytd":
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    case "1y":
      return d.toLocaleDateString("en-US", { month: "short", year: "numeric" });
    case "5y":
      return d.toLocaleDateString("en-US", { year: "numeric" });
    default:
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }
}

export function PriceChart({
  history,
  range,
  currency = "USD",
}: {
  history: History;
  range: Range;
  currency?: string;
}) {
  const data = history.candles.map((c) => ({
    t: new Date(c.timestamp).getTime(),
    c: c.close,
    v: c.volume ?? 0,
  }));

  if (data.length === 0) {
    return (
      <div className="flex h-[360px] items-center justify-center text-sm text-muted-foreground">
        No price data for this range.
      </div>
    );
  }

  // Color the chart by overall direction across the visible range.
  const up = data[data.length - 1].c >= data[0].c;
  const color = up ? "hsl(var(--bullish))" : "hsl(var(--bearish))";
  const maxVol = Math.max(...data.map((d) => d.v));

  return (
    <ResponsiveContainer width="100%" height={360}>
      <ComposedChart data={data} margin={{ top: 10, right: 8, bottom: 0, left: 8 }}>
        <defs>
          <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>

        <XAxis
          dataKey="t"
          type="number"
          domain={["dataMin", "dataMax"]}
          scale="time"
          tickFormatter={(t) => formatAxisDate(t, range)}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          stroke="hsl(var(--border))"
          minTickGap={40}
        />
        <YAxis
          yAxisId="price"
          orientation="right"
          domain={["auto", "auto"]}
          tickFormatter={(v) => fmtCurrency(v, currency)}
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          stroke="hsl(var(--border))"
          width={70}
        />
        {/* Hidden axis scales volume bars to the lower ~25% of the chart. */}
        <YAxis yAxisId="vol" hide domain={[0, maxVol * 4]} />

        <Tooltip
          contentStyle={{
            background: "hsl(var(--background))",
            border: "1px solid hsl(var(--border))",
            borderRadius: 8,
            fontSize: 12,
          }}
          labelFormatter={(t) => new Date(Number(t)).toLocaleString()}
          formatter={(value: number, name: string) =>
            name === "Price"
              ? [fmtCurrency(value, currency), "Price"]
              : [fmtCompact(value), "Volume"]
          }
        />

        <Bar
          yAxisId="vol"
          dataKey="v"
          name="Volume"
          fill="hsl(var(--muted-foreground))"
          opacity={0.25}
          isAnimationActive={false}
        />
        <Area
          yAxisId="price"
          type="monotone"
          dataKey="c"
          name="Price"
          stroke={color}
          strokeWidth={2}
          fill="url(#priceFill)"
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
