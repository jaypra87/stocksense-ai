"use client";

import { Expand, Plus, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { ChatSurface } from "@/components/stockman/ChatSurface";
import { StockmanMark } from "@/components/stockman/StockmanMark";
import { cn } from "@/lib/utils";

const THREAD_KEY = "stockman:dock:conversation";

// Stock-man follows the visitor around the app as a floating button. The
// panel keeps one running thread between openings; the full page at
// /stock-man is where the history lives.
export function StockmanDock() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  useEffect(() => {
    try {
      setConversationId(window.localStorage.getItem(THREAD_KEY));
    } catch {
      // storage can be blocked; the thread just starts fresh
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  function remember(id: string | null) {
    setConversationId(id);
    try {
      if (id) window.localStorage.setItem(THREAD_KEY, id);
      else window.localStorage.removeItem(THREAD_KEY);
    } catch {
      // see above
    }
  }

  if (pathname === "/stock-man") return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close Stock-man" : "Ask Stock-man"}
        aria-expanded={open}
        className={cn(
          "fixed bottom-5 right-5 z-30 flex h-12 items-center gap-2 rounded-full border border-accent/30 bg-card py-2 pl-2 pr-4 text-sm font-semibold shadow-lg transition-[transform,box-shadow,border-color] hover:-translate-y-0.5 hover:border-accent/60 hover:shadow-xl active:scale-95",
          open &&
            "pointer-events-none scale-95 opacity-0 sm:pointer-events-auto sm:scale-100 sm:opacity-100",
        )}
      >
        <StockmanMark size="md" />
        <span className="hidden sm:inline">Ask Stock-man</span>
      </button>

      {open && (
        <section
          role="dialog"
          aria-label="Stock-man"
          className="animate-pop fixed inset-x-0 bottom-0 top-14 z-40 flex flex-col border-t border-border bg-card shadow-2xl sm:inset-auto sm:bottom-24 sm:right-5 sm:h-[620px] sm:max-h-[calc(100vh-7.5rem)] sm:w-[420px] sm:rounded-2xl sm:border"
        >
          <header className="flex items-center gap-2.5 border-b border-border px-4 py-3">
            <StockmanMark />
            <div className="min-w-0 flex-1 leading-tight">
              <p className="text-sm font-semibold">Stock-man</p>
              <p className="truncate text-xs text-muted-foreground">Your analyst, with receipts</p>
            </div>
            <button
              type="button"
              onClick={() => remember(null)}
              aria-label="New conversation"
              title="New conversation"
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <Plus className="h-4 w-4" aria-hidden />
            </button>
            <Link
              href="/stock-man"
              aria-label="Open the full page"
              title="Open the full page"
              onClick={() => setOpen(false)}
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <Expand className="h-4 w-4" aria-hidden />
            </Link>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close"
              className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <X className="h-4 w-4" aria-hidden />
            </button>
          </header>
          <ChatSurface conversationId={conversationId} onCreated={remember} className="flex-1" />
        </section>
      )}
    </>
  );
}
