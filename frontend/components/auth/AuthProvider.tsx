"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

import {
  guestApi,
  loginApi,
  logoutAllApi,
  logoutApi,
  meApi,
  signupApi,
} from "@/lib/api/auth";
import { ApiError, SESSION_LOST_EVENT } from "@/lib/api/client";
import type { User } from "@/types/auth";

/**
 * Session state for the whole app.
 *
 * There is no login wall. On first load this asks the API who the visitor is;
 * with no session it silently starts a guest one, so the dashboard is usable
 * immediately and anything saved belongs to that guest. Saving an account
 * (signup) upgrades the guest in place; signing in merges the guest into the
 * account. The credential is an httpOnly cookie the browser handles itself —
 * no token is ever stored in page-accessible storage.
 */

interface AuthContextValue {
  user: User | null;
  /** True until the first session resolution finishes. */
  loading: boolean;
  /** Set when the API refused to start a session; `challenge` means it will
   * accept one with a Turnstile token (see retry). */
  error: string | null;
  challenge: boolean;
  retry: (turnstileToken?: string | null) => Promise<void>;
  login: (email: string, password: string, turnstileToken?: string | null) => Promise<void>;
  signup: (email: string, password: string, turnstileToken?: string | null) => Promise<void>;
  logout: () => Promise<void>;
  logoutEverywhere: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [challenge, setChallenge] = useState(false);
  const inFlight = useRef<Promise<void> | null>(null);

  const startSession = useCallback(
    async (turnstileToken?: string | null) => {
      // Coalesce: several panels can lose the session at once.
      if (inFlight.current) return inFlight.current;
      inFlight.current = (async () => {
        setError(null);
        setChallenge(false);
        try {
          const res = await guestApi(turnstileToken);
          setUser(res.user);
        } catch (err) {
          setUser(null);
          if (err instanceof ApiError) {
            setChallenge(err.challenge);
            setError(err.message);
          } else {
            setError("Could not reach the server. Please try again.");
          }
        } finally {
          setLoading(false);
          inFlight.current = null;
        }
      })();
      return inFlight.current;
    },
    [],
  );

  // Resolve the session on first load: existing cookie → me; otherwise guest.
  useEffect(() => {
    let cancelled = false;
    meApi()
      .then((me) => {
        if (!cancelled) {
          setUser(me);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) void startSession();
      });
    return () => {
      cancelled = true;
    };
  }, [startSession]);

  // A data request found the session gone (expired, revoked): start a fresh
  // guest one and refetch everything that was on screen.
  useEffect(() => {
    const onLost = () => {
      void startSession().then(() => queryClient.invalidateQueries());
    };
    window.addEventListener(SESSION_LOST_EVENT, onLost);
    return () => window.removeEventListener(SESSION_LOST_EVENT, onLost);
  }, [startSession, queryClient]);

  async function login(email: string, password: string, turnstileToken?: string | null) {
    const res = await loginApi(email, password, turnstileToken);
    setUser(res.user);
    // The guest's data was merged into the account; show the account's view.
    await queryClient.invalidateQueries();
  }

  async function signup(email: string, password: string, turnstileToken?: string | null) {
    const res = await signupApi(email, password, turnstileToken);
    setUser(res.user);
  }

  async function logout() {
    try {
      await logoutApi();
    } finally {
      setUser(null);
      queryClient.clear();
      await startSession();
      router.push("/dashboard");
    }
  }

  async function logoutEverywhere() {
    try {
      await logoutAllApi();
    } finally {
      setUser(null);
      queryClient.clear();
      await startSession();
      router.push("/dashboard");
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        challenge,
        retry: startSession,
        login,
        signup,
        logout,
        logoutEverywhere,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
