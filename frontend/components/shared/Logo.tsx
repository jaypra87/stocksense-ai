import { LineChart } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

export function Logo({ href = "/", className }: { href?: string; className?: string }) {
  return (
    <Link
      href={href}
      className={cn("flex shrink-0 items-center gap-2 font-bold tracking-tight", className)}
    >
      <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/15">
        <LineChart className="h-4 w-4 text-accent" aria-hidden />
      </span>
      <span>
        StockSense <span className="text-accent">AI</span>
      </span>
    </Link>
  );
}
