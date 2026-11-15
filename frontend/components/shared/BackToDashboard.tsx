import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

// Small link placed above a page title on pages a visitor reaches from the
// dashboard (a stock, settings, the transparency report). The header logo
// goes to the landing page, so this is the explicit route back.
export function BackToDashboard({ className }: { className?: string }) {
  return (
    <Link
      href="/dashboard"
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md text-sm font-medium text-muted-foreground transition-colors hover:text-foreground",
        className,
      )}
    >
      <ArrowLeft className="h-4 w-4" aria-hidden />
      Back to dashboard
    </Link>
  );
}
