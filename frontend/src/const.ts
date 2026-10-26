// ==============================================================================
// FILE: frontend/src/const.ts
// PURPOSE: Frontend client environment constants and third-party OAuth redirect initializer.
// VIVA EXPLANATION: Configures OAuth authentication handshake parameters, generates secure nonces, and redirects users to external identity providers.
// ==============================================================================

import { OAUTH_STATE_COOKIE, encodeOAuthState } from "@shared/const";

export { COOKIE_NAME, ONE_YEAR_MS } from "@shared/const";

// --- startLogin ---
// What it does: Generates state nonce, stores security cookies, and initiates OAuth authentication redirect.
// Why it's structured this way: Uses crypto.randomUUID and secure cookies to prevent CSRF during external login flows.
// Parameters & Returns: None. Dispatches window redirect.
// ------------------------------------------------------------------------------
export const startLogin = () => {
  const oauthPortalUrl = import.meta.env.VITE_OAUTH_PORTAL_URL;
  const appId = import.meta.env.VITE_APP_ID;
  const redirectUri = `${window.location.origin}/api/oauth/callback`;

  const nonce = crypto.randomUUID();
  document.cookie = `${OAUTH_STATE_COOKIE}=${nonce}; Path=/; Max-Age=600; SameSite=None; Secure`;
  const state = encodeOAuthState({ redirectUri, nonce });

  const url = new URL(`${oauthPortalUrl}/app-auth`);
  url.searchParams.set("appId", appId);
  url.searchParams.set("redirectUri", redirectUri);
  url.searchParams.set("state", state);
  url.searchParams.set("type", "signIn");

  window.location.href = url.toString();
};
