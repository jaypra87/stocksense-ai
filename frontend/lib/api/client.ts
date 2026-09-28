import { clearToken, getToken } from "@/lib/auth";
import { env } from "@/lib/env";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

// Endpoints where a 401 is a normal outcome (bad credentials), not an expired session.
const AUTH_PATHS = ["/auth/login", "/auth/signup"];

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options;

  // Attach the JWT on client-side calls (no-op during SSR).
  const token = getToken();
  const mergedHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((headers as Record<string, string>) ?? {}),
  };

  const response = await fetch(`${env.NEXT_PUBLIC_API_URL}${path}`, {
    ...rest,
    headers: mergedHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // Guarded parse: proxies/gateways can return non-JSON error bodies (HTML 502
  // pages etc.) — those must still surface as ApiError, not a raw SyntaxError.
  const text = await response.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!response.ok) {
    // Expired/invalid session: clear the stale token and send the user to
    // login instead of leaving every panel in a silent error state.
    if (
      response.status === 401 &&
      token &&
      typeof window !== "undefined" &&
      !AUTH_PATHS.some((p) => path.startsWith(p))
    ) {
      clearToken();
      window.location.assign("/login");
    }

    const detail =
      typeof parsed === "object" && parsed !== null && "detail" in parsed
        ? String((parsed as { detail: unknown }).detail)
        : response.statusText || "Request failed";
    throw new ApiError(detail, response.status, parsed);
  }

  return parsed as T;
}

/**
 * Fire-and-forget ping that wakes a sleeping backend.
 *
 * The free hosting tier spins the API container down after idle, and the next
 * request pays the full cold start. Calling this when the login screen mounts
 * moves that wait to *while the user is typing their credentials* instead of
 * after they hit "Sign in", which is the whole of the perceived slowness.
 *
 * Deliberately targets /health: it touches no database or cache, so it can
 * answer as soon as the process is listening. Errors are ignored — this is an
 * optimization, never a precondition.
 */
let warmed = false;

export function warmBackend(): void {
  if (warmed || typeof window === "undefined") return;
  warmed = true;
  void fetch(`${env.NEXT_PUBLIC_API_URL}/health`, { cache: "no-store" }).catch(() => {
    // A failed pre-warm changes nothing; the real request reports real errors.
  });
}
