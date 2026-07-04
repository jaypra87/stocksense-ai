"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { useSearch } from "@/lib/hooks/useStocks";
import { cn } from "@/lib/utils";

export function SearchBar({ autoFocus = false }: { autoFocus?: boolean }) {
  const router = useRouter();
  const listboxId = useId();
  const [input, setInput] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounce: only query 250ms after the user stops typing.
  useEffect(() => {
    const t = setTimeout(() => setDebounced(input.trim()), 250);
    return () => clearTimeout(t);
  }, [input]);

  const { data: results, isFetching } = useSearch(debounced);

  // Reset keyboard highlight when the result set changes.
  useEffect(() => setActiveIndex(-1), [debounced]);

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

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Escape") {
      setOpen(false);
      return;
    }
    if (!results || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActiveIndex((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => (i <= 0 ? results.length - 1 : i - 1));
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const chosen =
      (activeIndex >= 0 ? results?.[activeIndex]?.symbol : undefined) ??
      results?.[0]?.symbol ??
      input.trim().toUpperCase();
    if (chosen) go(chosen);
  }

  const expanded = open && debounced.length > 0;

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <form onSubmit={onSubmit}>
        <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 shadow-sm transition-colors focus-within:border-accent focus-within:ring-2 focus-within:ring-ring/40">
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
          <input
            role="combobox"
            aria-label="Search stocks"
            aria-expanded={expanded}
            aria-controls={listboxId}
            aria-activedescendant={activeIndex >= 0 ? `${listboxId}-${activeIndex}` : undefined}
            aria-autocomplete="list"
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={onKeyDown}
            placeholder="Search ticker or company (AAPL, NVDA, Tesla…)"
            autoFocus={autoFocus}
            className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground/70"
          />
          {isFetching && <Spinner />}
        </div>
      </form>

      {expanded && (
        <ul
          id={listboxId}
          role="listbox"
          aria-label="Search results"
          className="absolute z-20 mt-1.5 w-full overflow-hidden rounded-lg border border-border bg-card shadow-lg"
        >
          {results && results.length > 0 ? (
            results.map((r, i) => (
              <li key={`${r.symbol}-${r.exchange}`} role="presentation">
                <button
                  id={`${listboxId}-${i}`}
                  role="option"
                  aria-selected={i === activeIndex}
                  onClick={() => go(r.symbol)}
                  onMouseEnter={() => setActiveIndex(i)}
                  className={cn(
                    "flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition-colors",
                    i === activeIndex ? "bg-muted" : "hover:bg-muted",
                  )}
                >
                  <span className="font-semibold">{r.symbol}</span>
                  <span className="truncate text-muted-foreground">{r.name}</span>
                  <span className="shrink-0 text-xs text-muted-foreground">{r.exchange}</span>
                </button>
              </li>
            ))
          ) : (
            <li className="px-3 py-3 text-sm text-muted-foreground" role="presentation">
              {isFetching ? "Searching…" : "No matches"}
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
