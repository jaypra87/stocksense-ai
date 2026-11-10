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
 * where the API refuses to start one — too many sessions from this address,
 * or the server unreachable — which gets an explanation and a retry.
 */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, error, challenge, retry } = useAuth();
  const [slow, setSlow] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);

  // Past a few seconds the wait is almost certainly the backend cold start;
  // say so rather than leave a spinner that reads as broken.
  useEffect(() => {
    if (!loading) return;
    const t = setTimeout(() => setSlow(true), 4000);
    return () => clearTimeout(t);
  }, [loading]);

  if (user) return <>{children}</>;

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 px-4 text-center">
        <Spinner className="h-6 w-6" />
        {slow && (
          <p className="max-w-sm text-sm text-muted-foreground">
            Waking up the server. The free tier sleeps when idle; this can take up to a minute the
            first time.
          </p>
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
