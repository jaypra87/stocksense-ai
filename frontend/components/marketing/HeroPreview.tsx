// Static, dependency-free product mock for the hero: a stylized forecast card.
// Purely decorative (aria-hidden) — real charts live in the app.
export function HeroPreview() {
  return (
    <div
      aria-hidden
      className="hover-lift relative rounded-2xl border border-border bg-card p-5 shadow-xl"
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-bold">NVDA</div>
          <div className="text-xs text-muted-foreground">NVIDIA Corporation</div>
        </div>
        <span className="rounded-full bg-bullish/15 px-2.5 py-1 text-xs font-semibold text-bullish">
          Bullish · 68% confidence
        </span>
      </div>

      <svg viewBox="0 0 400 140" className="mt-4 w-full" role="presentation">
        <defs>
          <linearGradient id="hero-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="hsl(var(--bullish))" stopOpacity="0.3" />
            <stop offset="100%" stopColor="hsl(var(--bullish))" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d="M0 110 C30 100, 45 118, 70 104 S 115 70, 140 82 S 185 96, 210 74 S 255 40, 280 52 S 330 64, 355 38 L 400 30"
          fill="none"
          stroke="hsl(var(--bullish))"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <path
          d="M0 110 C30 100, 45 118, 70 104 S 115 70, 140 82 S 185 96, 210 74 S 255 40, 280 52 S 330 64, 355 38 L 400 30 L 400 140 L 0 140 Z"
          fill="url(#hero-fill)"
        />
        {/* Dashed forecast cone */}
        <path
          d="M355 38 L 400 18 M355 38 L 400 46"
          fill="none"
          stroke="hsl(var(--accent))"
          strokeWidth="1.5"
          strokeDasharray="4 4"
        />
      </svg>

      <div className="mt-4 grid grid-cols-3 gap-3 text-center">
        {[
          ["Expected range", "$128 – $142"],
          ["Risk score", "54 / 100"],
          ["Sentiment", "Positive"],
        ].map(([label, value]) => (
          <div key={label} className="rounded-lg border border-border bg-background/50 px-2 py-2.5">
            <div className="text-[11px] text-muted-foreground">{label}</div>
            <div className="mt-0.5 text-sm font-semibold tabular-nums">{value}</div>
          </div>
        ))}
      </div>

      <p className="mt-4 border-t border-border pt-3 text-[11px] text-muted-foreground">
        Illustrative example · Educational only, not financial advice
      </p>
    </div>
  );
}
