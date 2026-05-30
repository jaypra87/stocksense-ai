import { clsx, type ClassValue } from "clsx";

// Tiny helper to compose conditional Tailwind class strings.
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
