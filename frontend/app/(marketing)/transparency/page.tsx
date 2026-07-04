"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Database, Layers, ListChecks } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { getModels } from "@/lib/api/models";

export default function TransparencyPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["models"], queryFn: getModels });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <Card className="flex items-center gap-3 border-bearish/40" role="alert">
        <AlertTriangle className="h-5 w-5 shrink-0 text-bearish" aria-hidden />
        <div>
          <p className="font-semibold">Couldn&apos;t load model information</p>
          <p className="text-sm text-muted-foreground">
            The backend may be waking up — try refreshing in a moment.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Model transparency</h1>
        <p className="mt-1 text-muted-foreground">
          How StockSense produces its forecasts — and where it falls short.
        </p>
      </div>

      <Card className="space-y-2">
        <CardTitle className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-accent" aria-hidden /> Methodology
        </CardTitle>
        <p className="text-sm leading-relaxed text-muted-foreground">{data.methodology}</p>
      </Card>

      <Card className="space-y-3">
        <CardTitle className="flex items-center gap-2">
          <Database className="h-4 w-4 text-accent" aria-hidden /> Data sources
        </CardTitle>
        <ul className="space-y-1.5 text-sm text-muted-foreground">
          {data.data_sources.map((s, i) => (
            <li key={i} className="flex gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" aria-hidden />
              {s}
            </li>
          ))}
        </ul>
      </Card>

      <Card className="space-y-3">
        <CardTitle>Trained models</CardTitle>
        {data.models.length === 0 ? (
          <p className="text-sm text-muted-foreground">No models trained yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">
                Trained model versions with accuracy vs baseline
              </caption>
              <thead className="text-left text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Version</th>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Horizon</th>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Accuracy</th>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Baseline</th>
                  <th scope="col" className="py-1.5 pr-4 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.models.map((m, i) => (
                  <tr key={i} className="border-t border-border">
                    <td className="py-2 pr-4 font-mono text-xs">{m.model_version}</td>
                    <td className="py-2 pr-4">{m.horizon}</td>
                    <td className="py-2 pr-4 tabular-nums">
                      {m.metrics.classifier?.accuracy != null
                        ? `${(m.metrics.classifier.accuracy * 100).toFixed(1)}%`
                        : "—"}
                    </td>
                    <td className="py-2 pr-4 tabular-nums text-muted-foreground">
                      {m.metrics.classifier?.baseline_accuracy != null
                        ? `${(m.metrics.classifier.baseline_accuracy * 100).toFixed(1)}%`
                        : "—"}
                    </td>
                    <td className="py-2 pr-4">
                      {m.is_active ? (
                        <Badge tone="bull">active</Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">archived</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card className="space-y-3">
        <CardTitle className="flex items-center gap-2">
          <ListChecks className="h-4 w-4 text-accent" aria-hidden /> Features (
          {data.features.length})
        </CardTitle>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {data.features.map((f) => (
            <div key={f.name} className="text-sm">
              <span className="font-mono text-xs text-accent">{f.name}</span>
              <span className="ml-2 text-muted-foreground">{f.description}</span>
            </div>
          ))}
        </div>
      </Card>

      <Card className="space-y-3 border-warning/40">
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-warning" aria-hidden /> Limitations
        </CardTitle>
        <ul className="space-y-1.5 text-sm text-muted-foreground">
          {data.limitations.map((l, i) => (
            <li key={i} className="flex gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-warning" aria-hidden />
              {l}
            </li>
          ))}
        </ul>
        <p className="border-t border-border pt-3 text-sm font-semibold">{data.disclaimer}</p>
      </Card>
    </div>
  );
}
