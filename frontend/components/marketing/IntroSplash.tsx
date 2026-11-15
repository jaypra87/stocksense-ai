"use client";

import { ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

// Full-screen opening panel for the landing page. The mark draws itself (tile
// scales in, the price line is stroked left to right, then the arrow head),
// after which the name is typed out, and finally the scroll cue appears. The
// rest of the page sits directly below. While this panel fills the viewport
// the site header is hidden (html[data-intro] in globals.css) so the logo is
// not shown twice; it fades in as soon as the visitor scrolls on.
//
// Timings are shared between the CSS keyframes on the SVG and the typing
// timer here: the line finishes drawing at ~1.2s, typing starts then.

const NAME = "StockSense";
const SUFFIX = "AI";
const FULL = `${NAME} ${SUFFIX}`;
const TYPING_START_MS = 1200;
const TYPING_STEP_MS = 75;

export function IntroSplash() {
  const ref = useRef<HTMLElement>(null);
  const [typed, setTyped] = useState(0);
  const [done, setDone] = useState(false);

  // Header hand-off.
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

  // Typewriter. Under reduced motion the name simply appears.
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setTyped(FULL.length);
      setDone(true);
      return;
    }
    const timers: ReturnType<typeof setTimeout>[] = [];
    for (let i = 1; i <= FULL.length; i++) {
      timers.push(setTimeout(() => setTyped(i), TYPING_START_MS + i * TYPING_STEP_MS));
    }
    // Keep the caret blinking briefly after the last letter, then drop it.
    timers.push(setTimeout(() => setDone(true), TYPING_START_MS + FULL.length * TYPING_STEP_MS + 900));
    return () => timers.forEach(clearTimeout);
  }, []);

  function scrollOn() {
    document.getElementById("hero")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const shown = FULL.slice(0, typed);
  const namePart = shown.slice(0, NAME.length);
  const suffixPart = shown.length > NAME.length + 1 ? shown.slice(NAME.length + 1) : "";
  const space = shown.length > NAME.length ? " " : "";

  return (
    <section
      ref={ref}
      aria-label="Welcome"
      className="intro-panel relative flex flex-col items-center justify-center border-b border-border px-4"
    >
      <div className="flex flex-col items-center gap-8 sm:gap-10">
        <span className="intro-tile flex h-32 w-32 items-center justify-center rounded-[2rem] bg-accent/15 sm:h-40 sm:w-40 lg:h-48 lg:w-48">
          <svg viewBox="0 0 32 32" className="h-20 w-20 sm:h-24 sm:w-24 lg:h-28 lg:w-28" aria-hidden>
            <path
              d="M6 22 L12 15 L16 18 L26 8"
              pathLength={1}
              className="intro-line"
              fill="none"
              stroke="hsl(var(--accent))"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M20 8 H26 V14"
              pathLength={1}
              className="intro-arrow"
              fill="none"
              stroke="hsl(var(--accent))"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>

        {/* The full name is always in the DOM for assistive tech and crawlers;
            the visible copy is the typed portion plus a caret. */}
        <p className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
          <span className="sr-only">{FULL}</span>
          <span aria-hidden className="whitespace-pre">
            {namePart}
            {space}
            <span className="text-accent">{suffixPart}</span>
            <span
              className={cn(
                "intro-caret ml-0.5 inline-block w-[3px] translate-y-[0.08em] rounded-sm bg-accent align-baseline",
                "h-[0.85em]",
                done && "hidden",
              )}
            />
          </span>
        </p>
      </div>

      <button
        type="button"
        onClick={scrollOn}
        className={cn(
          "absolute bottom-8 flex flex-col items-center gap-1 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground transition-opacity duration-700 hover:text-foreground",
          done ? "opacity-100" : "opacity-0",
        )}
      >
        Scroll
        <ChevronDown className="h-5 w-5 animate-bounce motion-reduce:animate-none" aria-hidden />
      </button>
    </section>
  );
}
