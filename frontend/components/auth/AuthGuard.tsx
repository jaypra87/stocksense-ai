"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { Turnstile, turnstileEnabled } from "@/components/auth/Turnstile";
import { Logo } from "@/components/shared/Logo";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";

/**
 * Wraps in-app pages. There is nothing to redirect to any more: a visitor
 * without a session gets one. What remains is the brief wait while that
 * happens (longer when the free-tier API is waking up) and the rare case
 * where the API refuses to start one, too many sessions from this address,
 * or the server unreachable, which gets an explanation and a retry.
 */
// A cold start on the free tier is usually under a minute; the bar is paced
// to that and never claims to be done.
const EXPECTED_WAKE_MS = 75_000;
const SLOW_AFTER_MS = 4_000;
const VERY_SLOW_AFTER_MS = 45_000;

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, error, challenge, retry } = useAuth();
  const [elapsed, setElapsed] = useState(0);
  const [token, setToken] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  // Past a few seconds the wait is almost certainly the backend cold start;
  // say so, and show it moving, rather than leave a spinner that reads as
  // broken.
  useEffect(() => {
    if (!loading) return;
    const started = Date.now();
    const tick = setInterval(() => setElapsed(Date.now() - started), 500);
    return () => clearInterval(tick);
  }, [loading]);

  if (user) return <>{children}</>;

  if (loading) {
    const slow = elapsed >= SLOW_AFTER_MS;
    const progress = Math.min(95, (elapsed / EXPECTED_WAKE_MS) * 100);
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
        <Spinner className="h-6 w-6" />
        {slow && (
          <div className="animate-fade-up w-full max-w-sm space-y-3">
            <p className="text-sm text-muted-foreground">
              {elapsed < VERY_SLOW_AFTER_MS
                ? "Waking up the server. The free tier sleeps when idle; this usually takes under a minute."
                : "Still waking up. After a long idle the free tier can take a minute or two. Hang on, it is still trying."}
            </p>
            <div
              role="progressbar"
              aria-label="Waking up the server"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(progress)}
              className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
            >
              <div
                className="h-full rounded-full bg-accent transition-[width] duration-500 ease-linear"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs tabular-nums text-muted-foreground">
              {Math.floor(elapsed / 1000)}s
            </p>
          </div>
        )}
      </div>
    );
  }

  async function onRetry() {
    setRetrying(true);
    try {
      await retry(token);
    } finally {
      setRetrying(false);
      setToken(null);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-5 rounded-xl border border-border bg-card p-6 text-center">
        <div className="flex justify-center">
          <Logo />
        </div>
        <div className="space-y-1">
          <h1 className="text-lg font-semibold">
            {challenge ? "Quick check before we continue" : "Couldn't start your session"}
          </h1>
          <p className="text-sm text-muted-foreground">
            {challenge
              ? "A lot of sessions have started from your network. Confirm you're human to get one."
              : (error ?? "Something went wrong.")}
          </p>
        </div>
        {challenge && turnstileEnabled && <Turnstile action="guest" onToken={setToken} />}
        <Button
          onClick={onRetry}
          disabled={retrying || (challenge && turnstileEnabled && !token)}
          className="w-full"
        >
          {retrying ? "Starting…" : "Try again"}
        </Button>
      </div>
    </div>
  );
}
