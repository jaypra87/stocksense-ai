"use client";

import { AlertCircle, ArrowUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Markdown } from "@/components/stockman/Markdown";
import { StockmanMark } from "@/components/stockman/StockmanMark";
import { ToolCallChip } from "@/components/stockman/ToolCallChip";
import { isTradeProposal, TradeProposalCard } from "@/components/stockman/TradeProposalCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { useChat, useStockmanStatus } from "@/lib/hooks/useStockman";
import { cn } from "@/lib/utils";
import type { ChatTurn } from "@/types/stockman";

const SUGGESTIONS = [
  "How is my paper portfolio doing?",
  "Is NVDA risky right now?",
  "Compare the 7-day forecast for AAPL and MSFT",
  "What's the news sentiment on TSLA?",
];

const MAX_LENGTH = 2000;

export function ChatSurface({
  conversationId,
  onCreated,
  className,
}: {
  conversationId: string | null;
  onCreated?: (id: string) => void;
  className?: string;
}) {
  const status = useStockmanStatus();
  const { turns, send, busy, loading } = useChat(conversationId, onCreated);
  const [draft, setDraft] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);

  const offline = status.data ? !status.data.enabled : false;
  const last = turns[turns.length - 1];

  // Follow the answer as it streams; a new turn always scrolls into view.
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [turns.length, last?.text, last?.tools.length]);

  function submit(text = draft) {
    if (!text.trim() || busy || offline) return;
    setDraft("");
    void send(text);
    input.current?.focus();
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className={cn("flex min-h-0 flex-col", className)}>
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {offline && (
          <div className="flex items-start gap-2.5 rounded-lg border border-warning/40 bg-warning/5 px-3 py-2.5 text-sm">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden />
            <span>Stock-man is offline: no model API key is configured on the server.</span>
          </div>
        )}

        {loading ? (
          <div className="space-y-3">
            <Skeleton className="ml-auto h-9 w-2/3" />
            <Skeleton className="h-20 w-5/6" />
          </div>
        ) : turns.length === 0 ? (
          <Welcome onPick={submit} disabled={offline} />
        ) : (
          turns.map((turn) => <Turn key={turn.id} turn={turn} />)
        )}
        <div ref={bottom} />
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="border-t border-border px-3 pb-3 pt-2"
      >
        <div className="flex items-end gap-2 rounded-xl border border-border bg-background/60 px-3 py-2 transition-colors focus-within:border-accent focus-within:ring-2 focus-within:ring-ring/40">
          <textarea
            ref={input}
            value={draft}
            onChange={(e) => setDraft(e.target.value.slice(0, MAX_LENGTH))}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder={offline ? "Stock-man is offline" : "Ask about a stock or your portfolio…"}
            aria-label="Message Stock-man"
            disabled={offline}
            className="max-h-32 min-h-[24px] flex-1 resize-none bg-transparent text-sm leading-6 outline-none placeholder:text-muted-foreground/70 disabled:opacity-60"
            style={{ height: "auto" }}
            onInput={(e) => {
              const el = e.currentTarget;
              el.style.height = "auto";
              el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
            }}
          />
          <button
            type="submit"
            disabled={!draft.trim() || busy || offline}
            aria-label="Send"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground transition-[background-color,transform,opacity] hover:bg-accent-hover active:scale-95 disabled:opacity-40"
          >
            <ArrowUp className="h-4 w-4" aria-hidden />
          </button>
        </div>
        <p className="mt-2 px-1 text-[11px] leading-snug text-muted-foreground">
          {status.data?.disclaimer ??
            "Stock-man is an educational assistant. Its answers come from this app's models and data, which are often wrong. Not financial advice."}
        </p>
      </form>
    </div>
  );
}

function Welcome({ onPick, disabled }: { onPick: (text: string) => void; disabled: boolean }) {
  return (
    <div className="animate-fade-up space-y-4 pt-2">
      <div className="flex items-start gap-3">
        <StockmanMark size="md" />
        <div className="text-sm">
          <p className="font-semibold">Hi, I&apos;m Stock-man.</p>
          <p className="mt-1 text-muted-foreground">
            I answer with this app&apos;s own quotes, forecasts, risk scores and news, and I show
            which tool every number came from. I can draft paper trades for you to confirm, but I
            never place them.
          </p>
        </div>
      </div>
      <ul className="grid gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((s, i) => (
          <li key={s} className="animate-fade-up" style={{ animationDelay: `${80 + i * 50}ms` }}>
            <button
              type="button"
              onClick={() => onPick(s)}
              disabled={disabled}
              className="hover-lift w-full rounded-xl border border-border bg-card px-3 py-2.5 text-left text-sm transition-colors hover:border-accent/50 disabled:opacity-50"
            >
              {s}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Turn({ turn }: { turn: ChatTurn }) {
  if (turn.role === "user") {
    return (
      <div className="animate-fade-up flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-accent px-3.5 py-2 text-sm text-accent-foreground">
          {turn.text}
        </div>
      </div>
    );
  }

  const proposals = turn.tools.filter((t) => isTradeProposal(t.result));
  const waiting = turn.streaming && turn.text === "" && !turn.error;

  return (
    <div className="animate-fade-up flex items-start gap-2.5">
      <StockmanMark className="mt-0.5" />
      <div className="min-w-0 flex-1 space-y-2">
        {turn.tools.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {turn.tools.map((call) => (
              <ToolCallChip key={call.id} call={call} />
            ))}
          </div>
        )}
        {waiting ? (
          <div className="flex items-center gap-1 py-2" aria-label="Stock-man is thinking">
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
            <span className="typing-dot h-1.5 w-1.5 rounded-full bg-muted-foreground" />
          </div>
        ) : (
          turn.text && (
            <div className="text-sm">
              <Markdown text={turn.text} />
              {turn.streaming && <span className="stream-caret" aria-hidden />}
            </div>
          )
        )}
        {proposals.map((call) =>
          isTradeProposal(call.result) ? (
            <TradeProposalCard key={call.id} proposal={call.result} />
          ) : null,
        )}
        {turn.grounding && turn.grounding.unmatched.length > 0 && (
          <p className="flex items-start gap-1.5 text-xs text-warning">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            {turn.grounding.unmatched.length === 1
              ? "One figure"
              : `${turn.grounding.unmatched.length} figures`}{" "}
            here couldn&apos;t be traced to a tool result: {turn.grounding.unmatched.join(", ")}.
            Treat them with care.
          </p>
        )}
        {turn.error && (
          <p className="flex items-start gap-1.5 text-xs text-bearish" role="alert">
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            {turn.error}
          </p>
        )}
      </div>
    </div>
  );
}
