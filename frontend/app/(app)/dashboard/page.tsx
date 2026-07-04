import type { Metadata } from "next";

import { WatchlistPreview } from "@/components/watchlist/WatchlistPreview";
import { PopularTickers } from "@/components/stock/PopularTickers";

export const metadata: Metadata = { title: "Dashboard" };

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Search any ticker above, or jump back into your watchlist.
        </p>
      </div>

      <WatchlistPreview />
      <PopularTickers />
    </div>
  );
}
