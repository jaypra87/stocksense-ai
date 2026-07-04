"use client";

import { cn } from "@/lib/utils";

export interface SegmentedControlProps<T extends string> {
  options: readonly T[];
  value: T;
  onChange: (value: T) => void;
  /** Accessible group label, e.g. "Chart range". */
  label: string;
  labels?: Partial<Record<T, string>>;
}

// Shared tab-style toggle group (chart ranges, forecast horizons, themes…).
export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  label,
  labels,
}: SegmentedControlProps<T>) {
  return (
    <div role="group" aria-label={label} className="flex flex-wrap gap-1 rounded-lg bg-muted p-1">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => onChange(opt)}
          aria-pressed={opt === value}
          className={cn(
            "rounded-md px-2.5 py-1 text-xs font-semibold uppercase tracking-wide transition-colors",
            opt === value
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground",
          )}
        >
          {labels?.[opt] ?? opt}
        </button>
      ))}
    </div>
  );
}
