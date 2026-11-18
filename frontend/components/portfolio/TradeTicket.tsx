"use client";

import { ArrowDownRight, ArrowUpRight, X } from "lucide-react";
import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { TickerLogo } from "@/components/shared/TickerLogo";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api/client";
import { fmtCurrency, fmtNumber, fmtPercent, isUp } from "@/lib/format";
import { usePortfolio, usePortfolioMutations } from "@/lib/hooks/usePortfolio";
import { useQuote } from "@/lib/hooks/useStocks";
import { cn } from "@/lib/utils";
import type { TradeOrder, TradeSide } from "@/types/portfolio";

const SIDES = ["buy", "sell"] as const;
const SIDE_LABELS = { buy: "Buy", sell: "Sell" } as const;
const MODES = ["shares", "dollars"] as const;
const MODE_LABELS = { shares: "Shares", dollars: "Dollars" } as const;

type Mode = (typeof MODES)[number];

// Matches the ledger's precision so a "max" sell closes the lot exactly.
const SHARE_DECIMALS = 6;

export function TradeTicket({
  ticker,
  open,
  onClose,
  initialSide = "buy",
}: {
  ticker: string;
  open: boolean;
  onClose: () => void;
  initialSide?: TradeSide;
}) {
  if (!open) return null;
  return <Ticket ticker={ticker} onClose={onClose} initialSide={initialSide} />;
}

