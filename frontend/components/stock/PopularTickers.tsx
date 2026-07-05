import Link from "next/link";

import { Reveal } from "@/components/shared/Reveal";
import { TickerLogo } from "@/components/shared/TickerLogo";

export const POPULAR = [
  { symbol: "AAPL", name: "Apple" },
  { symbol: "MSFT", name: "Microsoft" },
  { symbol: "NVDA", name: "NVIDIA" },
  { symbol: "TSLA", name: "Tesla" },
  { symbol: "AMZN", name: "Amazon" },
  { symbol: "GOOGL", name: "Alphabet" },
];

export function PopularTickers() {
  return (
    <section aria-labelledby="popular-heading">
      <h2
        id="popular-heading"
        className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
      >
        Popular tickers
      </h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {POPULAR.map((p, i) => (
          <Reveal key={p.symbol} delay={i * 50}>
            <Link
              href={`/stocks/${p.symbol}`}
              className="hover-lift flex items-center gap-2.5 rounded-xl border border-border bg-card p-3.5 shadow-sm transition-colors hover:border-accent/50 dark:shadow-none"
            >
              <TickerLogo ticker={p.symbol} size="md" />
              <div className="min-w-0">
                <div className="font-bold">{p.symbol}</div>
                <div className="truncate text-xs text-muted-foreground">{p.name}</div>
              </div>
            </Link>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
