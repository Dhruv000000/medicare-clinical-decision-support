// ==============================================================================
// FILE: frontend/src/services/api.js
// PURPOSE: Centralized Axios HTTP client configuring JWT Bearer injection, auto token refresh, and network interceptors.
// VIVA EXPLANATION: This module manages all frontend-backend HTTP communication. It intercepts outgoing requests to inject JWT access tokens and automatically handles 401 Unauthorized errors by exchanging refresh tokens transparently in a queued promise pipeline.
// ==============================================================================

import axios from "axios";

export const ACCESS_TOKEN_KEY = "medicare_access_token";
export const REFRESH_TOKEN_KEY = "medicare_refresh_token";
export const USER_INFO_KEY = "medicare_user_info";

// --- getAccessToken ---
// What it does: Retrieves persisted JWT access token from localStorage.
// Why it's structured this way: Fast client-side retrieval for request headers without state delays.
// Parameters & Returns: None. Returns string access token or null.
// ------------------------------------------------------------------------------
export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

// --- getRefreshToken ---
// What it does: Retrieves persisted JWT refresh token from localStorage.
// Why it's structured this way: Used to initiate background token rotation when access token expires.
// Parameters & Returns: None. Returns string refresh token or null.
// ------------------------------------------------------------------------------
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

// --- setTokens ---
// What it does: Commits access and refresh tokens to localStorage and updates axios default headers.
// Why it's structured this way: Updates both tokens synchronously to maintain authentication state and avoids stale cached tokens.
// Parameters & Returns: access (string), refresh (string). Returns void.
// ------------------------------------------------------------------------------
export function setTokens(access, refresh) {
  if (access) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    api.defaults.headers.common.Authorization = `Bearer ${access}`;
  }
  if (refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }
}

// --- clearTokens ---
// What it does: Removes all stored JWT credentials, user profile cache, and authorization headers.
// Why it's structured this way: Ensures clean session termination upon user logout or token revocation without stale role pollution.
// Parameters & Returns: None. Returns void.
// ------------------------------------------------------------------------------
export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_INFO_KEY);
  localStorage.removeItem("medicare-demo-user");
  localStorage.removeItem("medicare-doctor-session");
  localStorage.removeItem("manus-runtime-user-info");
  delete api.defaults.headers.common.Authorization;
}

const baseURL =
  import.meta.env.VITE_API_URL ||
  "https://medicare-clinical-decision-support.onrender.com/api/v1/";

const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 90000,
});

// ==============================================================================
// --- REQUEST INTERCEPTOR: ATTACH JWT AUTHORIZATION HEADER ---
// ==============================================================================
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      delete config.headers.Authorization;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ==============================================================================
// --- RESPONSE INTERCEPTOR: AUTO-REFRESH EXPIRED JWT TOKENS ---
// ==============================================================================
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Avoid infinite retry loops on auth endpoints
    const isAuthUrl =
      originalRequest?.url?.includes("/auth/login/") ||
      originalRequest?.url?.includes("/auth/token/refresh/") ||
      originalRequest?.url?.includes("/auth/register/");

    if (error.response?.status === 401 && !originalRequest?._retry && !isAuthUrl) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        isRefreshing = false;
        clearTokens();
        window.dispatchEvent(new CustomEvent("medicare-auth-expired"));
        return Promise.reject(error);
      }

      try {
        // Direct axios call without interceptor to prevent recursion
        const refreshUrl = baseURL.endsWith("/")
          ? `${baseURL}auth/token/refresh/`
          : `${baseURL}/auth/token/refresh/`;

        const { data } = await axios.post(refreshUrl, { refresh: refreshToken });
        const newAccessToken = data.access;
        const newRefreshToken = data.refresh;

        setTokens(newAccessToken, newRefreshToken);
        api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearTokens();
        window.dispatchEvent(new CustomEvent("medicare-auth-expired"));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
