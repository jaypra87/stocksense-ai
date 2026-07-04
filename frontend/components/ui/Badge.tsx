import { cn } from "@/lib/utils";

export type BadgeTone = "bull" | "bear" | "warning" | "accent" | "neutral";

const TONE_CLASSES: Record<BadgeTone, string> = {
  bull: "bg-bullish/15 text-bullish",
  bear: "bg-bearish/15 text-bearish",
  warning: "bg-warning/15 text-warning",
  accent: "bg-accent/15 text-accent",
  neutral: "bg-muted text-muted-foreground",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold",
        TONE_CLASSES[tone],
        className,
      )}
      {...props}
    />
  );
}
