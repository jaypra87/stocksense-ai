import {
  ArrowRight,
  Bell,
  Bot,
  BrainCircuit,
  Briefcase,
  CandlestickChart,
  FlaskConical,
  Gauge,
  KeyRound,
  LineChart,
  Lock,
  Newspaper,
  Search,
  ShieldAlert,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { ForecastPreview } from "@/components/marketing/ForecastPreview";
import { IntroSplash } from "@/components/marketing/IntroSplash";
import { Reveal } from "@/components/shared/Reveal";
import { ScrollBackground } from "@/components/marketing/ScrollBackground";
import { SITE_DESCRIPTION, SITE_NAME, SITE_TAGLINE } from "@/lib/site";

export const metadata: Metadata = {
  title: { absolute: `${SITE_NAME}: ${SITE_TAGLINE}` },
  description: SITE_DESCRIPTION,
  alternates: { canonical: "/" },
};

const PROOF_POINTS = [
  { value: "3", label: "Forecast horizons", detail: "1, 7 and 30 days ahead" },
  { value: "17", label: "Model inputs", detail: "Every one listed on this page" },
  { value: "200", label: "Trees per forest", detail: "Their vote share is the confidence" },
  { value: "6", label: "Risk factors", detail: "Each with its weight shown" },
  { value: "2", label: "Baselines to beat", detail: "In every backtest you run" },
  { value: "0", label: "Forecasts without a confidence score", detail: "It is part of the answer" },
];

const STEPS = [
  {
    Icon: Search,
    step: "1",
    title: "Search any ticker",
    description:
      "Autocomplete handles exchange suffixes such as BRK-B and VFV.TO. Quotes are live and history goes back up to five years.",
  },
  {
    Icon: LineChart,
    step: "2",
    title: "Read the full picture",
    description:
      "Price history, technical indicators, the forecast with its confidence and reasoning, risk factors and news sentiment, all on one page.",
  },
  {
    Icon: FlaskConical,
    step: "3",
    title: "Check it before you trust it",
    description:
      "Run a walk-forward backtest on that ticker and see how often the model was right compared with naive baselines. The losing runs are shown too.",
  },
];

const FEATURES = [
  {
    Icon: CandlestickChart,
    title: "Live quotes and charts",
    description: "Live quotes with up to five years of history, volume overlays and saved candles.",
  },
  {
    Icon: BrainCircuit,
    title: "Forecasts with confidence",
    description:
      "No bare buy or sell signals. Each forecast includes its probability, its expected range and the reasons behind it.",
  },
  {
    Icon: ShieldAlert,
    title: "Transparent risk scoring",
    description:
      "A composite score from 0 to 100 built from volatility, drawdown, volume, trend, model uncertainty and news sentiment.",
  },
  {
    Icon: Newspaper,
    title: "News sentiment",
    description: "Recent headlines are classified and summarised, then fed into the risk score.",
  },
  {
    Icon: Bell,
    title: "Watchlists and alerts",
    description: "Save tickers, set alert rules and review everything that has triggered.",
  },
  {
    Icon: FlaskConical,
    title: "Backtesting",
    description:
      "Walk-forward backtests with no lookahead, measured against naive baselines. You see the losing runs as well as the winning ones.",
  },
  {
    Icon: Briefcase,
    title: "Paper trading",
    description:
      "Practise with $100,000 of simulated money. Fractional shares, fills at the live quote, and a ledger that shows every trade.",
  },
  {
    Icon: Bot,
    title: "Stock-man, an analyst with receipts",
    description:
      "Ask about any stock or your portfolio. Every number comes from a tool call you can open, and he drafts trades he cannot place.",
  },
];

const FORMULAS = [
  {
    title: "The label",
    body: (
      <>
        r = (P<sub>t+h</sub> − P<sub>t</sub>) / P<sub>t</sub>
      </>
    ),
    caption:
      "The target is the forward return over the horizon. A move above the threshold for that horizon (0.5% for 1 day, 2% for 7 days, 4% for 30 days) is labelled bullish, a move below the negative threshold bearish, and anything in between neutral.",
  },
  {
    title: "Confidence",
    body: (
      <>
        confidence = max<sub>c</sub> p̂(c | x)
      </>
    ),
    caption:
      "The share of the forest's 200 trees that voted for the winning class. A confidence of 0.63 means 126 trees agreed and 74 did not. It appears on every forecast because it is part of the answer.",
  },
  {
    title: "Expected range",
    body: (
      <>
        [ P<sub>t</sub>(1 + r̂<sub>low</sub>), P<sub>t</sub>(1 + r̂<sub>high</sub>) ]
      </>
    ),
    caption:
      "The regressor's point estimate, widened by the spread of the individual tree predictions. When the trees disagree the band gets wider. Uncertainty is shown rather than averaged away.",
  },
  {
    title: "Risk score",
    body: (
      <>
        R = Σ w<sub>i</sub> · s<sub>i</sub> / Σ w<sub>i</sub>
      </>
    ),
    caption:
      "A weighted blend of six sub-scores, each from 0 to 100. If a factor is unavailable the remaining weights are renormalised, so the score never fills a gap with a guess.",
  },
];

const RISK_WEIGHTS = [
  { label: "Volatility (30-day)", weight: 25 },
  { label: "Drawdown", weight: 22 },
  { label: "Model uncertainty", weight: 16 },
  { label: "News sentiment", weight: 13 },
  { label: "Relative volume", weight: 12 },
  { label: "Trend", weight: 12 },
];

const FEATURE_GROUPS = [
  {
    title: "Trend ratios",
    count: 5,
    items: "Price vs SMA-7 / SMA-30 / SMA-100, SMA-7 vs SMA-30, price vs EMA-20",
  },
  {
    title: "Oscillators",
    count: 4,
    items: "RSI-14, MACD and MACD histogram (normalised by price), Bollinger band position",
  },
  {
    title: "Risk and volume",
    count: 3,
    items: "30-day volatility, drawdown from the rolling high, volume vs its own average",
  },
  {
    title: "Momentum",
    count: 5,
    items: "The last five daily returns, oldest to newest",
  },
];

const VALIDATION_POINTS = [
  {
    title: "Chronological splits, never shuffled",
    description:
      "Each ticker's history is split 80/20 in time order, so the model is always graded on data newer than anything it trained on. That is the only split that resembles real use.",
  },
  {
    title: "Walk-forward backtesting",
    description:
      "Forecast origins step forward by the horizon length so forward returns never overlap, and the model is retrained on an expanding window as it goes. It never sees the future.",
  },
  {
    title: "Two baselines to beat",
    description:
      "Every run is compared with always guessing the most common class and with predicting a zero return. When the model cannot beat those, the app says so.",
  },
  {
    title: "No headline accuracy number",
    description:
      "Accuracy varies by ticker, horizon and market regime. A single big number here would be marketing. Run the backtest on your ticker and get the real one.",
  },
];

const FAQ = [
  {
    q: "Is this financial advice?",
    a: "No. StockSense is an educational analytics project. Forecasts are probabilistic and often wrong, and every API response carries a disclaimer saying so.",
  },
  {
    q: "Which algorithm powers the forecasts?",
    a: "Two random forests per horizon. A classifier votes on direction, and its vote share is the confidence score. A regressor estimates the return, and the spread across its trees sets the price range. The details and the maths are on this page and in the transparency report.",
  },
  {
    q: "How accurate are the forecasts?",
    a: "It depends on the ticker and the market regime, so rather than quote a number we let you measure it. Run a walk-forward backtest on any stock and see the hit rate against naive baselines, losses included.",
  },
  {
    q: "Where does the data come from?",
    a: "Live quotes and history come from public market data providers. News sentiment comes from classified headlines. Every source is listed on the transparency page.",
  },
];

const JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "StockSense AI",
  applicationCategory: "FinanceApplication",
  description:
    "Stock analytics with ML forecasts, confidence ranges, transparent risk scoring, news sentiment and backtesting. Educational use only, not financial advice.",
  offers: { "@type": "Offer", price: "0" },
};

