"use client";

import { useQueries } from "@tanstack/react-query";
import Link from "next/link";

import { POPULAR } from "@/components/stock/PopularTickers";
import { Reveal } from "@/components/shared/Reveal";
import { TickerLogo } from "@/components/shared/TickerLogo";
import { Skeleton } from "@/components/ui/Skeleton";
import { getSentiment } from "@/lib/api/stocks";
import { useWatchlist } from "@/lib/hooks/useWatchlist";
import { cn } from "@/lib/utils";
import type { Sentiment } from "@/types/sentiment";

// Latest headlines across the user's most relevant tickers — their watchlist
// when it has entries, popular tickers otherwise. Reuses the per-ticker
// sentiment endpoint (and its React Query cache key) rather than adding a
// backend aggregate.

const TICKER_COUNT = 4;
const HEADLINES_PER_TICKER = 3;
const MAX_HEADLINES = 8;

const LABEL_DOT: Record<string, string> = {
  positive: "bg-bullish",
  negative: "bg-bearish",
  neutral: "bg-muted-foreground",
};

type Headline = Sentiment["items"][number] & { ticker: string };

export function MarketNews() {
  const watchlist = useWatchlist();
  const saved = (watchlist.data ?? []).map((w) => w.ticker);
  const tickers = (saved.length > 0 ? saved : POPULAR.map((p) => p.symbol)).slice(
    0,
    TICKER_COUNT,
  );

  const results = useQueries({
    queries: tickers.map((ticker) => ({
      queryKey: ["sentiment", ticker],
      queryFn: () => getSentiment(ticker),
      staleTime: 15 * 60 * 1000, // matches backend's 15min cache
      enabled: !watchlist.isLoading,
    })),
  });

  const isLoading = watchlist.isLoading || results.some((r) => r.isLoading);
  const headlines: Headline[] = results
    .flatMap((r, i) =>
      (r.data?.items ?? [])
        .slice(0, HEADLINES_PER_TICKER)
        .map((item) => ({ ...item, ticker: tickers[i] })),
    )
    .sort((a, b) => (b.published_at ?? "").localeCompare(a.published_at ?? ""))
    .slice(0, MAX_HEADLINES);

  return (
    <section aria-labelledby="market-news-heading">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2
          id="market-news-heading"
          className="text-xs font-semibold uppercase tracking-wider text-muted-foreground"
        >
          Latest market news
        </h2>
        <span className="text-xs text-muted-foreground">
          {saved.length > 0 ? "From your watchlist" : "From popular tickers"}
        </span>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : headlines.length === 0 ? (
        <p className="rounded-xl border border-dashed border-border px-4 py-5 text-sm text-muted-foreground">
          No recent headlines for {tickers.join(", ")}.
        </p>
      ) : (
        <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-card shadow-sm dark:shadow-none">
          {headlines.map((h, i) => (
            <Reveal
              as="li"
              key={`${h.ticker}-${h.title}`}
              delay={i * 40}
              className="group flex items-center gap-3 px-4 py-3 transition-colors hover:bg-card-hover"
            >
              <TickerLogo ticker={h.ticker} size="sm" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  {h.url ? (
                    <a
                      href={h.url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="underline-offset-2 group-hover:text-accent group-hover:underline"
                    >
                      {h.title}
                    </a>
                  ) : (
                    h.title
                  )}
                </p>
                <p className="mt-0.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span
                    aria-hidden
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      LABEL_DOT[h.label] ?? "bg-muted-foreground",
                    )}
                  />
                  <span className="capitalize">{h.label}</span>
                  {h.publisher && <span>· {h.publisher}</span>}
                  {h.published_at && (
                    <span>· {new Date(h.published_at).toLocaleDateString()}</span>
                  )}
                </p>
              </div>
              <Link
                href={`/stocks/${h.ticker}`}
                className="shrink-0 rounded-md border border-border px-2 py-1 font-mono text-xs font-semibold text-muted-foreground transition-colors hover:border-accent/50 hover:text-accent"
              >
                {h.ticker}
              </Link>
            </Reveal>
          ))}
        </ul>
      )}
    </section>
  );
}
