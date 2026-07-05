"use client";

import { AlertCircle } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import { BacktestPanel } from "@/components/backtest/BacktestPanel";
import { IndicatorsPanel } from "@/components/indicators/IndicatorsPanel";
import { RSIChart } from "@/components/indicators/RSIChart";
import { PredictionPanel } from "@/components/prediction/PredictionPanel";
import { RiskPanel } from "@/components/risk/RiskPanel";
import { SentimentPanel } from "@/components/sentiment/SentimentPanel";
import { Reveal } from "@/components/shared/Reveal";
import { TickerLogo } from "@/components/shared/TickerLogo";
import { KeyStats } from "@/components/stock/KeyStats";
import { PriceChart } from "@/components/stock/PriceChart";
import { QuoteCard } from "@/components/stock/QuoteCard";
import { Card, CardTitle } from "@/components/ui/Card";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { Skeleton } from "@/components/ui/Skeleton";
import { WatchlistButton } from "@/components/watchlist/WatchlistButton";
import { useHistory, useIndicators, useQuote, useStock } from "@/lib/hooks/useStocks";
import { RANGES, type Range } from "@/types/stock";

export default function StockPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = decodeURIComponent(params.ticker).toUpperCase();
  const [range, setRange] = useState<Range>("1y");

  const quote = useQuote(ticker);
  const stock = useStock(ticker);
  const history = useHistory(ticker, range);
  const indicators = useIndicators(ticker, range);

  // A failing quote is our signal that the ticker is bad / upstream is down.
  if (quote.isError) {
    return (
      <Card className="flex items-center gap-3 border-bearish/40" role="alert">
        <AlertCircle className="h-5 w-5 shrink-0 text-bearish" aria-hidden />
        <div>
          <p className="font-semibold">Couldn&apos;t load {ticker}</p>
          <p className="text-sm text-muted-foreground">
            The ticker may be invalid, or the data provider is unavailable. Try another symbol.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header row: ticker + watchlist toggle */}
      <div className="flex animate-fade-up items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <TickerLogo ticker={ticker} size="lg" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{ticker}</h1>
            {stock.data?.company_name && (
              <p className="text-sm text-muted-foreground">{stock.data.company_name}</p>
            )}
          </div>
        </div>
        <WatchlistButton ticker={ticker} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Side column first in DOM so price + stats lead on mobile; visually right
            on lg, where it sticks in place while the analysis column scrolls. */}
        <div className="space-y-6 lg:sticky lg:top-20 lg:order-2 lg:self-start">
          <Reveal>
            <QuoteCard quote={quote.data} stock={stock.data} isLoading={quote.isLoading} />
          </Reveal>
          <Reveal delay={80}>
            <KeyStats quote={quote.data} isLoading={quote.isLoading} />
          </Reveal>
          {stock.data && (stock.data.sector || stock.data.exchange) && (
            <Reveal delay={160} className="hidden lg:block">
              <Card className="space-y-3">
                <CardTitle>Profile</CardTitle>
                <dl className="space-y-2 text-sm">
                  {(
                    [
                      ["Sector", stock.data.sector],
                      ["Exchange", stock.data.exchange],
                      ["Currency", stock.data.currency],
                    ] as const
                  )
                    .filter(([, value]) => value)
                    .map(([label, value]) => (
                      <div key={label} className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">{label}</dt>
                        <dd className="font-medium">{value}</dd>
                      </div>
                    ))}
                </dl>
              </Card>
            </Reveal>
          )}
        </div>

        {/* Main column: chart + analysis panels */}
        <div className="space-y-6 lg:order-1 lg:col-span-2">
          <Reveal>
            <Card className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle>Price history</CardTitle>
                <SegmentedControl
                  options={RANGES}
                  value={range}
                  onChange={setRange}
                  label="Chart range"
                />
              </div>
              {history.isLoading ? (
                <Skeleton className="h-[360px] w-full" />
              ) : history.isError ? (
                <div className="flex h-[360px] items-center justify-center text-sm text-muted-foreground">
                  Failed to load price history.
                </div>
              ) : (
                history.data && (
                  <PriceChart
                    history={history.data}
                    range={range}
                    currency={quote.data?.currency ?? "USD"}
                  />
                )
              )}
            </Card>
          </Reveal>

          <Reveal>
            <PredictionPanel ticker={ticker} currency={quote.data?.currency ?? "USD"} />
          </Reveal>
          <Reveal>
            <RiskPanel ticker={ticker} />
          </Reveal>
          <Reveal>
            <SentimentPanel ticker={ticker} />
          </Reveal>

          <Reveal>
            <IndicatorsPanel
              data={indicators.data}
              isLoading={indicators.isLoading}
              currency={quote.data?.currency ?? "USD"}
            />
          </Reveal>
          {!indicators.isLoading && indicators.data && (
            <Reveal>
              <RSIChart data={indicators.data} range={range} />
            </Reveal>
          )}

          <Reveal>
            <BacktestPanel ticker={ticker} />
          </Reveal>
        </div>
      </div>
    </div>
  );
}
