/**
 * Token storage.
 *
 * Tokens are kept in localStorage for this build pass, which is the
 * simplest thing that works for local development against the FastAPI
 * backend. The trade-off: localStorage is readable by any script on the
 * page, so it's more exposed to XSS than an httpOnly cookie would be.
 * A production hardening pass would move refresh-token issuance behind a
 * Next.js route handler that sets an httpOnly cookie instead — noted here
 * so it isn't forgotten, not implemented in this pass.
 */

const ACCESS_KEY = "researchos_access_token";
const REFRESH_KEY = "researchos_refresh_token";

export interface TokenPair {
  access_token: string;
  refresh_token: string;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_KEY);
}

export function setTokens(tokens: TokenPair): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}
