"use client";

import { useEffect, useRef, useState } from "react";

const DURATION_MS = 700;

// Eases a number from its previous value to the new one, for headline
// figures that would otherwise snap. Reduced-motion users get the value
// immediately; subsequent updates (the 30s quote poll) ease from where they
// were rather than from zero.
export function useCountUp(target: number | undefined): number | undefined {
  const [value, setValue] = useState(target);
  const from = useRef(target ?? 0);

  useEffect(() => {
    if (target == null) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      from.current = target;
      setValue(target);
      return;
    }
    const start = performance.now();
    const base = from.current;
    let frame = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / DURATION_MS);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(base + (target - base) * eased);
      if (t < 1) frame = requestAnimationFrame(tick);
      else from.current = target;
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target]);

  return value;
}