function Ticket({
  ticker,
  onClose,
  initialSide,
}: {
  ticker: string;
  onClose: () => void;
  initialSide: TradeSide;
}) {
  const quote = useQuote(ticker);
  const portfolio = usePortfolio();
  const { trade } = usePortfolioMutations();
  const { toast } = useToast();
  const titleId = useId();
  const inputRef = useRef<HTMLInputElement>(null);

  const [side, setSide] = useState<TradeSide>(initialSide);
  const [mode, setMode] = useState<Mode>("shares");
  const [raw, setRaw] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Escape closes, the page behind stays put, and focus goes back to the
  // control that opened the ticket.
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    inputRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
      opener?.focus();
    };
  }, [onClose]);

  const price = quote.data?.price;
  const ccy = quote.data?.currency ?? "USD";
  const cash = portfolio.data?.cash ?? 0;
  const held = portfolio.data?.positions.find((p) => p.ticker === ticker)?.quantity ?? 0;

  const entered = Number(raw);
  const valid = raw !== "" && Number.isFinite(entered) && entered > 0;
  const shares = !valid || !price ? 0 : mode === "shares" ? entered : entered / price;
  const total = shares * (price ?? 0);
  const over = side === "buy" ? total > cash + 0.005 : shares > held + 1e-6;

  function fillMax() {
    if (!price) return;
    if (side === "buy") {
      setRaw(mode === "dollars" ? cash.toFixed(2) : (cash / price).toFixed(SHARE_DECIMALS));
    } else {
      setRaw(mode === "dollars" ? (held * price).toFixed(2) : held.toFixed(SHARE_DECIMALS));
    }
    setError(null);
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!valid || over || !price) return;
    const order: TradeOrder =
      mode === "shares"
        ? { ticker, side, quantity: Number(entered.toFixed(SHARE_DECIMALS)) }
        : { ticker, side, amount: entered };
    trade.mutate(order, {
      onSuccess: (fill) => {
        const verb = fill.side === "buy" ? "Bought" : "Sold";
        toast(
          `${verb} ${fmtNumber(fill.quantity, 4)} ${fill.ticker} at ${fmtCurrency(fill.price, ccy)}`,
        );
        onClose();
      },
      onError: (err) =>
        setError(err instanceof ApiError ? err.message : "The order couldn't be placed."),
    });
  }

  const up = isUp(quote.data?.change);

  return createPortal(
    <div className="fixed inset-0 z-40">
      <div
        className="animate-backdrop absolute inset-0 bg-background/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <form
        onSubmit={submit}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="animate-slide-in absolute inset-y-0 right-0 flex w-full max-w-md flex-col border-l border-border bg-card shadow-xl"
      >
        <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-4">
          <div className="flex items-center gap-3">
            <TickerLogo ticker={ticker} size="lg" />
            <div>
              <h2 id={titleId} className="text-lg font-bold leading-tight">
                Paper trade {ticker}
              </h2>
              {quote.isLoading ? (
                <Skeleton className="mt-1 h-4 w-32" />
              ) : quote.data ? (
                <p className="mt-0.5 flex items-center gap-1.5 text-sm tabular-nums">
                  <span className="font-semibold">{fmtCurrency(quote.data.price, ccy)}</span>
                  <span
                    className={cn(
                      "flex items-center text-xs font-medium",
                      up ? "text-bullish" : "text-bearish",
                    )}
                  >
                    {up ? (
                      <ArrowUpRight className="h-3.5 w-3.5" aria-hidden />
                    ) : (
                      <ArrowDownRight className="h-3.5 w-3.5" aria-hidden />
                    )}
                    {fmtPercent(quote.data.change_percent)}
                  </span>
                </p>
              ) : (
                <p className="mt-0.5 text-sm text-bearish">Live price unavailable</p>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <SegmentedControl
              options={SIDES}
              value={side}
              onChange={(s) => {
                setSide(s);
                setError(null);
              }}
              label="Order side"
              labels={SIDE_LABELS}
            />
            <SegmentedControl
              options={MODES}
              value={mode}
              onChange={(m) => {
                setMode(m);
                setRaw("");
                setError(null);
              }}
              label="Order size"
              labels={MODE_LABELS}
            />
          </div>

          <div className="relative">
            <Input
              ref={inputRef}
              label={mode === "shares" ? "Shares" : `Amount (${ccy})`}
              type="number"
              inputMode="decimal"
              step="any"
              min="0"
              placeholder={mode === "shares" ? "0.00" : "1,000.00"}
              value={raw}
              onChange={(e) => {
                setRaw(e.target.value);
                setError(null);
              }}
              error={error ?? undefined}
              className="pr-14"
            />
            <button
              type="button"
              onClick={fillMax}
              disabled={!price}
              className="absolute right-2 top-[31px] rounded px-1.5 py-0.5 text-xs font-semibold uppercase tracking-wide text-accent transition-colors hover:bg-accent/10 disabled:opacity-50"
            >
              Max
            </button>
          </div>

          <dl className="space-y-2 rounded-lg border border-border bg-background/50 p-3 text-sm">
            <Row label="Fill price" value={fmtCurrency(price, ccy)} />
            <Row
              label={mode === "shares" ? "Estimated total" : "Shares"}
              value={
                mode === "shares"
                  ? fmtCurrency(valid ? total : null, ccy)
                  : fmtNumber(valid ? shares : null, 4)
              }
            />
            {side === "buy" ? (
              <Row
                label="Cash after"
                value={fmtCurrency(valid ? cash - total : cash, ccy)}
                tone={over ? "bad" : undefined}
              />
            ) : (
              <Row
                label="Holding after"
                value={`${fmtNumber(valid ? Math.max(0, held - shares) : held, 4)} shares`}
                tone={over ? "bad" : undefined}
              />
            )}
          </dl>

          {over && (
            <p className="text-xs text-bearish" role="alert">
              {side === "buy"
                ? `That's more than the ${fmtCurrency(cash, ccy)} of cash available.`
                : `You hold ${fmtNumber(held, 4)} shares of ${ticker}.`}
            </p>
          )}
        </div>

        <div className="space-y-3 border-t border-border px-5 py-4">
          <Button
            type="submit"
            className="w-full"
            disabled={!valid || over || !price}
            loading={trade.isPending}
          >
            {SIDE_LABELS[side]} {ticker}
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            Paper money only. Fills use delayed quotes and ignore fees and market hours.
          </p>
        </div>
      </form>
    </div>,
    document.body,
  );
}

function Row({ label, value, tone }: { label: string; value: string; tone?: "bad" }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={cn("font-medium tabular-nums", tone === "bad" && "text-bearish")}>{value}</dd>
    </div>
  );
}
