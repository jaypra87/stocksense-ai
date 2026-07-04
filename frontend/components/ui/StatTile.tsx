import { cn } from "@/lib/utils";

// Small label/value/sub tile used in indicator grids, backtest metrics, and forecasts.
export function StatTile({
  label,
  value,
  sub,
  badge,
  valueClassName,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  badge?: React.ReactNode;
  valueClassName?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-background/50 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">{label}</span>
        {badge}
      </div>
      <div className={cn("mt-1 text-lg font-semibold tabular-nums", valueClassName)}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}
