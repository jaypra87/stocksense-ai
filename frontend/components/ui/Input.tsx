import { forwardRef, useId } from "react";

import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  /** Visually hide the label (still announced to screen readers). */
  hideLabel?: boolean;
  error?: string;
}

// Labeled text input with accessible error wiring (aria-invalid + aria-describedby).
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, label, hideLabel = false, error, id, ...props },
  ref,
) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const errorId = `${inputId}-error`;

  return (
    <div className="w-full">
      <label
        htmlFor={inputId}
        className={cn("mb-1.5 block text-sm font-medium", hideLabel && "sr-only")}
      >
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          "h-10 w-full rounded-lg border bg-card px-3 text-sm shadow-sm outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-accent focus:ring-2 focus:ring-ring/40 disabled:opacity-50",
          error ? "border-bearish" : "border-border",
          className,
        )}
        {...props}
      />
      {error && (
        <p id={errorId} role="alert" className="mt-1.5 text-xs text-bearish">
          {error}
        </p>
      )}
    </div>
  );
});
