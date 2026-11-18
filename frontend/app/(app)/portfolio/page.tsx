"use client";

import { Briefcase, RotateCcw } from "lucide-react";
import { useState } from "react";

import { AllocationChart } from "@/components/portfolio/AllocationChart";
import { HoldingsTable } from "@/components/portfolio/HoldingsTable";
import { TradeHistory } from "@/components/portfolio/TradeHistory";
import { TradeTicket } from "@/components/portfolio/TradeTicket";
import { BackToDashboard } from "@/components/shared/BackToDashboard";
import { Reveal } from "@/components/shared/Reveal";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { StatTile } from "@/components/ui/StatTile";
import { useToast } from "@/components/ui/Toast";
import { fmtCurrency, fmtPercent, fmtSignedCurrency, isUp } from "@/lib/format";
import { useCountUp } from "@/lib/hooks/useCountUp";
import { usePortfolio, usePortfolioMutations } from "@/lib/hooks/usePortfolio";
import { cn } from "@/lib/utils";

export default function PortfolioPage() {
  const { data, isLoading, isError } = usePortfolio();
  const { reset } = usePortfolioMutations();
  const { toast } = useToast();
  const [trading, setTrading] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);
  const equity = useCountUp(data?.equity);

  function onReset() {
    reset.mutate(undefined, {
      onSuccess: () => {
        setConfirmReset(false);
        toast("Portfolio reset to $100,000");
      },
      onError: () => toast("Couldn't reset the portfolio", "error"),
    });
  }

  return (
    <div className="space-y-6">
      <BackToDashboard />
      <div className="animate-fade-up">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Paper portfolio</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Practice with simulated money. Every fill uses the live quote and lands in the ledger
          below.
        </p>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : isError || !data ? (
        <Card className="text-sm text-muted-foreground">Couldn&apos;t load your portfolio.</Card>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Reveal>
              <StatTile
                label="Equity"
                value={fmtCurrency(equity)}
                sub={`started with ${fmtCurrency(data.starting_cash)}`}
                valueClassName="text-2xl"
              />
            </Reveal>
            <Reveal delay={50}>
              <StatTile
                label="Total return"
                value={fmtSignedCurrency(data.total_return)}
                sub={`${fmtPercent(data.total_return_pct)} · ${fmtSignedCurrency(data.realized_pnl)} realized`}
                valueClassName={cn("text-2xl", pnlColor(data.total_return))}
              />
            </Reveal>
            <Reveal delay={100}>
              <StatTile
                label="Today"
                value={fmtSignedCurrency(data.day_change)}
                sub={fmtPercent(data.day_change_pct)}
                valueClassName={cn("text-2xl", pnlColor(data.day_change))}
              />
            </Reveal>
            <Reveal delay={150}>
              <StatTile
                label="Cash"
                value={fmtCurrency(data.cash)}
                sub={`${fmtCurrency(data.market_value)} invested`}
                valueClassName="text-2xl"
              />
            </Reveal>
          </div>

          {data.positions.length === 0 ? (
            <Reveal>
              <EmptyState
                icon={Briefcase}
                title="No positions yet"
                description={`You have ${fmtCurrency(data.cash)} of paper money. Open any stock and tap “Paper trade”.`}
              />
            </Reveal>
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <Reveal className="lg:col-span-2">
                <Card className="space-y-3">
                  <CardTitle>Holdings</CardTitle>
                  <HoldingsTable positions={data.positions} onTrade={setTrading} />
                </Card>
              </Reveal>
              <Reveal delay={80}>
                <Card className="space-y-3">
                  <CardTitle>Allocation</CardTitle>
                  <AllocationChart portfolio={data} />
                </Card>
              </Reveal>
            </div>
          )}

          <Reveal>
            <TradeHistory />
          </Reveal>

          <Reveal>
            <Card className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>Start over</CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">
                  Clears every position and fill and restores the starting cash.
                </p>
              </div>
              {confirmReset ? (
                <div className="flex items-center gap-2">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={onReset}
                    loading={reset.isPending}
                  >
                    Yes, reset
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setConfirmReset(false)}>
                    Keep it
                  </Button>
                </div>
              ) : (
                <Button variant="secondary" size="sm" onClick={() => setConfirmReset(true)}>
                  <RotateCcw className="h-4 w-4" aria-hidden /> Reset portfolio
                </Button>
              )}
            </Card>
          </Reveal>

          <p className="text-xs text-muted-foreground">{data.disclaimer}</p>
        </>
      )}

      {trading && <TradeTicket ticker={trading} open onClose={() => setTrading(null)} />}
    </div>
  );
}

function pnlColor(value: number): string {
  if (value === 0) return "";
  return isUp(value) ? "text-bullish" : "text-bearish";
}
