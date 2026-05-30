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
import { KeyStats } from "@/components/stock/KeyStats";
import { PriceChart } from "@/components/stock/PriceChart";
import { QuoteCard } from "@/components/stock/QuoteCard";
import { RangeSelector } from "@/components/stock/RangeSelector";
import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { WatchlistButton } from "@/components/watchlist/WatchlistButton";
import { useHistory, useIndicators, useQuote, useStock } from "@/lib/hooks/useStocks";
import type { Range } from "@/types/stock";

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
      <Card className="flex items-center gap-3 border-bearish/40">
        <AlertCircle className="h-5 w-5 text-bearish" />
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
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{ticker}</h1>
          {stock.data?.company_name && (
            <p className="text-sm text-muted-foreground">{stock.data.company_name}</p>
          )}
        </div>
        <WatchlistButton ticker={ticker} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main column: chart */}
        <div className="space-y-6 lg:col-span-2">
        <Card className="space-y-4">
          <div className="flex items-center justify-between gap-3">
            <CardTitle>Price history</CardTitle>
            <RangeSelector value={range} onChange={setRange} />
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

        {/* AI Forecast (Phase 5) + Risk (Phase 6). */}
        <PredictionPanel ticker={ticker} currency={quote.data?.currency ?? "USD"} />
        <RiskPanel ticker={ticker} />

        {/* News Sentiment (Phase 7). */}
        <SentimentPanel ticker={ticker} />

        {/* Technical indicators (Phase 4). */}
        <IndicatorsPanel
          data={indicators.data}
          isLoading={indicators.isLoading}
          currency={quote.data?.currency ?? "USD"}
        />
        {!indicators.isLoading && indicators.data && (
          <RSIChart data={indicators.data} range={range} />
        )}

        {/* Backtesting (Phase 9). */}
        <BacktestPanel ticker={ticker} />
        </div>

        {/* Side column: quote + stats */}
        <div className="space-y-6">
          <QuoteCard quote={quote.data} stock={stock.data} isLoading={quote.isLoading} />
          <KeyStats quote={quote.data} isLoading={quote.isLoading} />
        </div>
      </div>
    </div>
  );
}
