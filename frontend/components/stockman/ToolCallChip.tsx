"use client";

import { AlertCircle, Check, ChevronDown } from "lucide-react";

import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/utils";
import type { ToolCall } from "@/types/stockman";

const LABELS: Record<string, string> = {
  get_quote: "Quote",
  get_forecast: "Forecast",
  get_risk: "Risk",
  get_sentiment: "Sentiment",
  get_indicators: "Indicators",
  run_backtest: "Backtest",
  get_portfolio: "Portfolio",
  get_watchlist: "Watchlist",
  propose_paper_trade: "Trade idea",
};

function describe(call: ToolCall): string {
  const label = LABELS[call.name] ?? call.name;
  const ticker = typeof call.input.ticker === "string" ? call.input.ticker.toUpperCase() : "";
  const horizon = typeof call.input.horizon === "string" ? call.input.horizon : "";
  return [label, ticker, horizon].filter(Boolean).join(" · ");
}

// Every number in an answer traces back to one of these. The chip shows the
// call while it runs and opens to the raw result once it has landed.
export function ToolCallChip({ call }: { call: ToolCall }) {
  const summary = (
    <>
      {call.status === "running" ? (
        <Spinner className="h-3 w-3" />
      ) : call.status === "error" ? (
        <AlertCircle className="h-3 w-3 text-bearish" aria-hidden />
      ) : (
        <Check className="h-3 w-3 text-bullish" aria-hidden />
      )}
      <span>{describe(call)}</span>
    </>
  );

  if (call.result === undefined) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border border-border bg-background/60 px-2.5 py-1 text-xs font-medium text-muted-foreground",
          call.status === "running" && "animate-pulse border-accent/40 text-foreground",
        )}
      >
        {summary}
      </span>
    );
  }

  return (
    <details className="group inline-block">
      <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 rounded-full border border-border bg-background/60 px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-accent/50 hover:text-foreground [&::-webkit-details-marker]:hidden">
        {summary}
        <ChevronDown className="h-3 w-3 transition-transform group-open:rotate-180" aria-hidden />
      </summary>
      <pre className="mt-2 max-h-56 overflow-auto rounded-lg border border-border bg-background/60 p-3 text-[11px] leading-snug text-muted-foreground">
        {typeof call.result === "string" ? call.result : JSON.stringify(call.result, null, 2)}
      </pre>
    </details>
  );
}
