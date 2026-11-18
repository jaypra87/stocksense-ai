"use client";

import { AlertCircle, RotateCcw } from "lucide-react";

import { Reveal } from "@/components/shared/Reveal";
import { Markdown } from "@/components/stockman/Markdown";
import { StockmanMark } from "@/components/stockman/StockmanMark";
import { Card, CardTitle } from "@/components/ui/Card";
import { useToast } from "@/components/ui/Toast";
import { useDigest, useRefreshDigest } from "@/lib/hooks/useStockman";
import { cn } from "@/lib/utils";
import type { DigestSource } from "@/types/stockman";

const TOOL_LABELS: Record<string, string> = {
  get_portfolio: "Portfolio",
  get_risk: "Risk",
  get_sentiment: "Sentiment",
  get_forecast: "7d forecast",
};

// Stock-man's note for the day, written on the first visit and cached. When
// he is offline or out of budget the card stays off the dashboard rather
// than explaining itself; the chat dock already says so.
export function DigestCard() {
  const digest = useDigest();
  const refresh = useRefreshDigest();
  const { toast } = useToast();

  if (digest.isError) return null;
  if (digest.data && !digest.data.available) return null;

  const writing = digest.isLoading || refresh.isPending;
  const data = digest.data;
  const unmatched = data?.grounding?.unmatched ?? [];

  function onRefresh() {
    refresh.mutate(undefined, {
      onError: () => toast("Couldn't rewrite the digest right now", "error"),
    });
  }

  return (
    <Reveal>
      <Card className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="flex items-center gap-2">
            <StockmanMark /> Today&apos;s digest
            {data?.for_date && (
              <span className="font-normal normal-case tracking-normal">
                ·{" "}
                {new Date(`${data.for_date}T12:00:00`).toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                })}
              </span>
            )}
          </CardTitle>
          {data && (
            <button
              type="button"
              onClick={onRefresh}
              disabled={writing}
              aria-label="Rewrite today's digest"
              title="Rewrite with the latest numbers"
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-50"
            >
              <RotateCcw className={cn("h-4 w-4", writing && "animate-spin")} aria-hidden />
            </button>
          )}
        </div>

        {writing ? (
          <div className="space-y-2.5" aria-live="polite">
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="flex items-center gap-1" aria-hidden>
                <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
                <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
              </span>
              Stock-man is writing today&apos;s digest…
            </p>
            <div className="h-3 w-11/12 animate-pulse rounded bg-muted" />
            <div className="h-3 w-full animate-pulse rounded bg-muted" />
            <div className="h-3 w-3/4 animate-pulse rounded bg-muted" />
          </div>
        ) : data?.body ? (
          <>
            <div className="text-sm">
              <Markdown text={data.body} />
            </div>
            {data.sources.length > 0 && (
              <ul className="flex flex-wrap gap-1.5" aria-label="Sources">
                {data.sources.map((s) => (
                  <li
                    key={sourceKey(s)}
                    className="rounded-full border border-border bg-background/60 px-2 py-0.5 text-[11px] font-medium text-muted-foreground"
                  >
                    {TOOL_LABELS[s.tool] ?? s.tool}
                    {s.ticker ? ` · ${s.ticker}` : ""}
                  </li>
                ))}
              </ul>
            )}
            {unmatched.length > 0 && (
              <p className="flex items-start gap-1.5 text-xs text-warning">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
                {unmatched.length === 1 ? "One figure" : `${unmatched.length} figures`} here
                couldn&apos;t be traced to a tool result: {unmatched.join(", ")}.
              </p>
            )}
            <p className="border-t border-border pt-3 text-xs text-muted-foreground">
              {data.disclaimer}
            </p>
          </>
        ) : null}
      </Card>
    </Reveal>
  );
}

function sourceKey(s: DigestSource): string {
  return `${s.tool}:${s.ticker ?? ""}`;
}
