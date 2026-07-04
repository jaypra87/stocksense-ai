"use client";

import { Bell, BellOff, Pause, Play, Trash2 } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";
import { useAlertEvents, useAlertMutations, useAlerts } from "@/lib/hooks/useAlerts";
import { ALERT_TYPE_LABELS, type AlertType } from "@/types/alert";

export default function AlertsPage() {
  const alerts = useAlerts();
  const events = useAlertEvents();
  const { create, update, remove } = useAlertMutations();
  const { toast } = useToast();

  const [ticker, setTicker] = useState("");
  const [alertType, setAlertType] = useState<AlertType>("price_above");
  const [threshold, setThreshold] = useState("");

  function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker || threshold === "") return;
    create.mutate(
      { ticker: ticker.toUpperCase(), alertType, threshold: Number(threshold) },
      {
        onSuccess: () => {
          setTicker("");
          setThreshold("");
          toast("Alert created");
        },
        onError: () => toast("Couldn't create the alert — check the ticker and try again", "error"),
      },
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Alerts</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Rules are checked on a schedule; triggered alerts appear below.
        </p>
      </div>

      {/* Create */}
      <Card>
        <CardTitle>New alert</CardTitle>
        <form onSubmit={onCreate} className="mt-4 flex flex-wrap items-end gap-3">
          <div className="w-36">
            <Input
              label="Ticker"
              placeholder="e.g. NVDA"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
            />
          </div>
          <Select
            label="Condition"
            value={alertType}
            onChange={(e) => setAlertType(e.target.value as AlertType)}
          >
            {(Object.keys(ALERT_TYPE_LABELS) as AlertType[]).map((t) => (
              <option key={t} value={t}>
                {ALERT_TYPE_LABELS[t]}
              </option>
            ))}
          </Select>
          <div className="w-32">
            <Input
              label="Threshold"
              type="number"
              step="any"
              placeholder="0.00"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
          </div>
          <Button type="submit" loading={create.isPending}>
            Create alert
          </Button>
        </form>
      </Card>

      {/* Active alerts */}
      <Card className="space-y-3">
        <CardTitle>Your alerts</CardTitle>
        {alerts.isLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : !alerts.data || alerts.data.length === 0 ? (
          <div className="flex items-center gap-3 rounded-lg border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">
            <BellOff className="h-4 w-4 shrink-0" aria-hidden />
            No alerts yet — create one above to get notified when a rule triggers.
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {alerts.data.map((a) => (
              <li key={a.id} className="flex items-center justify-between gap-3 py-2.5">
                <div className="text-sm">
                  <span className="font-semibold">{a.ticker}</span>{" "}
                  <span className="text-muted-foreground">
                    {ALERT_TYPE_LABELS[a.alert_type]} {a.threshold}
                  </span>
                  {!a.active && (
                    <Badge tone="neutral" className="ml-2">
                      paused
                    </Badge>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() =>
                      update.mutate(
                        { id: a.id, changes: { active: !a.active } },
                        {
                          onError: () => toast("Couldn't update the alert", "error"),
                        },
                      )
                    }
                    aria-label={
                      a.active ? `Pause alert for ${a.ticker}` : `Resume alert for ${a.ticker}`
                    }
                    className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    {a.active ? (
                      <Pause className="h-4 w-4" aria-hidden />
                    ) : (
                      <Play className="h-4 w-4" aria-hidden />
                    )}
                  </button>
                  <button
                    onClick={() =>
                      remove.mutate(a.id, {
                        onSuccess: () => toast("Alert deleted"),
                        onError: () => toast("Couldn't delete the alert", "error"),
                      })
                    }
                    aria-label={`Delete alert for ${a.ticker}`}
                    className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-bearish"
                  >
                    <Trash2 className="h-4 w-4" aria-hidden />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* Triggered history */}
      <Card className="space-y-3">
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-accent" aria-hidden /> Triggered history
        </CardTitle>
        {events.isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : !events.data || events.data.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nothing triggered yet.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {events.data.map((e) => (
              <li key={e.id} className="flex items-start gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" aria-hidden />
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
