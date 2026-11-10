import { apiFetch } from "@/lib/api/client";
import type { SessionInfo, SessionResponse, User } from "@/types/auth";

/** Start (or resume) a guest session. Idempotent for a caller that has one. */
export function guestApi(turnstileToken?: string | null): Promise<SessionResponse> {
  return apiFetch<SessionResponse>("/auth/guest", {
    method: "POST",
    body: turnstileToken ? { turnstile_token: turnstileToken } : {},
  });
}

/** Save the current guest as an account (or create one outright). */
export function signupApi(
  email: string,
  password: string,
  turnstileToken?: string | null,
): Promise<SessionResponse> {
  return apiFetch<SessionResponse>("/auth/signup", {
    method: "POST",
    body: { email, password, turnstile_token: turnstileToken ?? null },
  });
}

export function loginApi(
  email: string,
  password: string,
  turnstileToken?: string | null,
): Promise<SessionResponse> {
  return apiFetch<SessionResponse>("/auth/login", {
    method: "POST",
    body: { email, password, turnstile_token: turnstileToken ?? null },
  });
}

export function logoutApi(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}

export function logoutAllApi(): Promise<void> {
  return apiFetch<void>("/auth/logout-all", { method: "POST" });
}

export function meApi(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export function sessionsApi(): Promise<SessionInfo[]> {
  return apiFetch<SessionInfo[]>("/auth/sessions");
}
