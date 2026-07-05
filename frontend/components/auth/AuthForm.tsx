"use client";

import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { Logo } from "@/components/shared/Logo";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ApiError } from "@/lib/api/client";

const BRAND_POINTS = [
  "Forecasts with confidence scores and expected ranges",
  "Transparent risk breakdowns — every factor shown",
  "Honest walk-forward backtests vs naive baselines",
];

export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const router = useRouter();
  const { login, signup } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const isLogin = mode === "login";

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await (isLogin ? login(email, password) : signup(email, password));
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

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
            <h1 className="text-2xl font-bold tracking-tight">
              {isLogin ? "Welcome back" : "Create your account"}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {isLogin ? "Sign in to your dashboard." : "Start tracking stocks in seconds."}
            </p>
          </div>

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
                placeholder={isLogin ? "Your password" : "At least 8 characters"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute right-2 top-[34px] rounded p-1 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" aria-hidden />
                ) : (
                  <Eye className="h-4 w-4" aria-hidden />
                )}
              </button>
            </div>

            {error && (
              <p
                role="alert"
                className="rounded-lg border border-bearish/40 bg-bearish/10 px-3 py-2 text-sm text-bearish"
              >
                {error}
              </p>
            )}

            <Button type="submit" loading={busy} className="w-full">
              {isLogin ? "Sign in" : "Create account"}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            {isLogin ? "No account? " : "Already have an account? "}
            <Link
              href={isLogin ? "/signup" : "/login"}
              className="font-semibold text-accent underline-offset-4 hover:underline"
            >
              {isLogin ? "Sign up" : "Sign in"}
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
