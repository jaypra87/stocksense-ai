"use client";

import { useQueries } from "@tanstack/react-query";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getHistory } from "@/lib/api/stocks";

// Distinct line colors for up to ~6 tickers.
const COLORS = [
  "hsl(var(--accent))",
  "hsl(var(--bullish))",
  "hsl(var(--bearish))",
  "#f59e0b",
  "#a855f7",
  "#06b6d4",
];

export function CompareChart({ tickers }: { tickers: string[] }) {
  const results = useQueries({
    queries: tickers.map((t) => ({
      queryKey: ["history", t, "6m"],
      queryFn: () => getHistory(t, "6m" as const),
    })),
  });

  const ready = results.every((r) => r.data);
  if (!ready) {
    return <div className="py-10 text-center text-sm text-muted-foreground">Loading comparison…</div>;
  }

  // Rebase each ticker's closes to 100 at its first point, then merge by date.
  const byDate: Record<string, Record<string, number>> = {};
  results.forEach((r, idx) => {
    const candles = r.data!.candles;
    if (candles.length === 0) return;
    const base = candles[0].close;
    for (const c of candles) {
      const day = c.timestamp.slice(0, 10);
      byDate[day] ??= {};
      byDate[day][tickers[idx]] = Number(((c.close / base) * 100).toFixed(2));
    }
  });

  const data = Object.keys(byDate)
    .sort()
    .map((date) => ({ date, ...byDate[date] }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          stroke="hsl(var(--border))"
          minTickGap={48}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
          stroke="hsl(var(--border))"
          width={40}
          domain={["auto", "auto"]}
        />
        <Tooltip
          contentStyle={{
            background: "hsl(var(--background))",
            border: "1px solid hsl(var(--border))",
            borderRadius: 8,
            fontSize: 12,
          }}
        />
        {tickers.map((t, idx) => (
          <Line
            key={t}
            type="monotone"
            dataKey={t}
            stroke={COLORS[idx % COLORS.length]}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
