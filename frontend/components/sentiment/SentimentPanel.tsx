"use client";

import { Newspaper } from "lucide-react";

import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useSentiment } from "@/lib/hooks/useStocks";
import { cn } from "@/lib/utils";
import type { SentimentLabel } from "@/types/sentiment";

const LABEL_STYLE: Record<SentimentLabel, { color: string; bg: string; text: string }> = {
  positive: { color: "text-bullish", bg: "bg-bullish/15", text: "Positive" },
  negative: { color: "text-bearish", bg: "bg-bearish/15", text: "Negative" },
  neutral: { color: "text-neutral", bg: "bg-muted", text: "Neutral" },
  mixed: { color: "text-yellow-500", bg: "bg-yellow-500/15", text: "Mixed" },
};

const ITEM_DOT: Record<string, string> = {
  positive: "bg-bullish",
  negative: "bg-bearish",
  neutral: "bg-muted-foreground",
};

export function SentimentPanel({ ticker }: { ticker: string }) {
  const { data, isLoading, isError } = useSentiment(ticker);

  return (
    <Card className="space-y-4">
      <CardTitle className="flex items-center gap-2">
        <Newspaper className="h-4 w-4 text-accent" /> News Sentiment
      </CardTitle>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : isError || !data ? (
        <p className="text-sm text-muted-foreground">Couldn&apos;t load news sentiment.</p>
      ) : data.headline_count === 0 ? (
        <p className="text-sm text-muted-foreground">No recent headlines found.</p>
      ) : (
        <>
          {/* Overall */}
          <div className="flex flex-wrap items-center gap-3">
            <span
              className={cn(
                "rounded-lg px-3 py-1.5 text-lg font-bold",
                LABEL_STYLE[data.overall_label].bg,
                LABEL_STYLE[data.overall_label].color,
              )}
            >
              {LABEL_STYLE[data.overall_label].text}
            </span>
            <div className="text-sm text-muted-foreground">
              <span className="tabular-nums">{data.overall_score >= 0 ? "+" : ""}{data.overall_score.toFixed(2)}</span>{" "}
              score · {data.counts.positive}↑ {data.counts.negative}↓ {data.counts.neutral}–
            </div>
          </div>

          <p className="text-sm text-muted-foreground">{data.summary}</p>

          {/* Headlines */}
          <ul className="space-y-2">
            {data.items.map((it, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span
                  className={cn("mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full", ITEM_DOT[it.label])}
                  title={it.label}
                />
                <div className="min-w-0">
                  {it.url ? (
                    <a
                      href={it.url}
                      target="_blank"
                      rel="noreferrer"
                      className="hover:text-accent hover:underline"
                    >
                      {it.title}
                    </a>
                  ) : (
                    <span>{it.title}</span>
                  )}
                  {it.publisher && (
                    <span className="ml-1 text-xs text-muted-foreground">· {it.publisher}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>

          <p className="border-t border-border pt-3 text-xs text-muted-foreground">{data.note}</p>
        </>
      )}
    </Card>
  );
}
