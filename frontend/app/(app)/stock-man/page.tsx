"use client";

import { MessageSquare, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { BackToDashboard } from "@/components/shared/BackToDashboard";
import { ChatSurface } from "@/components/stockman/ChatSurface";
import { StockmanMark } from "@/components/stockman/StockmanMark";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/components/ui/Toast";
import { fmtCompact } from "@/lib/format";
import {
  useConversationMutations,
  useConversations,
  useStockmanStatus,
} from "@/lib/hooks/useStockman";
import { cn } from "@/lib/utils";

export default function StockmanPage() {
  const status = useStockmanStatus();
  const conversations = useConversations();
  const { remove } = useConversationMutations();
  const { toast } = useToast();
  const [current, setCurrent] = useState<string | null>(null);

  function onDelete(id: string) {
    remove.mutate(id, {
      onSuccess: () => {
        if (current === id) setCurrent(null);
      },
      onError: () => toast("Couldn't delete the conversation", "error"),
    });
  }

  const budget = status.data?.budget;
  const usedPct =
    budget && budget.limit > 0 ? Math.min(100, (budget.used / budget.limit) * 100) : 0;

  return (
    <div className="space-y-6">
      <BackToDashboard />
      <div className="animate-fade-up flex flex-wrap items-end justify-between gap-3">
        <div className="flex items-center gap-3">
          <StockmanMark size="md" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Stock-man</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              An analyst that answers with this app&apos;s own data and shows its work.
            </p>
          </div>
        </div>
        {budget && (
          <div className="w-44 text-xs text-muted-foreground">
            <div className="flex justify-between">
              <span>Today&apos;s budget</span>
              <span className="tabular-nums">
                {fmtCompact(budget.used)} / {fmtCompact(budget.limit)} tokens
              </span>
            </div>
            <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-accent" style={{ width: `${usedPct}%` }} />
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
        <Card className="flex flex-col gap-3 p-4">
          <div className="flex items-center justify-between">
            <CardTitle>Conversations</CardTitle>
            <Button size="sm" variant="secondary" onClick={() => setCurrent(null)}>
              <Plus className="h-3.5 w-3.5" aria-hidden /> New
            </Button>
          </div>
          {conversations.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          ) : !conversations.data || conversations.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Nothing yet. Ask something and it will show up here.
            </p>
          ) : (
            <ul className="max-h-[60vh] space-y-1 overflow-y-auto">
              {conversations.data.map((c, i) => (
                <li
                  key={c.id}
                  className="animate-fade-up flex items-center gap-1"
                  style={{ animationDelay: `${i * 30}ms` }}
                >
                  <button
                    type="button"
                    onClick={() => setCurrent(c.id)}
                    aria-current={current === c.id ? "true" : undefined}
                    className={cn(
                      "flex min-w-0 flex-1 items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors",
                      current === c.id
                        ? "bg-muted text-foreground"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    <MessageSquare className="h-3.5 w-3.5 shrink-0" aria-hidden />
                    <span className="truncate">{c.title}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(c.id)}
                    aria-label={`Delete “${c.title}”`}
                    className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-bearish"
                  >
                    <Trash2 className="h-3.5 w-3.5" aria-hidden />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card className="flex h-[calc(100vh-15rem)] min-h-[480px] flex-col p-0">
          <ChatSurface conversationId={current} onCreated={setCurrent} className="h-full" />
        </Card>
      </div>
    </div>
  );
}
