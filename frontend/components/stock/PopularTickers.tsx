import Link from "next/link";

const POPULAR = [
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
        {POPULAR.map((p) => (
          <Link
            key={p.symbol}
            href={`/stocks/${p.symbol}`}
            className="hover-lift rounded-xl border border-border bg-card p-3.5 shadow-sm transition-colors hover:border-accent/50 dark:shadow-none"
          >
            <div className="font-bold">{p.symbol}</div>
            <div className="text-xs text-muted-foreground">{p.name}</div>
          </Link>
        ))}
      </div>
    </section>
  );
}
