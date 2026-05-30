"use client";

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
import { fmtNumber } from "@/lib/format";
import type { Indicators } from "@/types/indicator";
import type { Range } from "@/types/stock";

const INTRADAY = ["1d", "5d"];

export function RSIChart({ data, range }: { data: Indicators; range: Range }) {
  const points = data.series
    .filter((p) => p.rsi_14 != null)
    .map((p) => ({ t: new Date(p.timestamp).getTime(), rsi: p.rsi_14 as number }));

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
                day: INTRADAY.includes(range) ? "numeric" : undefined,
              })
            }
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            stroke="hsl(var(--border))"
            minTickGap={40}
          />
          <YAxis
            domain={[0, 100]}
            ticks={[0, 30, 50, 70, 100]}
            tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            stroke="hsl(var(--border))"
            width={28}
          />
          {/* Overbought / oversold guide lines. */}
          <ReferenceLine y={70} stroke="hsl(var(--bearish))" strokeDasharray="3 3" />
          <ReferenceLine y={30} stroke="hsl(var(--bullish))" strokeDasharray="3 3" />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--background))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
            }}
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
