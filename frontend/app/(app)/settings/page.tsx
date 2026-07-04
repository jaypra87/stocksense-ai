"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { RANGES, type Range } from "@/types/stock";

const RANGE_KEY = "stocksense_default_range";
const THEMES = ["light", "dark", "system"] as const;

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const [defaultRange, setDefaultRange] = useState<Range>("1y");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = window.localStorage.getItem(RANGE_KEY) as Range | null;
    if (saved && (RANGES as readonly string[]).includes(saved)) setDefaultRange(saved);
  }, []);

  function chooseRange(r: Range) {
    setDefaultRange(r);
    window.localStorage.setItem(RANGE_KEY, r);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Preferences are stored on this device.</p>
      </div>

      <Card className="space-y-3">
        <CardTitle>Account</CardTitle>
        <p className="text-sm">
          Signed in as <span className="font-semibold">{user?.email}</span>
        </p>
        <Button variant="destructive" size="sm" onClick={logout}>
          Sign out
        </Button>
      </Card>

      <Card className="space-y-3">
        <CardTitle>Appearance</CardTitle>
        {mounted && (
          <SegmentedControl
            options={THEMES}
            value={(theme as (typeof THEMES)[number]) ?? "system"}
            onChange={setTheme}
            label="Color theme"
          />
        )}
      </Card>

      <Card className="space-y-3">
        <CardTitle>Default chart range</CardTitle>
        <SegmentedControl
          options={RANGES}
          value={defaultRange}
          onChange={chooseRange}
          label="Default chart range"
        />
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
