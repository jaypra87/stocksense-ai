export interface User {
  id: string;
  /** null for guests */
  email: string | null;
  is_guest: boolean;
  preferences: Record<string, unknown>;
}

/** Browsers receive the session in an httpOnly cookie; `access_token` is for
 * API clients and is ignored by the app. */
export interface SessionResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SessionInfo {
  id: string;
  current: boolean;
  created_at: string | null;
  last_seen_at: string | null;
  user_agent: string | null;
}
