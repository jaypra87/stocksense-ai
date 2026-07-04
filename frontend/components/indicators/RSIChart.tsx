"use client";

import { useMemo } from "react";
import {
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardTitle } from "@/components/ui/Card";
import { chartAxisStroke, chartAxisTick, chartTooltipStyle } from "@/lib/chartTheme";
import { fmtNumber } from "@/lib/format";
import type { Indicators } from "@/types/indicator";
import type { Range } from "@/types/stock";

// Ranges long enough that ticks need the year to stay unambiguous.
const LONG_RANGES: Range[] = ["1y", "5y"];

export function RSIChart({ data, range }: { data: Indicators; range: Range }) {
  const points = useMemo(
    () =>
      data.series
        .filter((p) => p.rsi_14 != null)
        .map((p) => ({ t: new Date(p.timestamp).getTime(), rsi: p.rsi_14 as number })),
    [data],
  );

  if (points.length === 0) return null;

  return (
    <Card className="space-y-3">
      <CardTitle>RSI (14)</CardTitle>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
          <XAxis
            dataKey="t"
            type="number"
            domain={["dataMin", "dataMax"]}
            scale="time"
            tickFormatter={(t) =>
              new Date(t).toLocaleDateString("en-US", {
                month: "short",
                day: LONG_RANGES.includes(range) ? undefined : "numeric",
                year: LONG_RANGES.includes(range) ? "numeric" : undefined,
              })
            }
            tick={chartAxisTick}
            stroke={chartAxisStroke}
            minTickGap={40}
          />
          <YAxis
            domain={[0, 100]}
            ticks={[0, 30, 50, 70, 100]}
            tick={chartAxisTick}
            stroke={chartAxisStroke}
            width={28}
          />
          {/* Overbought / oversold guide lines. */}
          <ReferenceLine y={70} stroke="hsl(var(--bearish))" strokeDasharray="3 3" />
          <ReferenceLine y={30} stroke="hsl(var(--bullish))" strokeDasharray="3 3" />
          <Tooltip
            contentStyle={chartTooltipStyle}
            labelFormatter={(t) => new Date(Number(t)).toLocaleDateString()}
            formatter={(v: number) => [fmtNumber(v, 1), "RSI"]}
          />
          <Line
            type="monotone"
            dataKey="rsi"
            stroke="hsl(var(--accent))"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
