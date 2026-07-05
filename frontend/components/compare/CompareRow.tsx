"use client";

import { X } from "lucide-react";
import Link from "next/link";

import { TickerLogo } from "@/components/shared/TickerLogo";
import { fmtCurrency, fmtPercent, isUp } from "@/lib/format";
import { useQuote, useRisk, useSentiment } from "@/lib/hooks/useStocks";
import { cn } from "@/lib/utils";

export function CompareRow({ ticker, onRemove }: { ticker: string; onRemove: () => void }) {
  const quote = useQuote(ticker);
  const risk = useRisk(ticker);
  const sentiment = useSentiment(ticker);

  const up = isUp(quote.data?.change_percent);

  return (
    <tr className="border-t border-border">
      <td className="py-2.5 pr-4">
        <Link
          href={`/stocks/${ticker}`}
          className="inline-flex items-center gap-2 font-semibold underline-offset-2 hover:text-accent hover:underline"
        >
          <TickerLogo ticker={ticker} size="sm" />
          {ticker}
        </Link>
      </td>
      <td className="py-2.5 pr-4 tabular-nums">
        {quote.isError ? "—" : fmtCurrency(quote.data?.price, quote.data?.currency ?? "USD")}
      </td>
      <td className={cn("py-2.5 pr-4 tabular-nums", up ? "text-bullish" : "text-bearish")}>
        {quote.isLoading ? "…" : quote.isError ? "—" : fmtPercent(quote.data?.change_percent)}
      </td>
      <td className="py-2.5 pr-4 tabular-nums">
        {risk.isLoading
          ? "…"
          : risk.data
            ? `${Math.round(risk.data.risk_score)} (${risk.data.risk_level.replace("_", " ")})`
            : "—"}
      </td>
      <td className="py-2.5 pr-4 capitalize">
        {sentiment.isLoading ? "…" : (sentiment.data?.overall_label ?? "—")}
      </td>
      <td className="py-2.5">
        <button
          onClick={onRemove}
          aria-label={`Remove ${ticker} from comparison`}
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-bearish"
        >
          <X className="h-4 w-4" aria-hidden />
        </button>
      </td>
    </tr>
  );
}
