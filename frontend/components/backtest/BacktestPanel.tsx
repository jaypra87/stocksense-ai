"use client";

import { FlaskConical } from "lucide-react";
import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardTitle } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { useRunBacktest } from "@/lib/hooks/useBacktest";
import { cn } from "@/lib/utils";
import type { Backtest, Horizon } from "@/types/backtest";

const HORIZONS: Horizon[] = ["1d", "7d", "30d"];

export function BacktestPanel({ ticker }: { ticker: string }) {
  const [horizon, setHorizon] = useState<Horizon>("7d");
  const { mutate, data, isPending, isError, error } = useRunBacktest();

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2">
          <FlaskConical className="h-4 w-4 text-accent" /> Backtesting
        </CardTitle>
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            {HORIZONS.map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={cn(
                  "rounded-md px-2.5 py-1 text-xs font-semibold uppercase transition-colors",
                  h === horizon
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-muted",
                )}
              >
                {h}
              </button>
            ))}
          </div>
          <button
            onClick={() => mutate({ ticker, horizon })}
            disabled={isPending}
            className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-sm font-semibold text-accent-foreground hover:opacity-90 disabled:opacity-50"
          >
            {isPending && <Spinner />}
            Run backtest
          </button>
        </div>
      </div>

      {isPending ? (
        <p className="text-sm text-muted-foreground">
          Running walk-forward backtest — training the model across history…
        </p>
      ) : isError ? (
        <p className="text-sm text-muted-foreground">
          {(error as { status?: number })?.status === 422
            ? "Not enough history for this horizon."
            : "Couldn't run the backtest."}
        </p>
      ) : data ? (
        <Results data={data} />
      ) : (
        <p className="text-sm text-muted-foreground">
          Test how this model would have performed historically, vs. naive baselines.
        </p>
      )}
    </Card>
  );
}

function Stat({ label, value, sub, good }: { label: string; value: string; sub?: string; good?: boolean }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={cn("text-lg font-semibold tabular-nums", good === true && "text-bullish", good === false && "text-bearish")}>
        {value}
      </div>
      {sub && <div className="text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

function Results({ data }: { data: Backtest }) {
  const m = data.metrics;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat
          label="Directional accuracy"
          value={`${m.directional_accuracy}%`}
          sub={`baseline ${m.baseline_accuracy}%`}
          good={m.beats_baseline}
        />
        <Stat label="MAE (return)" value={m.mae.toFixed(4)} sub={`baseline ${m.baseline_mae.toFixed(4)}`} />
        <Stat label="RMSE" value={m.rmse.toFixed(4)} />
        <Stat label="Predictions" value={String(m.n_predictions)} sub={`${data.start_date} → ${data.end_date}`} />
      </div>

      <div>
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Strategy vs buy &amp; hold (cumulative %)
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data.chart_data.equity} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.4} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              stroke="hsl(var(--border))"
              minTickGap={48}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              stroke="hsl(var(--border))"
              width={44}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={{
                background: "hsl(var(--background))",
                border: "1px solid hsl(var(--border))",
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(v: number, name: string) => [`${v}%`, name === "model" ? "Model" : "Buy & hold"]}
            />
            <Line type="monotone" dataKey="buy_hold" stroke="hsl(var(--muted-foreground))" strokeWidth={2} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="model" stroke="hsl(var(--accent))" strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className={cn("rounded-lg px-3 py-2 text-sm", m.beats_baseline ? "bg-bullish/10 text-bullish" : "bg-muted text-muted-foreground")}>
        {m.beats_baseline
          ? "The model beat the naive baseline on directional accuracy over this period."
          : "The model did not beat the naive baseline here — a reminder that markets are hard to predict."}
      </div>

      <p className="border-t border-border pt-3 text-xs text-muted-foreground">
        {data.note}
        <br />
        <span className="font-semibold">{data.disclaimer}</span>
      </p>
    </div>
  );
}
