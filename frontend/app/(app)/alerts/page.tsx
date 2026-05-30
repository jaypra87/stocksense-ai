"use client";

import { Bell, Pause, Play, Trash2 } from "lucide-react";
import { useState } from "react";

import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAlertEvents, useAlertMutations, useAlerts } from "@/lib/hooks/useAlerts";
import { cn } from "@/lib/utils";
import { ALERT_TYPE_LABELS, type AlertType } from "@/types/alert";

export default function AlertsPage() {
  const alerts = useAlerts();
  const events = useAlertEvents();
  const { create, update, remove } = useAlertMutations();

  const [ticker, setTicker] = useState("");
  const [alertType, setAlertType] = useState<AlertType>("price_above");
  const [threshold, setThreshold] = useState("");

  function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker || threshold === "") return;
    create.mutate(
      { ticker: ticker.toUpperCase(), alertType, threshold: Number(threshold) },
      { onSuccess: () => { setTicker(""); setThreshold(""); } },
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Alerts</h1>
        <p className="text-sm text-muted-foreground">
          Rules are checked on a schedule; triggered alerts appear below.
        </p>
      </div>

      {/* Create */}
      <Card>
        <CardTitle>New alert</CardTitle>
        <form onSubmit={onCreate} className="mt-3 flex flex-wrap items-end gap-3">
          <input
            placeholder="Ticker (e.g. NVDA)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            className="w-32 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent"
          />
          <select
            value={alertType}
            onChange={(e) => setAlertType(e.target.value as AlertType)}
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent"
          >
            {(Object.keys(ALERT_TYPE_LABELS) as AlertType[]).map((t) => (
              <option key={t} value={t}>
                {ALERT_TYPE_LABELS[t]}
              </option>
            ))}
          </select>
          <input
            type="number"
            step="any"
            placeholder="Threshold"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            className="w-28 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-accent"
          />
          <button
            type="submit"
            disabled={create.isPending}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-accent-foreground transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            Create
          </button>
        </form>
      </Card>

      {/* Active alerts */}
      <Card className="space-y-3">
        <CardTitle>Your alerts</CardTitle>
        {alerts.isLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : !alerts.data || alerts.data.length === 0 ? (
          <p className="text-sm text-muted-foreground">No alerts yet.</p>
        ) : (
          <div className="divide-y divide-border">
            {alerts.data.map((a) => (
              <div key={a.id} className="flex items-center justify-between gap-3 py-2.5">
                <div className="text-sm">
                  <span className="font-semibold">{a.ticker}</span>{" "}
                  <span className="text-muted-foreground">
                    {ALERT_TYPE_LABELS[a.alert_type]} {a.threshold}
                  </span>
                  {!a.active && (
                    <span className="ml-2 rounded bg-muted px-1.5 py-0.5 text-xs">paused</span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => update.mutate({ id: a.id, changes: { active: !a.active } })}
                    className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
                    title={a.active ? "Pause" : "Resume"}
                  >
                    {a.active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  </button>
                  <button
                    onClick={() => remove.mutate(a.id)}
                    className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-bearish"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Triggered history */}
      <Card className="space-y-3">
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-accent" /> Triggered history
        </CardTitle>
        {events.isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : !events.data || events.data.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nothing triggered yet.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {events.data.map((e) => (
              <li key={e.id} className="flex items-start gap-2">
                <span className={cn("mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent")} />
                <span>
                  {e.payload.message}
                  {e.triggered_at && (
                    <span className="ml-2 text-xs text-muted-foreground">
                      {new Date(e.triggered_at).toLocaleString()}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
