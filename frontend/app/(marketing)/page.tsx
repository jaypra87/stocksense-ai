import {
  ArrowRight,
  Bell,
  BrainCircuit,
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

import { CodeTerminal } from "@/components/marketing/CodeTerminal";
import { Reveal } from "@/components/shared/Reveal";
import { ScrollBackground } from "@/components/marketing/ScrollBackground";

export const metadata: Metadata = {
  title: { absolute: "StockSense AI — Interpretable stock analytics, not black-box predictions" },
  description:
    "Every forecast comes with a confidence score, an expected range, a plain-English explanation, a transparent risk breakdown, and honest backtests. Educational only.",
  alternates: { canonical: "/" },
};

const API_DOCS_URL = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`;

const PROOF_POINTS = [
  { value: "3", label: "Forecast horizons — 1d, 7d, 30d" },
  { value: "17", label: "Model inputs, every one listed below" },
  { value: "6", label: "Risk factors, every weight shown" },
  { value: "0", label: "Forecasts shipped without a confidence score" },
];

const STEPS = [
  {
    Icon: Search,
    step: "1",
    title: "Search any ticker",
    description:
      "Autocomplete with exchange-suffix support — AAPL, BRK-B, VFV.TO — backed by live quotes and up to five years of history.",
  },
  {
    Icon: LineChart,
    step: "2",
    title: "Read the full picture",
    description:
      "Price history, technical indicators, a forecast with its confidence and reasoning, risk factors, and news sentiment on one page.",
  },
  {
    Icon: FlaskConical,
    step: "3",
    title: "Verify before you trust",
    description:
      "Run a walk-forward backtest on that exact ticker and see the model's real hit rate against naive baselines — losses included.",
  },
];

const FEATURES = [
  {
    Icon: CandlestickChart,
    title: "Live quotes & charts",
    description: "Real-time quotes with 1D–5Y history, volume overlays, and persistent candles.",
  },
  {
    Icon: BrainCircuit,
    title: "Forecasts with confidence",
    description:
      "Never a bare buy/sell signal. Every call ships its probability, expected range, and reasoning.",
  },
  {
    Icon: ShieldAlert,
    title: "Transparent risk scoring",
    description:
      "A 0–100 composite from volatility, drawdown, volume, trend, model uncertainty, and sentiment.",
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

const FORMULAS = [
  {
    title: "The label",
    body: (
      <>
        r = (P<sub>t+h</sub> − P<sub>t</sub>) / P<sub>t</sub>
      </>
    ),
    caption:
      "The target is the forward return over the horizon. Bullish if r clears a per-horizon threshold (+0.5% for 1d, +2% for 7d, +4% for 30d), bearish below the negative threshold, neutral between.",
  },
  {
    title: "Confidence",
    body: <>confidence = max<sub>c</sub> p̂(c | x)</>,
    caption:
      "The share of the forest's 200 trees voting for the winning class. 0.63 means 126 trees agreed — and 74 didn't. It's shown on every forecast because it's part of the answer.",
  },
  {
    title: "Expected range",
    body: (
      <>
        [ P<sub>t</sub>(1 + r̂<sub>low</sub>), P<sub>t</sub>(1 + r̂<sub>high</sub>) ]
      </>
    ),
    caption:
      "The regressor's point estimate widened by the spread of per-tree predictions. When the trees disagree, the band gets wider — uncertainty is displayed, not averaged away.",
  },
  {
    title: "Risk score",
    body: (
      <>
        R = Σ w<sub>i</sub> · s<sub>i</sub> / Σ w<sub>i</sub>
      </>
    ),
    caption:
      "A weighted blend of six 0–100 sub-scores. If a factor is unavailable, the weights renormalize over what's left — the score never silently fills gaps with guesses.",
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
    items: "RSI-14, MACD and MACD histogram (normalized by price), Bollinger-band position",
  },
  {
    title: "Risk & volume",
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
      "Each ticker's history is split 80/20 in time order. The model is always graded on data newer than anything it trained on — the only split that mimics real use.",
  },
  {
    title: "Walk-forward backtesting",
    description:
      "Forecast origins step forward by the horizon length so forward returns never overlap, and the model is retrained on an expanding window as it walks — no peeking at the future, ever.",
  },
  {
    title: "Two baselines to beat",
    description:
      "Every run is compared against always guessing the most common class, and against predicting zero return. A model that can't beat those isn't a model — and when it can't, the app says so.",
  },
  {
    title: "No headline accuracy number",
    description:
      "Accuracy genuinely varies by ticker, horizon, and market regime. Quoting one big number here would be marketing, not measurement — run the backtest on your ticker and get the real one.",
  },
];

const FAQ = [
  {
    q: "Is this financial advice?",
    a: "No. StockSense is an educational analytics project. Forecasts are probabilistic, frequently wrong, and every response says so — the disclaimer is part of the API contract, not fine print.",
  },
  {
    q: "Which algorithm powers the forecasts?",
    a: "Two random forests per horizon: a classifier that votes on direction (its vote share is the confidence score) and a regressor that estimates the return, with the spread across trees setting the price range. Details, hyperparameters, and the math are on this page and the transparency report.",
  },
  {
    q: "How accurate are the forecasts?",
    a: "It depends on the ticker and regime, and we'd rather show you than claim a number: run a walk-forward backtest on any stock and see the model's real hit rate against naive baselines, losses included.",
  },
  {
    q: "Where does the data come from?",
    a: "Live quotes and history come from public market-data providers, news sentiment from classified headlines. Every data source is listed on the transparency page.",
  },
  {
    q: "Can I build on top of it?",
    a: "Yes — the dashboard is backed by a documented REST API with interactive OpenAPI docs, using standard Bearer-token auth. The link is in the developers section below.",
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

      <ScrollBackground />

      {/* Hero */}
      <section className="border-b border-border">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-16 sm:px-6 md:py-24 lg:grid-cols-[46fr_54fr]">
          <div className="animate-fade-up space-y-6">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Market analytics, uncertainty included
            </p>
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl lg:text-[3.25rem] lg:leading-[1.08]">
              Interpretable stock analytics, not black-box predictions.
            </h1>
            <p className="max-w-xl text-lg text-muted-foreground">
              Every forecast ships with a confidence score, an expected range, the factors behind
              it, and a backtest you can run yourself. In the dashboard, or over one REST call.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <Link
                href="/signup"
                className="group inline-flex h-11 items-center gap-2 rounded-md bg-accent px-6 font-semibold text-accent-foreground transition-colors hover:bg-accent-hover"
              >
                Create a free account
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
              Educational project — not financial advice. Forecasts are probabilistic and
              frequently wrong; we show you when.
            </p>
          </div>
          <div className="animate-fade-up [animation-delay:150ms]">
            <CodeTerminal />
          </div>
        </div>
      </section>

      {/* Proof strip */}
      <section aria-label="At a glance" className="border-b border-border bg-card/40">
        <dl className="mx-auto grid max-w-6xl grid-cols-2 gap-px px-4 py-8 sm:px-6 md:grid-cols-4 md:py-10">
          {PROOF_POINTS.map(({ value, label }, i) => (
            <Reveal key={label} delay={i * 70} className="flex flex-col-reverse px-2 py-3 md:px-4">
              <dt className="mt-1 text-sm text-muted-foreground">{label}</dt>
              <dd className="text-3xl font-bold tabular-nums tracking-tight">{value}</dd>
            </Reveal>
          ))}
        </dl>
      </section>

      {/* How it works */}
      <section aria-labelledby="steps-heading" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
        <Reveal className="mb-12 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            How it works
          </p>
          <h2 id="steps-heading" className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
            From a ticker symbol to a verified forecast.
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
            <h2 id="features-heading" className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
              The data, the reasoning, and the uncertainty behind every number.
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
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{description}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Model & math */}
      <section aria-labelledby="model-heading" id="model" className="mx-auto max-w-6xl scroll-mt-20 px-4 py-16 sm:px-6 md:py-20">
        <Reveal className="mb-12 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Under the hood
          </p>
          <h2 id="model-heading" className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
            The model, the math, and where it fails.
          </h2>
          <p className="mt-3 text-muted-foreground">
            Nothing here is proprietary or hidden. This is the actual algorithm, the actual
            formulas, and the actual validation discipline in the codebase.
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
              200 decision trees (depth ≤ 8, ≥ 20 samples per leaf) vote bullish, neutral, or
              bearish. The winning class becomes the trend call, and the share of trees that voted
              for it becomes the confidence score — so &ldquo;63% confident&rdquo; is a literal
              vote count, not a vibe. One forest is trained per horizon on data pooled across
              tickers.
            </p>
          </Reveal>
          <Reveal delay={90} className="hover-lift rounded-lg border border-border bg-card p-7 hover:border-accent/40">
            <p className="font-mono text-xs font-semibold uppercase tracking-wide text-accent">
              Magnitude
            </p>
            <h3 className="mt-2 text-lg font-semibold">Random-forest regressor</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              A twin forest estimates the forward return itself. Its point estimate sets the middle
              of the expected price range, and the disagreement between individual trees sets the
              width — a calm consensus gives a tight band, a split forest gives a wide one.
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
              <p className="mt-3 overflow-x-auto rounded-md bg-[#0b1120] px-4 py-3 font-mono text-sm text-slate-200">
                {body}
              </p>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{caption}</p>
            </Reveal>
          ))}
        </div>

        {/* Risk weights + feature groups */}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <Reveal className="rounded-lg border border-border bg-card p-7">
            <h3 className="font-semibold">How the risk score is weighted</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">
              The exact weights from the risk engine — they sum to 1 and renormalize when a factor
              is unavailable.
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
                  <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-muted" role="presentation">
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
              Every feature is a ratio or an oscillator, never a raw price — that&apos;s what lets
              one global model learn across tickers. Each row uses only data up to that day;
              forward returns are labels, never inputs.
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
          <h3 className="font-semibold">How accuracy is measured — and why there&apos;s no big number here</h3>
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
      <section aria-labelledby="security-heading" id="security" className="scroll-mt-20 border-y border-border bg-card/40">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
          <Reveal className="mb-12 max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Security
            </p>
            <h2 id="security-heading" className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
              Boring, verifiable security.
            </h2>
            <p className="mt-3 text-muted-foreground">
              No badges we didn&apos;t earn — just the controls actually in the codebase, which you
              can read.
            </p>
          </Reveal>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                Icon: Lock,
                title: "bcrypt-hashed credentials",
                description:
                  "Passwords are never stored or logged in plain text. Sessions use short-lived JWTs.",
              },
              {
                Icon: Gauge,
                title: "Rate-limited API",
                description:
                  "Per-route limits on auth and data endpoints blunt brute-force and scraping attempts.",
              },
              {
                Icon: ShieldCheck,
                title: "Validated at both ends",
                description:
                  "Every payload is schema-checked twice — Zod in the browser, Pydantic on the server.",
              },
              {
                Icon: KeyRound,
                title: "No brokerage access",
                description:
                  "StockSense is read-only market analytics. It never connects to your broker or touches your money.",
              },
              {
                Icon: Terminal,
                title: "Hardened headers",
                description:
                  "Strict transport and content-security headers ship on every response, both apps.",
              },
              {
                Icon: FlaskConical,
                title: "Documented limitations",
                description:
                  "Data sources, model features, and known failure modes are published, not buried.",
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
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{description}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Developers */}
      <section aria-labelledby="developers-heading" id="developers" className="scroll-mt-20 bg-[#0b1120]">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
          <Reveal className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Developers
            </p>
            <h2 id="developers-heading" className="mt-3 text-2xl font-bold tracking-tight text-white sm:text-3xl">
              Documentation you can execute.
            </h2>
            <p className="mt-3 text-slate-400">
              The API reference is interactive OpenAPI — try every endpoint from the browser. The
              transparency report covers the models: features, data sources, training discipline,
              and where they fail.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <a
                href={API_DOCS_URL}
                className="group inline-flex h-11 items-center gap-2 rounded-md bg-white px-6 font-semibold text-slate-900 transition-colors hover:bg-slate-200"
              >
                Open the API reference
                <ArrowRight
                  className="h-4 w-4 transition-transform group-hover:translate-x-0.5"
                  aria-hidden
                />
              </a>
              <Link
                href="/transparency"
                className="inline-flex h-11 items-center rounded-md border border-slate-700 px-6 font-semibold text-white transition-colors hover:border-slate-500"
              >
                Model transparency report
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      {/* FAQ */}
      <section aria-labelledby="faq-heading" className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
        <Reveal className="mb-10 max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            Questions
          </p>
          <h2 id="faq-heading" className="mt-3 text-2xl font-bold tracking-tight sm:text-3xl">
            Asked before, answered plainly.
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
              See what the model actually knows.
            </h2>
            <p className="mt-2 text-muted-foreground">
              Free, transparent, and honest about what it doesn&apos;t know.
            </p>
          </Reveal>
          <Reveal delay={100} className="flex flex-wrap gap-3">
            <Link
              href="/signup"
              className="group inline-flex h-11 items-center gap-2 rounded-md bg-accent px-6 font-semibold text-accent-foreground transition-colors hover:bg-accent-hover"
            >
              Create a free account
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
