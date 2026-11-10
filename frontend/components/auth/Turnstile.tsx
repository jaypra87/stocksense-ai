"use client";

import { useEffect, useRef } from "react";

import { env } from "@/lib/env";

/**
 * Cloudflare Turnstile widget. Renders nothing when no site key is configured,
 * so the app behaves identically with bot protection off.
 *
 * `onToken` receives a fresh token when the (usually invisible) check passes,
 * and `null` when a token expires or the check errors, so the caller always
 * knows whether it currently holds something it can send.
 */

type TurnstileApi = {
  render: (el: HTMLElement, opts: Record<string, unknown>) => string;
  remove: (id: string) => void;
  reset: (id: string) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileApi;
    __turnstileReady?: Promise<TurnstileApi>;
  }
}

const SCRIPT_SRC = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

function loadTurnstile(): Promise<TurnstileApi> {
  if (window.turnstile) return Promise.resolve(window.turnstile);
  if (!window.__turnstileReady) {
    window.__turnstileReady = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = SCRIPT_SRC;
      script.async = true;
      script.defer = true;
      script.onload = () =>
        window.turnstile ? resolve(window.turnstile) : reject(new Error("turnstile missing"));
      script.onerror = () => reject(new Error("turnstile failed to load"));
      document.head.appendChild(script);
    });
  }
  return window.__turnstileReady;
}

export const turnstileEnabled = Boolean(env.NEXT_PUBLIC_TURNSTILE_SITE_KEY);

export function Turnstile({
  action,
  onToken,
}: {
  action: string;
  onToken: (token: string | null) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const siteKey = env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;
  const latest = useRef(onToken);
  latest.current = onToken;

  useEffect(() => {
    if (!siteKey || !container.current) return;
    let widgetId: string | undefined;
    let cancelled = false;

    loadTurnstile()
      .then((api) => {
        if (cancelled || !container.current) return;
        widgetId = api.render(container.current, {
          sitekey: siteKey,
          action,
          theme: "auto",
          size: "flexible",
          callback: (token: string) => latest.current(token),
          "expired-callback": () => latest.current(null),
          "error-callback": () => latest.current(null),
        });
      })
      .catch(() => latest.current(null));

    return () => {
      cancelled = true;
      if (widgetId && window.turnstile) window.turnstile.remove(widgetId);
    };
  }, [siteKey, action]);

  if (!siteKey) return null;
  return <div ref={container} className="min-h-[65px]" />;
}
