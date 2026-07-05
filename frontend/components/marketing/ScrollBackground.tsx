"use client";

import { useEffect, useRef } from "react";

// Fixed full-viewport canvas behind the landing page: three faint "price path"
// sine lines plus two soft accent glows. Time drifts them slowly; scrolling
// shifts their phase and vertical position, so the background visibly responds
// to the user moving through the page. Everything stays bounded (phase math,
// not translation), and prefers-reduced-motion gets a single static frame.

const LINES = [
  { band: 0.24, amp1: 42, freq1: 0.0032, amp2: 16, freq2: 0.010, drift: 0.14, scrollPhase: 0.0016, width: 1.5 },
  { band: 0.52, amp1: 34, freq1: 0.0026, amp2: 20, freq2: 0.013, drift: 0.10, scrollPhase: 0.0011, width: 1.25 },
  { band: 0.78, amp1: 48, freq1: 0.0021, amp2: 14, freq2: 0.008, drift: 0.07, scrollPhase: 0.0022, width: 1.5 },
];

export function ScrollBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let width = 0;
    let height = 0;
    let scroll = window.scrollY;
    let easedScroll = scroll;
    let frame = 0;
    let isDark = document.documentElement.classList.contains("dark");

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = (t: number) => {
      ctx.clearRect(0, 0, width, height);
      const [r, g, b] = isDark ? [96, 150, 250] : [37, 99, 235];
      const glowAlpha = isDark ? 0.07 : 0.05;
      const lineAlpha = isDark ? 0.14 : 0.1;

      // Soft glows, drifting on opposite parallax rates.
      const glows: Array<[number, number, number]> = [
        [width * 0.82, height * 0.18 + Math.sin(easedScroll * 0.0009) * 90, Math.max(width, height) * 0.42],
        [width * 0.08, height * 0.8 - Math.sin(easedScroll * 0.0006 + 2) * 110, Math.max(width, height) * 0.36],
      ];
      for (const [gx, gy, radius] of glows) {
        const gradient = ctx.createRadialGradient(gx, gy, 0, gx, gy, radius);
        gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${glowAlpha})`);
        gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);
      }

      // Price-path lines: scroll advances their phase, time drifts them slowly.
      LINES.forEach((line, i) => {
        const phase = t * 0.001 * line.drift + easedScroll * line.scrollPhase + i * 2.1;
        const baseY = height * line.band + Math.sin(easedScroll * 0.0007 + i * 1.7) * 26;
        ctx.beginPath();
        for (let x = 0; x <= width; x += 6) {
          const y =
            baseY +
            line.amp1 * Math.sin(x * line.freq1 + phase) +
            line.amp2 * Math.sin(x * line.freq2 - phase * 0.6);
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${lineAlpha})`;
        ctx.lineWidth = line.width;
        ctx.stroke();
      });
    };

    const loop = (t: number) => {
      easedScroll += (scroll - easedScroll) * 0.08;
      draw(t);
      frame = requestAnimationFrame(loop);
    };

    const onScroll = () => {
      scroll = window.scrollY;
    };
    const onResize = () => {
      resize();
      if (reducedMotion) draw(0);
    };

    // Theme flips (next-themes toggles the `dark` class) recolor the canvas.
    const themeObserver = new MutationObserver(() => {
      isDark = document.documentElement.classList.contains("dark");
      if (reducedMotion) draw(0);
    });
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    resize();
    window.addEventListener("resize", onResize);
    if (reducedMotion) {
      draw(0);
    } else {
      window.addEventListener("scroll", onScroll, { passive: true });
      frame = requestAnimationFrame(loop);
    }

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", onResize);
      window.removeEventListener("scroll", onScroll);
      themeObserver.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10"
    />
  );
}
