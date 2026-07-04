import { z } from "zod";

const clientEnvSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url(),
  // "true" on the public demo deployment (shows a synthetic-data banner).
  NEXT_PUBLIC_DEMO_MODE: z.string().optional(),
});

const result = clientEnvSchema.safeParse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_DEMO_MODE: process.env.NEXT_PUBLIC_DEMO_MODE,
});

if (!result.success) {
  throw new Error(
    "Invalid frontend environment: NEXT_PUBLIC_API_URL must be a valid URL " +
      "(set it in frontend/.env.local — see .env.example).",
  );
}

export const env = result.data;
