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
