import { forwardRef, useId } from "react";

import { cn } from "@/lib/utils";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  hideLabel?: boolean;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { className, label, hideLabel = false, id, children, ...props },
  ref,
) {
  const autoId = useId();
  const selectId = id ?? autoId;

  return (
    <div>
      <label
        htmlFor={selectId}
        className={cn("mb-1.5 block text-sm font-medium", hideLabel && "sr-only")}
      >
        {label}
      </label>
      <select
        ref={ref}
        id={selectId}
        className={cn(
          "h-10 rounded-lg border border-border bg-card px-3 text-sm shadow-sm outline-none transition-colors focus:border-accent focus:ring-2 focus:ring-ring/40 disabled:opacity-50",
          className,
        )}
        {...props}
      >
        {children}
      </select>
    </div>
  );
});
