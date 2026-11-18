"use client";

import { ArrowLeftRight } from "lucide-react";
import { useState } from "react";

import { TradeTicket } from "@/components/portfolio/TradeTicket";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { fmtCurrency, fmtNumber } from "@/lib/format";
import type { TradeSide } from "@/types/portfolio";

export interface TradeProposal {
  proposal: true;
  ticker: string;
  side: TradeSide;
  quantity: number;
  estimated_price: number;
  estimated_total: number;
  cash_available: number;
  currently_held: number;
  rationale: string;
}

export function isTradeProposal(value: unknown): value is TradeProposal {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as { proposal?: unknown }).proposal === true &&
    typeof (value as { ticker?: unknown }).ticker === "string"
  );
}

// Stock-man can draft a trade but never place one. The card hands the draft
// to the same ticket a person would use, where they confirm it themselves.
export function TradeProposalCard({ proposal }: { proposal: TradeProposal }) {
  const [open, setOpen] = useState(false);
  const buy = proposal.side === "buy";

  return (
    <div className="rounded-xl border border-accent/40 bg-accent/5 p-3.5 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={buy ? "accent" : "neutral"}>{buy ? "Buy idea" : "Sell idea"}</Badge>
        <span className="font-semibold">{proposal.ticker}</span>
        <span className="tabular-nums text-muted-foreground">
          {fmtNumber(proposal.quantity, 4)} shares · about {fmtCurrency(proposal.estimated_total)}
        </span>
      </div>
      <p className="mt-2 text-muted-foreground">{proposal.rationale}</p>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">Not placed. Paper money, your call.</span>
        <Button size="sm" variant="secondary" onClick={() => setOpen(true)}>
          <ArrowLeftRight className="h-3.5 w-3.5" aria-hidden /> Review in ticket
        </Button>
      </div>
      <TradeTicket
        ticker={proposal.ticker}
        open={open}
        onClose={() => setOpen(false)}
        initialSide={proposal.side}
        initialQuantity={proposal.quantity}
      />
    </div>
  );
}
