import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";

const FEATURES = [
  "Live quotes & historical charts",
  "Technical indicators",
  "ML trend forecasts with confidence ranges",
  "News sentiment & risk scoring",
  "Watchlists, alerts & backtests",
];

export default function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-10 px-6 py-16">
      <header className="space-y-4">
        <p className="text-sm font-medium uppercase tracking-wide text-accent">StockSense AI</p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Interpretable market analytics, not black-box predictions.
        </h1>
        <p className="text-lg text-muted-foreground">
          Live quotes, technical indicators, ML forecasts with confidence ranges, news sentiment,
          risk scoring, and historical backtests — all in one dashboard.
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 font-semibold text-accent-foreground transition-opacity hover:opacity-90"
        >
          Launch dashboard <ArrowRight className="h-4 w-4" />
        </Link>
      </header>

      <DisclaimerBanner />

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          What&apos;s inside
        </h2>
        <ul className="grid gap-2 text-sm sm:grid-cols-2">
          {FEATURES.map((f) => (
            <li key={f} className="rounded-lg border border-border bg-muted px-3 py-2">
              {f}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
