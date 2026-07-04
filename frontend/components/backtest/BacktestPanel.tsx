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

import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { StatTile } from "@/components/ui/StatTile";
import { ApiError } from "@/lib/api/client";
import { chartAxisStroke, chartAxisTick, chartTooltipStyle } from "@/lib/chartTheme";
import { useRunBacktest } from "@/lib/hooks/useBacktest";
import { cn } from "@/lib/utils";
import type { Backtest, Horizon } from "@/types/backtest";

const HORIZONS: readonly Horizon[] = ["1d", "7d", "30d"];

export function BacktestPanel({ ticker }: { ticker: string }) {
  const [horizon, setHorizon] = useState<Horizon>("7d");
  const { mutate, data, isPending, isError, error } = useRunBacktest();

  return (
    <Card className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2">
          <FlaskConical className="h-4 w-4 text-accent" aria-hidden /> Backtesting
        </CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          <SegmentedControl
            options={HORIZONS}
            value={horizon}
            onChange={setHorizon}
            label="Backtest horizon"
          />
          <Button size="sm" loading={isPending} onClick={() => mutate({ ticker, horizon })}>
            Run backtest
          </Button>
        </div>
      </div>

      {isPending ? (
        <p aria-live="polite" className="text-sm text-muted-foreground">
          Running walk-forward backtest — training the model across history…
        </p>
      ) : isError ? (
        <p className="text-sm text-muted-foreground">
          {error instanceof ApiError && error.status === 422
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

function Results({ data }: { data: Backtest }) {
  const m = data.metrics;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatTile
          label="Directional accuracy"
          value={`${m.directional_accuracy}%`}
          sub={`baseline ${m.baseline_accuracy}%`}
          valueClassName={m.beats_baseline ? "text-bullish" : "text-bearish"}
        />
        <StatTile
          label="MAE (return)"
          value={m.mae.toFixed(4)}
          sub={`baseline ${m.baseline_mae.toFixed(4)}`}
        />
        <StatTile label="RMSE" value={m.rmse.toFixed(4)} />
        <StatTile
          label="Predictions"
          value={String(m.n_predictions)}
          sub={`${data.start_date} → ${data.end_date}`}
        />
      </div>

      <div>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Strategy vs buy &amp; hold (cumulative %)
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data.chart_data.equity} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={chartAxisStroke} opacity={0.4} />
            <XAxis dataKey="date" tick={chartAxisTick} stroke={chartAxisStroke} minTickGap={48} />
            <YAxis
              tick={chartAxisTick}
              stroke={chartAxisStroke}
              width={44}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              contentStyle={chartTooltipStyle}
              formatter={(v: number, name: string) => [
                `${v}%`,
                name === "model" ? "Model" : "Buy & hold",
              ]}
            />
            <Line
              type="monotone"
              dataKey="buy_hold"
              stroke="hsl(var(--muted-foreground))"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="model"
              stroke="hsl(var(--accent))"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div
        className={cn(
          "rounded-lg px-3 py-2 text-sm",
          m.beats_baseline ? "bg-bullish/10 text-bullish" : "bg-muted text-muted-foreground",
        )}
      >
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
