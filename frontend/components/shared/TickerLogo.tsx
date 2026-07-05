"use client";

import Image from "next/image";
import { useState } from "react";

import { cn } from "@/lib/utils";

// Company logo for a ticker, served by parqet's public logo CDN. Falls back
// to a monogram tile when no logo exists (indexes, foreign listings, etc.).
// Decorative only — the ticker text is always rendered next to it.

const SIZE_PX = { sm: 24, md: 32, lg: 40 } as const;

export function TickerLogo({
  ticker,
  size = "md",
  className,
}: {
  ticker: string;
  size?: keyof typeof SIZE_PX;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);
  const px = SIZE_PX[size];
  // Strip exchange suffixes (VFV.TO, BRK-B) — the CDN indexes plain symbols.
  const symbol = ticker.split(/[.-]/)[0];

  if (failed || !symbol) {
    return (
      <span
        aria-hidden
        style={{ width: px, height: px }}
        className={cn(
          "flex shrink-0 items-center justify-center rounded-full border border-border bg-muted font-bold text-muted-foreground",
          size === "sm" ? "text-[9px]" : size === "md" ? "text-[11px]" : "text-xs",
          className,
        )}
      >
        {symbol.slice(0, 2) || "?"}
      </span>
    );
  }

  return (
    <Image
      src={`https://assets.parqet.com/logos/symbol/${encodeURIComponent(symbol)}?format=png`}
      alt=""
      width={px}
      height={px}
      onError={() => setFailed(true)}
      className={cn("shrink-0 rounded-full border border-border bg-white object-contain", className)}
    />
  );
}
