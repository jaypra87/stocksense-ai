import { AlertTriangle } from "lucide-react";
import Link from "next/link";

export function DisclaimerBanner() {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-warning/30 bg-warning/5 px-4 py-3 text-sm text-muted-foreground">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden />
      <p>
        <span className="font-semibold text-foreground">Educational project.</span> StockSense AI
        provides probabilistic analytics for learning purposes only. Forecasts may be wrong. This
        is not financial advice.{" "}
        <Link
          href="/transparency"
          className="font-medium text-accent underline-offset-2 hover:underline"
        >
          How it works →
        </Link>
      </p>
    </div>
  );
}
