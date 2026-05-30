import Link from "next/link";

import { Card } from "@/components/ui/Card";

const POPULAR = [
  { symbol: "AAPL", name: "Apple" },
  { symbol: "MSFT", name: "Microsoft" },
  { symbol: "NVDA", name: "NVIDIA" },
  { symbol: "TSLA", name: "Tesla" },
  { symbol: "AMZN", name: "Amazon" },
  { symbol: "GOOGL", name: "Alphabet" },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Search any ticker above, or jump into a popular one below.
        </p>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Popular tickers
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {POPULAR.map((p) => (
            <Link key={p.symbol} href={`/stocks/${p.symbol}`}>
              <Card className="transition-colors hover:border-accent hover:bg-muted">
                <div className="font-bold">{p.symbol}</div>
                <div className="text-xs text-muted-foreground">{p.name}</div>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
