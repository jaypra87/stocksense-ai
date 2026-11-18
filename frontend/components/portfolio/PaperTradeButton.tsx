"use client";

import { ArrowLeftRight } from "lucide-react";
import { useState } from "react";

import { TradeTicket } from "@/components/portfolio/TradeTicket";

export function PaperTradeButton({ ticker }: { ticker: string }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        <ArrowLeftRight className="h-4 w-4" aria-hidden />
        Paper trade
      </button>
      <TradeTicket ticker={ticker} open={open} onClose={() => setOpen(false)} />
    </>
  );
}
