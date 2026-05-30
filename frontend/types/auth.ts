export interface User {
  id: string;
  email: string;
  preferences: Record<string, unknown>;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}
