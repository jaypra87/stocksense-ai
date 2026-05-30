"use client";

import { Bell, GitCompare, LineChart, LogOut, Settings, Star } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/auth/AuthProvider";
import { SearchBar } from "@/components/shared/SearchBar";
import { ThemeToggle } from "@/components/shared/ThemeToggle";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/watchlist", label: "Watchlist", Icon: Star },
  { href: "/compare", label: "Compare", Icon: GitCompare },
  { href: "/alerts", label: "Alerts", Icon: Bell },
];

export function Header() {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
        <Link href="/dashboard" className="flex shrink-0 items-center gap-2 font-bold">
          <LineChart className="h-5 w-5 text-accent" />
          <span className="hidden sm:inline">StockSense AI</span>
        </Link>

        <div className="flex flex-1 justify-center">
          <SearchBar />
        </div>

        <nav className="hidden items-center gap-1 md:flex">
          {NAV.map(({ href, label, Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm transition-colors",
                pathname === href
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" /> {label}
            </Link>
          ))}
        </nav>

        <Link
          href="/settings"
          title="Settings"
          className="flex h-9 w-9 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <Settings className="h-4 w-4" />
        </Link>

        <ThemeToggle />

        {user && (
          <button
            onClick={logout}
            title={`Sign out (${user.email})`}
            className="flex h-9 w-9 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <LogOut className="h-4 w-4" />
          </button>
        )}
      </div>
    </header>
  );
}
