"use client";

import { cn } from "@/lib/utils";
import type { Range } from "@/types/stock";

const RANGES: Range[] = ["1d", "5d", "1m", "6m", "ytd", "1y", "5y"];

export function RangeSelector({
  value,
  onChange,
}: {
  value: Range;
  onChange: (r: Range) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1">
      {RANGES.map((r) => (
        <button
          key={r}
          type="button"
          onClick={() => onChange(r)}
          className={cn(
            "rounded-md px-3 py-1 text-xs font-semibold uppercase transition-colors",
            r === value
              ? "bg-accent text-accent-foreground"
              : "text-muted-foreground hover:bg-muted hover:text-foreground",
          )}
        >
          {r}
        </button>
      ))}
    </div>
  );
}
