// JWT lives in localStorage. Simple and works for this SPA-style app; the
// trade-off vs httpOnly cookies is XSS exposure (acceptable for an educational
// project, noted in the README). Only touch localStorage in the browser.

const TOKEN_KEY = "stocksense_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}
