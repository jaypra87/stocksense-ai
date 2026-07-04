"use client";

import { useQueries } from "@tanstack/react-query";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getHistory } from "@/lib/api/stocks";
import { chartAxisStroke, chartAxisTick, chartTooltipStyle } from "@/lib/chartTheme";

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

  const isLoading = results.some((r) => r.isLoading);
  const loaded = results.filter((r) => r.data);
  const failed = tickers.filter((_, i) => results[i].isError);

  // Rebase each ticker's closes to 100 at its first point, then merge by date.
  const byDate: Record<string, Record<string, number>> = {};
  results.forEach((r, idx) => {
    const candles = r.data?.candles;
    if (!candles || candles.length === 0) return;
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

  if (isLoading) {
    return (
      <div className="py-10 text-center text-sm text-muted-foreground" aria-live="polite">
        Loading comparison…
      </div>
    );
  }

  if (loaded.length === 0) {
    return (
      <div className="py-10 text-center text-sm text-muted-foreground">
        Couldn&apos;t load history for these tickers.
      </div>
    );
  }

  return (
    <div>
      {failed.length > 0 && (
        <p className="mb-2 text-xs text-muted-foreground">
          No history available for: {failed.join(", ")}
        </p>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
          <XAxis dataKey="date" tick={chartAxisTick} stroke={chartAxisStroke} minTickGap={48} />
          <YAxis
            tick={chartAxisTick}
            stroke={chartAxisStroke}
            width={40}
            domain={["auto", "auto"]}
          />
          <Tooltip contentStyle={chartTooltipStyle} />
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
    </div>
  );
}
