import { z } from "zod";

// The API is reached through this site's own origin (see app/api/v1/[...path]):
// the backend address lives server-side in BACKEND_URL and never ships to the
// browser.
export const API_BASE = "/api/v1";

const clientEnvSchema = z.object({
  // "true" on the public demo deployment (shows the live-demo banner).
  NEXT_PUBLIC_DEMO_MODE: z.string().optional(),
  // Cloudflare Turnstile site key (public). Unset = no challenge widget.
  NEXT_PUBLIC_TURNSTILE_SITE_KEY: z.string().optional(),
});

export const env = clientEnvSchema.parse({
  NEXT_PUBLIC_DEMO_MODE: process.env.NEXT_PUBLIC_DEMO_MODE,
  NEXT_PUBLIC_TURNSTILE_SITE_KEY: process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY,
});
