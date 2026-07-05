"use client";

import { createElement, useEffect, useRef } from "react";

// Scroll-reveal wrapper: fades content up whenever it enters the viewport,
// from either scroll direction — the class toggles off on exit so the
// animation replays on re-entry. Pure IntersectionObserver, no scroll
// listeners. Under prefers-reduced-motion the content is simply shown.

type RevealProps = {
  children: React.ReactNode;
  /** Stagger offset in ms, for sibling cards. */
  delay?: number;
  className?: string;
  /** Rendered element, so lists can keep their semantics. */
  as?: "div" | "li";
};

export function Reveal({ children, delay = 0, className, as = "div" }: RevealProps) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.classList.add("is-in");
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => el.classList.toggle("is-in", entry.isIntersecting),
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  return createElement(
    as,
    {
      ref,
      className: `reveal ${className ?? ""}`,
      style: delay ? { transitionDelay: `${delay}ms` } : undefined,
    },
    children,
  );
}
