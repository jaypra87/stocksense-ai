import {
  ArrowRight,
  Bell,
  BrainCircuit,
  CandlestickChart,
  FlaskConical,
  Newspaper,
  ShieldAlert,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { HeroPreview } from "@/components/marketing/HeroPreview";

export const metadata: Metadata = {
  title: { absolute: "StockSense AI — Interpretable stock analytics, not black-box predictions" },
  description:
    "Every forecast comes with a confidence score, an expected range, a plain-English explanation, a transparent risk breakdown, and honest backtests. Educational only.",
  alternates: { canonical: "/" },
};

const FEATURES = [
  {
    Icon: CandlestickChart,
    title: "Live quotes & charts",
    description: "Real-time quotes with 1D–5Y history, volume overlays, and persistent candles.",
  },
  {
    Icon: BrainCircuit,
    title: "ML forecasts with confidence",
    description:
      "1d/7d/30d trend calls with confidence scores, expected price ranges, and the factors driving each call.",
  },
  {
    Icon: ShieldAlert,
    title: "Transparent risk scoring",
    description:
      "A 0–100 composite built from volatility, drawdown, volume, trend, model uncertainty, and sentiment — every factor shown.",
  },
  {
    Icon: Newspaper,
    title: "News sentiment",
    description: "Recent headlines classified and summarized, then fed back into the risk engine.",
  },
  {
    Icon: Bell,
    title: "Watchlists & alerts",
    description: "Save tickers, set alert rules, and review the full triggered history.",
  },
  {
    Icon: FlaskConical,
    title: "Honest backtesting",
    description:
      "Walk-forward, no-lookahead backtests against naive baselines — including when the model loses.",
  },
];

const STEPS = [
  {
    step: "01",
    title: "Search any ticker",
    description: "Autocomplete with exchange-suffix support: AAPL, BRK-B, VFV.TO.",
  },
  {
    step: "02",
    title: "Read the full picture",
    description:
      "Price history, technical indicators, an AI forecast with its reasoning, risk factors, and news sentiment on one page.",
  },
  {
    step: "03",
    title: "Verify before you trust",
    description:
      "Run a walk-forward backtest and inspect the model's real accuracy against naive baselines.",
  },
];

const JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "StockSense AI",
  applicationCategory: "FinanceApplication",
  description:
    "Interpretable, uncertainty-aware stock analytics: ML forecasts with confidence ranges, transparent risk scoring, news sentiment, and honest backtesting. Educational only — not financial advice.",
  offers: { "@type": "Offer", price: "0" },
};

export default function LandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }}
      />

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,hsl(var(--accent)/0.15),transparent)]"
        />
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 md:py-24 lg:grid-cols-2">
          <div className="animate-fade-up space-y-6">
            <p className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-bullish" aria-hidden />
              Educational project · Every forecast explained
            </p>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.4rem] lg:leading-[1.1]">
              Interpretable market analytics,{" "}
              <span className="text-accent">not black-box predictions.</span>
            </h1>
            <p className="max-w-xl text-lg text-muted-foreground">
              Live quotes, technical indicators, ML forecasts with confidence ranges, news
              sentiment, risk scoring, and honest backtests — all in one dashboard.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <Link
                href="/dashboard"
                className="inline-flex h-11 items-center gap-2 rounded-lg bg-accent px-6 font-semibold text-accent-foreground shadow-sm transition-colors hover:bg-accent-hover"
              >
                Launch dashboard <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
              <Link
                href="/transparency"
                className="inline-flex h-11 items-center gap-2 rounded-lg border border-border bg-card px-6 font-semibold transition-colors hover:bg-card-hover"
              >
                How the models work
              </Link>
            </div>
            <p className="text-xs text-muted-foreground">
              Not financial advice. Forecasts are probabilistic and frequently wrong — by design,
              we show you when.
            </p>
          </div>
          <div className="animate-fade-up [animation-delay:150ms]">
            <HeroPreview />
          </div>
        </div>
      </section>

      {/* Features */}
      <section aria-labelledby="features-heading" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="mb-10 max-w-2xl">
          <h2 id="features-heading" className="text-2xl font-bold tracking-tight sm:text-3xl">
            Everything you need to understand a stock
          </h2>
          <p className="mt-2 text-muted-foreground">
            Not just signals — the data, the reasoning, and the uncertainty behind every number.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(({ Icon, title, description }) => (
            <div
              key={title}
              className="hover-lift rounded-xl border border-border bg-card p-5 hover:border-accent/40"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent/15">
                <Icon className="h-5 w-5 text-accent" aria-hidden />
              </div>
              <h3 className="mt-4 font-semibold">{title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section
        aria-labelledby="how-heading"
        className="border-y border-border bg-card/40"
      >
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <h2 id="how-heading" className="text-2xl font-bold tracking-tight sm:text-3xl">
            How it works
          </h2>
          <div className="mt-10 grid gap-8 md:grid-cols-3">
            {STEPS.map(({ step, title, description }) => (
              <div key={step} className="relative">
                <span className="text-sm font-bold text-accent">{step}</span>
                <h3 className="mt-2 font-semibold">{title}</h3>
                <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Honesty as a feature */}
      <section aria-labelledby="honesty-heading" className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div>
            <h2 id="honesty-heading" className="text-2xl font-bold tracking-tight sm:text-3xl">
              Built to be honest, not to sell certainty
            </h2>
            <p className="mt-3 text-muted-foreground">
              Retail investors are handed either black-box buy/sell signals with no explanation, or
              raw data with no interpretation. StockSense takes a third path: every forecast ships
              with its confidence, its reasoning, and its real backtested track record — even when
              the model loses to a coin flip.
            </p>
            <Link
              href="/transparency"
              className="mt-5 inline-flex items-center gap-1.5 font-semibold text-accent underline-offset-4 hover:underline"
            >
              Read the model transparency report <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          </div>
          <ul className="space-y-3">
            {[
              "Confidence scores and expected ranges on every forecast",
              "Plain-English factor attribution — why the model said what it said",
              "Walk-forward backtests vs naive baselines, with losses shown",
              "Full list of features, data sources, and known limitations",
            ].map((item) => (
              <li
                key={item}
                className="flex items-start gap-3 rounded-lg border border-border bg-card px-4 py-3 text-sm"
              >
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" aria-hidden />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Final CTA */}
      <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <div className="relative overflow-hidden rounded-2xl border border-border bg-card px-6 py-12 text-center sm:px-12">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_50%_80%_at_50%_120%,hsl(var(--accent)/0.18),transparent)]"
          />
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Start exploring the market — with the uncertainty included
          </h2>
          <p className="mx-auto mt-2 max-w-xl text-muted-foreground">
            Free, educational, and transparent about what it doesn&apos;t know.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Link
              href="/signup"
              className="inline-flex h-11 items-center gap-2 rounded-lg bg-accent px-6 font-semibold text-accent-foreground shadow-sm transition-colors hover:bg-accent-hover"
            >
              Create a free account <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
            <Link
              href="/login"
              className="inline-flex h-11 items-center rounded-lg border border-border bg-background px-6 font-semibold transition-colors hover:bg-muted"
            >
              Sign in
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
