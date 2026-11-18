"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { chartTooltipStyle } from "@/lib/chartTheme";
import { fmtCurrency, fmtNumber } from "@/lib/format";
import type { Portfolio } from "@/types/portfolio";

const COLORS = [
  "hsl(var(--accent))",
  "hsl(var(--bullish))",
  "hsl(var(--warning))",
  "#a855f7",
  "#06b6d4",
  "#f43f5e",
  "#84cc16",
  "#f97316",
];
const CASH_COLOR = "hsl(var(--muted-foreground))";

export function AllocationChart({ portfolio }: { portfolio: Portfolio }) {
  const slices = [
    ...portfolio.positions.map((p, i) => ({
      name: p.ticker,
      value: p.market_value,
      weight: p.weight,
      color: COLORS[i % COLORS.length],
    })),
    {
      name: "Cash",
      value: portfolio.cash,
      weight: portfolio.equity > 0 ? (portfolio.cash / portfolio.equity) * 100 : 100,
      color: CASH_COLOR,
    },
  ].filter((s) => s.value > 0);

  return (
    <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
      <div className="relative h-44 w-44 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={slices}
              dataKey="value"
              nameKey="name"
              innerRadius={58}
              outerRadius={82}
              paddingAngle={slices.length > 1 ? 2 : 0}
              stroke="none"
              animationDuration={700}
              animationEasing="ease-out"
            >
              {slices.map((s) => (
                <Cell key={s.name} fill={s.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(value: number) => fmtCurrency(value)}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Equity</span>
          <span className="text-sm font-bold tabular-nums">{fmtCurrency(portfolio.equity)}</span>
        </div>
      </div>

      <ul className="w-full space-y-1.5 text-sm">
        {slices.map((s) => (
          <li key={s.name} className="flex items-center gap-2">
            <span
              aria-hidden
              className="h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ background: s.color }}
            />
            <span className="font-medium">{s.name}</span>
            <span className="ml-auto tabular-nums text-muted-foreground">
              {fmtNumber(s.weight, 1)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
