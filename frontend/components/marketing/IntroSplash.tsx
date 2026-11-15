"use client";

import { ChevronDown } from "lucide-react";
import { useEffect, useRef } from "react";

// Full-screen opening panel for the landing page: the mark, the name, and a
// cue to scroll. The rest of the page sits directly below it. While this
// panel fills the viewport the site header is hidden (see the html[data-intro]
// rule in globals.css) so the logo is not shown twice; it fades in as soon as
// the visitor scrolls on.

export function IntroSplash() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const root = document.documentElement;
    const observer = new IntersectionObserver(
      ([entry]) => root.toggleAttribute("data-intro", entry.intersectionRatio > 0.5),
      { threshold: [0.5] },
    );
    observer.observe(el);
    return () => {
      observer.disconnect();
      root.removeAttribute("data-intro");
    };
  }, []);

  function scrollOn() {
    document.getElementById("hero")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <section
      ref={ref}
      aria-label="Welcome"
      className="intro-panel relative flex flex-col items-center justify-center border-b border-border px-4"
    >
      <div className="animate-fade-up flex flex-col items-center gap-6">
        <span className="flex h-24 w-24 items-center justify-center rounded-3xl bg-accent/15 sm:h-28 sm:w-28">
          <svg viewBox="0 0 32 32" className="h-14 w-14 sm:h-16 sm:w-16" aria-hidden>
            <path
              d="M6 22 L12 15 L16 18 L26 8"
              fill="none"
              stroke="hsl(var(--accent))"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M20 8 H26 V14"
              fill="none"
              stroke="hsl(var(--accent))"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <p className="text-4xl font-bold tracking-tight sm:text-5xl">
          StockSense <span className="text-accent">AI</span>
        </p>
      </div>

      <button
        type="button"
        onClick={scrollOn}
        className="absolute bottom-8 flex flex-col items-center gap-1 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground transition-colors hover:text-foreground"
      >
        Scroll
        <ChevronDown className="h-5 w-5 animate-bounce motion-reduce:animate-none" aria-hidden />
      </button>
    </section>
  );
}
