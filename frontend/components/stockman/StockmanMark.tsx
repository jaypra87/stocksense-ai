import { Bot } from "lucide-react";

import { cn } from "@/lib/utils";

const SIZES = { sm: "h-7 w-7 [&>svg]:h-4 [&>svg]:w-4", md: "h-9 w-9 [&>svg]:h-5 [&>svg]:w-5" };

// Stock-man's face: the same accent tile the logo uses, so he reads as part
// of the product rather than a third-party widget.
export function StockmanMark({
  size = "sm",
  className,
}: {
  size?: "sm" | "md";
  className?: string;
}) {
  return (
    <span
      aria-hidden
      className={cn(
        "flex shrink-0 items-center justify-center rounded-full bg-accent/15 text-accent",
        SIZES[size],
        className,
      )}
    >
      <Bot />
    </span>
  );
}
