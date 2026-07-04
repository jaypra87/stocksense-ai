import Link from "next/link";

import { Logo } from "@/components/shared/Logo";

const LINKS = [
  { href: "/transparency", label: "How the models work" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/compare", label: "Compare" },
];

export function Footer() {
  return (
    <footer className="mt-16 border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-10 sm:px-6 md:flex-row md:items-start md:justify-between">
        <div className="max-w-sm space-y-3">
          <Logo />
          <p className="text-sm text-muted-foreground">
            Interpretable, uncertainty-aware stock analytics. Educational project — forecasts are
            probabilistic and frequently wrong. Not financial advice.
          </p>
        </div>
        <nav aria-label="Footer">
          <ul className="space-y-2 text-sm">
            {LINKS.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="border-t border-border py-4 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} StockSense AI · Educational use only
      </div>
    </footer>
  );
}
