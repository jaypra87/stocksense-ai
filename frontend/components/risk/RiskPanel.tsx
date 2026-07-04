"use client";

import { ShieldAlert } from "lucide-react";

import { RiskGauge } from "@/components/risk/RiskGauge";
import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useRisk } from "@/lib/hooks/useStocks";

export function RiskPanel({ ticker }: { ticker: string }) {
  const { data, isLoading, isError } = useRisk(ticker);

  return (
    <Card className="space-y-4">
      <CardTitle className="flex items-center gap-2">
        <ShieldAlert className="h-4 w-4 text-accent" aria-hidden /> Risk Score
      </CardTitle>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : isError || !data ? (
        <p className="text-sm text-muted-foreground">Couldn&apos;t compute risk right now.</p>
      ) : (
        <>
          <RiskGauge score={data.risk_score} level={data.risk_level} />

          <div className="space-y-2.5">
            {data.factors.map((f) => {
              const pct = Math.min(100, Math.max(0, f.score));
              return (
                <div key={f.name}>
                  <div className="flex justify-between text-xs">
                    <span className="capitalize text-muted-foreground">{f.description}</span>
                    <span className="tabular-nums">{Math.round(f.score)}</span>
                  </div>
                  <div
                    role="progressbar"
                    aria-label={f.description}
                    aria-valuenow={Math.round(pct)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted"
                  >
                    <div className="h-full rounded-full bg-accent" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>

          <p className="border-t border-border pt-3 text-xs text-muted-foreground">{data.note}</p>
        </>
      )}
    </Card>
  );
}
