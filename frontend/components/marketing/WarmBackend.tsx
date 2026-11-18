"use client";

import { useEffect } from "react";

import { warmBackend } from "@/lib/api/client";

// Public pages make no API call of their own, so the backend may be asleep
// when the visitor clicks through. One early ping starts it waking while
// they read, which is the whole difference between a dashboard that opens
// and one that shows the waiting screen.
export function WarmBackend() {
  useEffect(() => warmBackend(), []);
  return null;
}