export default function LandingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(JSON_LD) }}
      />

      <ScrollBackground />

      <IntroSplash />

      {/* Hero */}
      <section id="hero" className="scroll-mt-14 border-b border-border">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 md:py-24 lg:grid-cols-[46fr_54fr]">
          <div className="animate-fade-up min-w-0 space-y-6">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Market analytics with the uncertainty included
            </p>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem] lg:leading-[1.08]">
              Stock forecasts that show their work.
            </h1>
            <p className="max-w-xl text-lg text-muted-foreground">
              Every forecast comes with a confidence score, an expected range, the factors behind it
              and a backtest you can run yourself.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <Link
                href="/dashboard"
                className="group inline-flex h-11 items-center gap-2 rounded-md bg-accent px-6 font-semibold text-accent-foreground transition-colors hover:bg-accent-hover"
              >
                Open the dashboard
                <ArrowRight
                  className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
                  aria-hidden
                />
              </Link>
              <Link
                href="/#model"
                className="inline-flex h-11 items-center rounded-md border border-border bg-card px-6 font-semibold transition-colors hover:border-accent/40 hover:bg-muted"
              >
                See how the model works
              </Link>
            </div>
            <p className="text-xs text-muted-foreground">
              Educational project, not financial advice. Forecasts are probabilistic and often
              wrong, and the app tells you when.
            </p>
          </div>
          {/* min-w-0 keeps the card from widening the page on narrow screens. */}
          <div className="animate-fade-up min-w-0 [animation-delay:150ms]">
            <ForecastPreview />
          </div>
        </div>
      </section>

      {/* Proof strip. Every cell is top-anchored with a fixed-height number
          row, so labels that wrap to two lines cannot push the figures out
          of line with their neighbours. */}
      <section aria-labelledby="glance-heading" className="border-b border-border bg-card/40">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 md:py-16">
          <Reveal className="mb-8">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              At a glance
            </p>
            <h2 id="glance-heading" className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
              The numbers behind every forecast.
            </h2>
          </Reveal>
          <dl className="grid grid-cols-2 overflow-hidden rounded-lg border border-border bg-card md:grid-cols-3">
            {PROOF_POINTS.map(({ value, label, detail }, i) => (
              <Reveal
                key={label}
                delay={(i % 3) * 70}
                className="-ml-px -mt-px flex flex-col border-l border-t border-border p-5 md:p-6"
              >
                <dt className="order-2 mt-2 text-sm font-semibold">{label}</dt>
                <dd className="order-1 flex h-12 items-center text-4xl font-bold tabular-nums tracking-tight">
                  {value}
                </dd>
                <dd className="order-3 mt-0.5 text-sm text-muted-foreground">{detail}</dd>
              </Reveal>
            ))}
          </dl>
        </div>
      </section>

      {/* How it works */}
      <section
        aria-labelledby="steps-heading"
        className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20"
      >
        <Reveal className="mb-12 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            How it works
          </p>
          <h2 id="steps-heading" className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
            From a ticker symbol to a forecast you can check.
          </h2>
        </Reveal>
        <ol className="grid gap-6 md:grid-cols-3">
          {STEPS.map(({ Icon, step, title, description }, i) => (
            <Reveal
              as="li"
              key={step}
              delay={i * 90}
              className="hover-lift group rounded-lg border border-border bg-card p-6 hover:border-accent/40"
            >
              <div className="flex items-center justify-between">
                <span className="flex h-10 w-10 items-center justify-center rounded-md bg-accent/10 transition-transform group-hover:-translate-y-0.5">
                  <Icon className="h-5 w-5 text-accent" aria-hidden />
                </span>
                <span className="font-mono text-sm font-semibold text-muted-foreground">
                  {step} / 3
                </span>
              </div>
              <h3 className="mt-4 font-semibold">{title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{description}</p>
            </Reveal>
          ))}
        </ol>
      </section>

      {/* Features */}
      <section aria-labelledby="features-heading" className="border-y border-border bg-card/40">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
          <Reveal className="mb-12 max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              What&apos;s inside
            </p>
            <h2
              id="features-heading"
              className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl"
            >
              The data, the reasoning and the uncertainty behind every number.
            </h2>
          </Reveal>
          <div className="grid overflow-hidden rounded-lg border border-border bg-card sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ Icon, title, description }, i) => (
              <Reveal
                key={title}
                delay={(i % 3) * 80}
                className="group -ml-px -mt-px border-l border-t border-border p-6 transition-colors hover:bg-card-hover"
              >
                <Icon
                  className="h-5 w-5 text-accent transition-transform group-hover:-translate-y-0.5"
                  aria-hidden
                />
                <h3 className="mt-4 font-semibold">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                  {description}
                </p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Model & math */}
      <section
        aria-labelledby="model-heading"
        id="model"
        className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6 md:py-20"
      >
        <Reveal className="mb-12 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Under the hood
          </p>
          <h2 id="model-heading" className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
            The model, the maths and where it fails.
          </h2>
          <p className="mt-3 text-muted-foreground">
            Nothing here is hidden. These are the algorithm, the formulas and the validation steps
            used in the codebase.
          </p>
        </Reveal>

        {/* Algorithm */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Reveal className="hover-lift rounded-lg border border-border bg-card p-7 hover:border-accent/40">
            <p className="font-mono text-xs font-semibold uppercase tracking-wide text-accent">
              Direction
            </p>
            <h3 className="mt-2 text-lg font-semibold">Random-forest classifier</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              200 decision trees (depth of at most 8, at least 20 samples per leaf) vote bullish,
              neutral or bearish. The winning class becomes the trend call, and the share of trees
              that voted for it becomes the confidence score, so 63% confident means 126 of the 200
              trees agreed. One forest is trained per horizon on data pooled across tickers.
            </p>
          </Reveal>
          <Reveal
            delay={90}
            className="hover-lift rounded-lg border border-border bg-card p-7 hover:border-accent/40"
          >
            <p className="font-mono text-xs font-semibold uppercase tracking-wide text-accent">
              Magnitude
            </p>
            <h3 className="mt-2 text-lg font-semibold">Random-forest regressor</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              A second forest estimates the forward return itself. Its point estimate sets the
              middle of the expected price range, and the disagreement between individual trees sets
              the width. A calm consensus gives a tight band and a split forest gives a wide one.
            </p>
          </Reveal>
        </div>

        {/* Math */}
        <div className="mt-6 grid gap-6 sm:grid-cols-2">
          {FORMULAS.map(({ title, body, caption }, i) => (
            <Reveal
              key={title}
              delay={(i % 2) * 90}
              className="rounded-lg border border-border bg-card p-6 transition-colors hover:border-accent/40"
            >
              <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {title}
              </h3>
              <p className="mt-3 overflow-x-auto py-1 font-mono text-base font-semibold">{body}</p>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{caption}</p>
            </Reveal>
          ))}
        </div>

        {/* Risk weights + feature groups */}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <Reveal className="rounded-lg border border-border bg-card p-7">
            <h3 className="font-semibold">How the risk score is weighted</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">
              These are the weights used by the risk engine. They sum to 1 and are renormalised when
              a factor is unavailable.
            </p>
            <ul className="mt-5 space-y-3.5">
              {RISK_WEIGHTS.map(({ label, weight }) => (
                <li key={label} className="text-sm">
                  <div className="flex items-baseline justify-between gap-4">
                    <span>{label}</span>
                    <span className="font-mono text-xs tabular-nums text-muted-foreground">
                      {weight}%
                    </span>
                  </div>
                  <div
                    className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted"
                    role="presentation"
                  >
                    <div
                      className="h-full rounded-full bg-accent"
                      style={{ width: `${weight * 4}%` }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </Reveal>
          <Reveal delay={90} className="rounded-lg border border-border bg-card p-7">
            <h3 className="font-semibold">17 inputs, all scale-free</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">
              Every feature is a ratio or an oscillator rather than a raw price, which is what lets
              one model learn across tickers. Each row uses only data up to that day. Forward
              returns are labels, never inputs.
            </p>
            <ul className="mt-5 divide-y divide-border">
              {FEATURE_GROUPS.map(({ title, count, items }) => (
                <li key={title} className="flex items-start justify-between gap-6 py-3.5">
                  <div>
                    <h4 className="text-sm font-semibold">{title}</h4>
                    <p className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{items}</p>
                  </div>
                  <span className="font-mono text-xs tabular-nums text-muted-foreground">
                    ×{count}
                  </span>
                </li>
              ))}
            </ul>
          </Reveal>
        </div>

        {/* Validation */}
        <Reveal className="mt-6 rounded-lg border border-border bg-card p-7">
          <h3 className="font-semibold">
            How accuracy is measured, and why there is no big number here
          </h3>
          <div className="mt-5 grid gap-x-10 gap-y-6 md:grid-cols-2">
            {VALIDATION_POINTS.map(({ title, description }) => (
              <div key={title}>
                <h4 className="text-sm font-semibold">{title}</h4>
                <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
          <Link
            href="/dashboard"
            className="group mt-6 inline-flex items-center gap-1.5 font-semibold text-accent"
          >
            Run a backtest on your ticker
            <ArrowRight
              className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
              aria-hidden
            />
          </Link>
        </Reveal>
      </section>

      {/* Security */}
      <section
        aria-labelledby="security-heading"
        id="security"
        className="scroll-mt-20 border-y border-border bg-card/40"
      >
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
          <Reveal className="mb-12 max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Security
            </p>
            <h2
              id="security-heading"
              className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl"
            >
              Plain, verifiable security.
            </h2>
            <p className="mt-3 text-muted-foreground">
              These are the controls in the codebase, which you can read for yourself.
            </p>
          </Reveal>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                Icon: Lock,
                title: "bcrypt-hashed credentials",
                description:
                  "Passwords are never stored or logged in plain text. Sessions live on the server and can be revoked.",
              },
              {
                Icon: Gauge,
                title: "Rate-limited API",
                description:
                  "Per-route limits on auth and data endpoints slow down brute force and scraping.",
              },
              {
                Icon: ShieldCheck,
                title: "Validated at both ends",
                description:
                  "Every payload is schema-checked twice, with Zod in the browser and Pydantic on the server.",
              },
              {
                Icon: KeyRound,
                title: "No brokerage access",
                description:
                  "StockSense is read-only market analytics. It never connects to a broker or touches your money.",
              },
              {
                Icon: Bot,
                title: "An analyst that cannot trade",
                description:
                  "Stock-man can only call read-only tools. A trade idea is a draft you confirm by hand, and a server-side check flags any figure it cannot trace.",
              },
              {
                Icon: Terminal,
                title: "Hardened headers",
                description:
                  "Strict transport and content security headers ship on every response from both apps.",
              },
              {
                Icon: FlaskConical,
                title: "Documented limitations",
                description:
                  "Data sources, model features and known failure modes are published on the transparency page.",
              },
            ].map(({ Icon, title, description }, i) => (
              <Reveal
                key={title}
                delay={(i % 3) * 80}
                className="hover-lift flex gap-4 rounded-lg border border-border bg-card p-5 hover:border-accent/40"
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-bullish/10">
                  <Icon className="h-5 w-5 text-bullish" aria-hidden />
                </span>
                <div>
                  <h3 className="text-sm font-semibold">{title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
                    {description}
                  </p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section
        aria-labelledby="faq-heading"
        className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20"
      >
        <Reveal className="mb-10 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Questions
          </p>
          <h2 id="faq-heading" className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
            Common questions.
          </h2>
        </Reveal>
        <Reveal className="max-w-3xl">
          {FAQ.map(({ q, a }) => (
            <details key={q} className="group border-b border-border">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-6 py-5 font-semibold transition-colors hover:text-accent [&::-webkit-details-marker]:hidden">
                {q}
                <ArrowRight
                  className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-90"
                  aria-hidden
                />
              </summary>
              <p className="max-w-2xl pb-6 text-sm leading-relaxed text-muted-foreground">{a}</p>
            </details>
          ))}
        </Reveal>
      </section>

      {/* Closing CTA */}
      <section className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-8 px-4 py-14 sm:px-6">
          <Reveal>
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
              See what the model knows, and what it does not.
            </h2>
            <p className="mt-2 text-muted-foreground">Free to use and open about its limits.</p>
          </Reveal>
          <Reveal delay={100} className="flex flex-wrap gap-3">
            <Link
              href="/dashboard"
              className="group inline-flex h-11 items-center gap-2 rounded-md bg-accent px-6 font-semibold text-accent-foreground transition-colors hover:bg-accent-hover"
            >
              Open the dashboard
              <ArrowRight
                className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
                aria-hidden
              />
            </Link>
            <Link
              href="/login"
              className="inline-flex h-11 items-center rounded-md border border-border bg-card px-6 font-semibold transition-colors hover:border-accent/40 hover:bg-muted"
            >
              Sign in
            </Link>
          </Reveal>
        </div>
      </section>
    </>
  );
}
