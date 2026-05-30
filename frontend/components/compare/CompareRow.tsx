"use client";

import { X } from "lucide-react";
import Link from "next/link";

import { useQuote, useRisk, useSentiment } from "@/lib/hooks/useStocks";
import { fmtCurrency, fmtPercent, isUp } from "@/lib/format";
import { cn } from "@/lib/utils";

export function CompareRow({ ticker, onRemove }: { ticker: string; onRemove: () => void }) {
  const quote = useQuote(ticker);
  const risk = useRisk(ticker);
  const sentiment = useSentiment(ticker);

  const up = isUp(quote.data?.change_percent);

  return (
    <tr className="border-t border-border">
      <td className="py-2.5 pr-4">
        <Link href={`/stocks/${ticker}`} className="font-semibold hover:text-accent">
          {ticker}
        </Link>
      </td>
      <td className="py-2.5 pr-4 tabular-nums">{fmtCurrency(quote.data?.price, quote.data?.currency ?? "USD")}</td>
      <td className={cn("py-2.5 pr-4 tabular-nums", up ? "text-bullish" : "text-bearish")}>
        {quote.isLoading ? "…" : fmtPercent(quote.data?.change_percent)}
      </td>
      <td className="py-2.5 pr-4 tabular-nums">
        {risk.isLoading ? "…" : risk.data ? `${Math.round(risk.data.risk_score)} (${risk.data.risk_level.replace("_", " ")})` : "—"}
      </td>
      <td className="py-2.5 pr-4 capitalize">
        {sentiment.isLoading ? "…" : (sentiment.data?.overall_label ?? "—")}
      </td>
      <td className="py-2.5">
        <button
          onClick={onRemove}
          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-bearish"
          title="Remove"
        >
          <X className="h-4 w-4" />
        </button>
      </td>
    </tr>
  );
}
