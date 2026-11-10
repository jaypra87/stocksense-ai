"use client";

import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { Turnstile, turnstileEnabled } from "@/components/auth/Turnstile";
import { Logo } from "@/components/shared/Logo";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ApiError } from "@/lib/api/client";

const BRAND_POINTS = [
  "Forecasts with confidence scores and expected ranges",
  "Transparent risk breakdowns — every factor shown",
  "Honest walk-forward backtests vs naive baselines",
];

/**
 * Optional account screens. Nobody is sent here: the app works as a guest from
 * the first visit. "Save your account" attaches an email and password to the
 * current guest so its watchlist and alerts follow the user to other devices;
 * "Sign in" returns to an existing account and brings the guest's data along.
 */
export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const { user, login, signup } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [slow, setSlow] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [widgetKey, setWidgetKey] = useState(0);
  const slowTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const isLogin = mode === "login";
  const isGuest = user?.is_guest ?? true;
  const hasAccount = user !== null && !user.is_guest;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSlow(false);
    setBusy(true);
    slowTimer.current = setTimeout(() => setSlow(true), 4000);
    try {
      await (isLogin ? login(email, password, token) : signup(email, password, token));
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
      // A Turnstile token is single-use; a fresh widget gets a fresh one.
      setToken(null);
      setWidgetKey((k) => k + 1);
    } finally {
      if (slowTimer.current) clearTimeout(slowTimer.current);
      setSlow(false);
      setBusy(false);
    }
  }

  const heading = isLogin ? "Sign in" : hasAccount ? "You already have an account" : "Save your account";
  const blurb = isLogin
    ? isGuest
      ? "Anything you've saved as a guest comes with you."
      : "Sign in to a different account."
    : hasAccount
      ? `You're signed in as ${user?.email}.`
      : "Keep your watchlist and alerts on every device. Nothing is lost — your guest data stays with you.";

  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel (desktop only) */}
      <div className="relative hidden flex-col justify-between overflow-hidden border-r border-border bg-card p-10 lg:flex">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_20%_0%,hsl(var(--accent)/0.14),transparent)]"
        />
        <Logo />
        <div className="space-y-5">
          <h2 className="text-2xl font-bold tracking-tight">
            Market analytics that show their work.
          </h2>
          <ul className="space-y-3">
            {BRAND_POINTS.map((point) => (
              <li key={point} className="flex items-start gap-3 text-sm text-muted-foreground">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-accent" aria-hidden />
                {point}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-xs text-muted-foreground">
          Educational project — not financial advice.
        </p>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm space-y-6">
          <div className="lg:hidden">
            <Logo />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{heading}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{blurb}</p>
          </div>

          {!isLogin && hasAccount ? (
            <Button onClick={() => router.push("/dashboard")} className="w-full">
              Back to the dashboard
            </Button>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4">
              <Input
                type="email"
                label="Email"
                autoComplete="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  label="Password"
                  autoComplete={isLogin ? "current-password" : "new-password"}
                  required
                  minLength={8}
                  maxLength={72}
                  placeholder={isLogin ? "Your password" : "At least 8 characters"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-[34px] text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>

              {turnstileEnabled && (
                <Turnstile key={widgetKey} action={isLogin ? "login" : "signup"} onToken={setToken} />
              )}

              {error && (
                <p role="alert" className="text-sm text-bearish">
                  {error}
                </p>
              )}
              {busy && slow && (
                <p className="text-xs text-muted-foreground">
                  Still working — the server may be waking up.
                </p>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={busy || (turnstileEnabled && !token)}
              >
                {busy ? "Please wait…" : isLogin ? "Sign in" : "Save account"}
              </Button>
            </form>
          )}

          <p className="text-center text-sm text-muted-foreground">
            {isLogin ? (
              <>
                No account yet?{" "}
                <Link href="/signup" className="font-medium text-accent hover:underline">
                  Save your guest session as one
                </Link>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <Link href="/login" className="font-medium text-accent hover:underline">
                  Sign in
                </Link>
              </>
            )}
            {" · "}
            <Link href="/dashboard" className="font-medium hover:underline">
              Continue as guest
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
