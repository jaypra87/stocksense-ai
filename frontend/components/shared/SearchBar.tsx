"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { useSearch } from "@/lib/hooks/useStocks";

export function SearchBar({ autoFocus = false }: { autoFocus?: boolean }) {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounce: only query 250ms after the user stops typing, so we don't fire
  // a request on every keystroke.
  useEffect(() => {
    const t = setTimeout(() => setDebounced(input.trim()), 250);
    return () => clearTimeout(t);
  }, [input]);

  const { data: results, isFetching } = useSearch(debounced);

  // Close the dropdown when clicking outside.
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  function go(symbol: string) {
    setOpen(false);
    setInput("");
    router.push(`/stocks/${encodeURIComponent(symbol)}`);
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const first = results?.[0]?.symbol ?? input.trim().toUpperCase();
    if (first) go(first);
  }

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <form onSubmit={onSubmit}>
        <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 focus-within:ring-2 focus-within:ring-accent">
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
          <input
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            placeholder="Search ticker or company (AAPL, NVDA, Tesla…)"
            autoFocus={autoFocus}
            className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          {isFetching && <Spinner />}
        </div>
      </form>

      {open && debounced.length > 0 && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-lg border border-border bg-background shadow-lg">
          {results && results.length > 0 ? (
            results.map((r) => (
              <button
                key={`${r.symbol}-${r.exchange}`}
                onClick={() => go(r.symbol)}
                className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
              >
                <span className="font-semibold">{r.symbol}</span>
                <span className="truncate text-muted-foreground">{r.name}</span>
                <span className="shrink-0 text-xs text-muted-foreground">{r.exchange}</span>
              </button>
            ))
          ) : (
            <p className="px-3 py-3 text-sm text-muted-foreground">
              {isFetching ? "Searching…" : "No matches"}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
