"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { Card, CardTitle } from "@/components/ui/Card";
import { cn } from "@/lib/utils";
import type { Range } from "@/types/stock";

const RANGES: Range[] = ["1d", "5d", "1m", "6m", "ytd", "1y", "5y"];
const RANGE_KEY = "stocksense_default_range";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [defaultRange, setDefaultRange] = useState<Range>("1y");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = window.localStorage.getItem(RANGE_KEY) as Range | null;
    if (saved) setDefaultRange(saved);
  }, []);

  function chooseRange(r: Range) {
    setDefaultRange(r);
    window.localStorage.setItem(RANGE_KEY, r);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">Preferences are stored on this device.</p>
      </div>

      <Card className="space-y-2">
        <CardTitle>Account</CardTitle>
        <p className="text-sm">
          Signed in as <span className="font-semibold">{user?.email}</span>
        </p>
        <button
          onClick={logout}
          className="w-fit rounded-lg border border-border px-3 py-1.5 text-sm text-bearish transition-colors hover:bg-muted"
        >
          Sign out
        </button>
      </Card>

      <Card className="space-y-3">
        <CardTitle>Appearance</CardTitle>
        {mounted && (
          <div className="flex gap-2">
            {(["light", "dark"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTheme(t)}
                className={cn(
                  "rounded-lg border px-4 py-2 text-sm capitalize transition-colors",
                  theme === t
                    ? "border-accent bg-accent/10 text-accent"
                    : "border-border text-muted-foreground hover:bg-muted",
                )}
              >
                {t}
              </button>
            ))}
          </div>
        )}
      </Card>

      <Card className="space-y-3">
        <CardTitle>Default chart range</CardTitle>
        <div className="flex flex-wrap gap-1">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => chooseRange(r)}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-semibold uppercase transition-colors",
                r === defaultRange
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              {r}
            </button>
          ))}
        </div>
      </Card>

      <Card className="space-y-2">
        <CardTitle>Alert delivery</CardTitle>
        <p className="text-sm text-muted-foreground">
          Alerts are delivered in-app (triggered history on the Alerts page). Email delivery is a
          planned enhancement.
        </p>
      </Card>
    </div>
  );
}
