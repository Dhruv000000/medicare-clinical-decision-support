// ==============================================================================
// FILE: frontend/src/shared/const.ts
// PURPOSE: Global shared constants and OAuth state serialization utilities.
// VIVA EXPLANATION: Defines platform session cookie tokens and helper utilities to encode/decode state payloads during third-party OAuth handshakes.
// ==============================================================================

export const COOKIE_NAME = "medicare-session";
export const ONE_YEAR_MS = 365 * 24 * 60 * 60 * 1000;
export const OAUTH_STATE_COOKIE = "medicare-oauth-state";

// --- encodeOAuthState ---
// What it does: Encodes state dictionary into a Base64 string for URL safety.
// Why it's structured this way: Uses native JSON serialization and btoa to preserve parameter integrity across authentication redirects.
// Parameters & Returns: value (Record<string, string>). Returns string.
// ------------------------------------------------------------------------------
export function encodeOAuthState(value: Record<string, string>) {
  return btoa(JSON.stringify(value));
}