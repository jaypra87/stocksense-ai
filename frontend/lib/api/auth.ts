import { apiFetch } from "@/lib/api/client";
import type { TokenResponse, User } from "@/types/auth";

export function signupApi(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/signup", { method: "POST", body: { email, password } });
}

export function loginApi(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", { method: "POST", body: { email, password } });
}

export function meApi(): Promise<User> {
  return apiFetch<User>("/auth/me");
}
