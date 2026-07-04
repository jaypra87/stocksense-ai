"use client";

import { AlertTriangle } from "lucide-react";

// Route-level error boundary: shows a friendly recovery UI instead of a blank
// screen and never surfaces internal error details to the user.
export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-bearish/10">
        <AlertTriangle className="h-6 w-6 text-bearish" aria-hidden />
      </div>
      <h1 className="text-3xl font-bold tracking-tight">Something went wrong</h1>
      <p className="max-w-md text-muted-foreground">
        An unexpected error occurred. It wasn&apos;t your fault — try again.
      </p>
      <button
        onClick={reset}
        className="mt-2 rounded-lg bg-accent px-5 py-2.5 font-semibold text-accent-foreground shadow-sm transition-colors hover:bg-accent-hover"
      >
        Try again
      </button>
    </main>
  );
}
