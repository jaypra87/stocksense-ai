import { Info } from "lucide-react";

import { env } from "@/lib/env";

// Shown only on the public demo deployment (NEXT_PUBLIC_DEMO_MODE=true).
export function DemoBanner() {
  if (env.NEXT_PUBLIC_DEMO_MODE !== "true") return null;
  return (
    <div className="flex items-start gap-2 rounded-lg border border-accent/30 bg-accent/10 px-4 py-2 text-xs text-muted-foreground">
      <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" aria-hidden />
      <p>
        <span className="font-semibold text-foreground">Live demo.</span> The free backend may take
        ~30s to wake on the first request. Market data is fetched from a public source and may be
        delayed or occasionally unavailable.
      </p>
    </div>
  );
}
