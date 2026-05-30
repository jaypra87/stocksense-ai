import { z } from "zod";

const clientEnvSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url(),
  // "true" on the public demo deployment (shows a synthetic-data banner).
  NEXT_PUBLIC_DEMO_MODE: z.string().optional(),
});

export const env = clientEnvSchema.parse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_DEMO_MODE: process.env.NEXT_PUBLIC_DEMO_MODE,
});
