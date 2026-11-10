import { API_BASE } from "@/lib/env";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body: unknown,
    /** The server wants a Turnstile (bot check) token before it will proceed. */
    public challenge: boolean = false,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

// Endpoints where a 401 is a normal outcome (bad credentials / no session yet),
// not a lost session.
const AUTH_PATHS = ["/auth/login", "/auth/signup", "/auth/guest", "/auth/me"];

/** Fired on `window` when a request finds the session gone; AuthProvider
 * listens and starts a fresh one. */
export const SESSION_LOST_EVENT = "stocksense:session-lost";

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options;

  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    // The session rides in an httpOnly cookie on this origin. Nothing to attach.
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...((headers as Record<string, string>) ?? {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 204) return undefined as T;

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
    if (
      response.status === 401 &&
      typeof window !== "undefined" &&
      !AUTH_PATHS.some((p) => path.startsWith(p))
    ) {
      window.dispatchEvent(new Event(SESSION_LOST_EVENT));
    }
    const { message, challenge } = describeError(parsed, response.statusText);
    throw new ApiError(message, response.status, parsed, challenge);
  }

  return parsed as T;
}

function describeError(parsed: unknown, fallback: string): { message: string; challenge: boolean } {
  if (typeof parsed === "object" && parsed !== null && "detail" in parsed) {
    const detail = (parsed as { detail: unknown }).detail;
    if (typeof detail === "string") return { message: detail, challenge: false };
    if (typeof detail === "object" && detail !== null) {
      const d = detail as { message?: unknown; challenge?: unknown };
      return {
        message: typeof d.message === "string" ? d.message : fallback || "Request failed",
        challenge: d.challenge === "turnstile",
      };
    }
  }
  return { message: fallback || "Request failed", challenge: false };
}

/**
 * Fire-and-forget ping that wakes a sleeping backend.
 *
 * The free hosting tier spins the API container down after idle, and the next
 * request pays the full cold start. The session bootstrap already does this on
 * every page load; this is for public pages that make no API call of their
 * own, so the dashboard is warm by the time the visitor clicks through.
 */
let warmed = false;

export function warmBackend(): void {
  if (warmed || typeof window === "undefined") return;
  warmed = true;
  void fetch(`${API_BASE}/health`, { cache: "no-store" }).catch(() => {
    // A failed pre-warm changes nothing; the real request reports real errors.
  });
}
