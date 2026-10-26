// ==============================================================================
// FILE: frontend/src/context/AuthContext.jsx
// PURPOSE: React context provider managing global authentication state, JWT tokens, and user credentials.
// VIVA EXPLANATION: Implements the central authentication authority for the frontend. Coordinates JWT access and refresh token lifecycle, executes user login/registration/logout, synchronizes cross-tab sessions via localStorage storage events, and provides user role-based access state across components.
// ==============================================================================

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import api, {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "../services/api";

const AuthContext = createContext(null);


// --- AuthProvider ---
// What it does: React context provider wrapping children with authentication state (user, role, isAuthenticated, tokens).
// Why it's structured this way: Eliminates prop-drilling by providing reactive authentication state to all components in the React tree.
// Parameters & Returns: { children } -> AuthContext.Provider JSX element.
// ------------------------------------------------------------------------------
export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("medicare_user_info");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // --- fetchCurrentUser ---
  // What it does: Resolves the logged-in user profile from /auth/me/ using the stored JWT access token.
  // Why it's structured this way: Verifies token validity on app initialization and rehydrates session state.
  // Parameters & Returns: None -> Resolved user object or null if session is expired.
  // ------------------------------------------------------------------------------
  const fetchCurrentUser = useCallback(async () => {
    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();

    if (!accessToken && !refreshToken) {
      setUser(null);
      localStorage.removeItem("medicare_user_info");
      setLoading(false);
      return null;
    }

    try {
      const { data } = await api.get("/auth/me/");
      // Add computed display name
      const full_name = [data.first_name, data.last_name].filter(Boolean).join(" ") || data.email;
      const enrichedUser = { ...data, full_name };

      setUser(enrichedUser);
      localStorage.setItem("medicare_user_info", JSON.stringify(enrichedUser));
      return enrichedUser;
    } catch (err) {
      console.warn("Auth initialization: session invalid or expired", err);
      clearTokens();
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();

    const handleAuthExpired = () => {
      setUser(null);
      localStorage.removeItem("medicare_user_info");
      setLoading(false);
    };

    const handleStorageChange = (e) => {
      if (e.key === "medicare_access_token") {
        fetchCurrentUser();
      }
    };

    window.addEventListener("medicare-auth-expired", handleAuthExpired);
    window.addEventListener("storage", handleStorageChange);

    return () => {
      window.removeEventListener("medicare-auth-expired", handleAuthExpired);
      window.removeEventListener("storage", handleStorageChange);
    };
  }, [fetchCurrentUser]);

  // --- login ---
  // What it does: Submits credentials and selected role to /auth/login/, stores received JWT tokens, and initializes user state.
  // Why it's structured this way: Enforces role verification, prevents stale tokens from corrupting active session, and enriches profile.
  // Parameters & Returns: { email, password, role } -> { success: boolean, user?: object, error?: string }.
  // ------------------------------------------------------------------------------
  const login = useCallback(async ({ email, password, role }) => {
    setLoading(true);
    setError(null);

    try {
      // Clear previous tokens before establishing fresh authenticated session
      clearTokens();

      const payload = {
        email: email.trim().toLowerCase(),
        password,
      };
      if (role) {
        payload.role = role.trim().toLowerCase();
      }

      const { data } = await api.post("/auth/login/", payload);

      const { access, refresh, user: loginUser } = data;
      setTokens(access, refresh);

      // Verify or enrich with full /auth/me/ profile using the newly acquired access token
      let enrichedUser = loginUser || {};
      try {
        const meRes = await api.get("/auth/me/", {
          headers: { Authorization: `Bearer ${access}` },
        });
        if (meRes.data && meRes.data.role) {
          enrichedUser = meRes.data;
        }
      } catch (meErr) {
        console.warn("Could not fetch /auth/me/, using login payload", meErr);
      }

      if (!enrichedUser.role && loginUser?.role) {
        enrichedUser.role = loginUser.role;
      }

      const full_name =
        [enrichedUser.first_name, enrichedUser.last_name].filter(Boolean).join(" ") ||
        enrichedUser.email;
      const finalUser = { ...enrichedUser, full_name };

      setUser(finalUser);
      localStorage.setItem("medicare_user_info", JSON.stringify(finalUser));
      window.dispatchEvent(new Event("medicare-auth-change"));

      return { success: true, user: finalUser };
    } catch (err) {
      let errorMsg = "Invalid email or password. Please try again.";
      const errorData = err.response?.data;
      if (errorData) {
        if (typeof errorData === "string") {
          errorMsg = errorData;
        } else if (errorData.error && typeof errorData.error === "object") {
          const { message, details } = errorData.error;
          if (details && typeof details === "object" && Object.keys(details).length > 0) {
            const fieldMsgs = Object.entries(details).map(([k, v]) => {
              const valText = Array.isArray(v) ? v.join(" ") : String(v);
              return `${k !== "non_field_errors" && k !== "detail" ? `${k}: ` : ""}${valText}`;
            });
            errorMsg = fieldMsgs.join(" | ");
          } else if (message) {
            errorMsg = message;
          }
        } else if (errorData.detail) {
          errorMsg = errorData.detail;
        } else if (typeof errorData === "object") {
          const fieldMsgs = Object.entries(errorData).map(([k, v]) => {
            const valText = Array.isArray(v) ? v.join(" ") : String(v);
            return `${k !== "non_field_errors" && k !== "detail" ? `${k}: ` : ""}${valText}`;
          });
          if (fieldMsgs.length > 0) {
            errorMsg = fieldMsgs.join(" | ");
          }
        }
      } else if (err.message) {
        errorMsg = err.message;
      }

      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  }, []);

  // --- register ---
  // What it does: Sends new user registration payload to /auth/register/ with password confirmation validation.
  // Why it's structured this way: Sanitizes names, email, and parses structured DRF field-level error responses.
  // Parameters & Returns: User attributes -> { success: boolean, data?: object, fieldErrors?: object }.
  // ------------------------------------------------------------------------------
  const register = useCallback(
    async ({
      email,
      password,
      confirm_password,
      confirmPassword,
      first_name,
      firstName,
      last_name,
      lastName,
      role = "patient",
      username,
    }) => {
      setLoading(true);
      setError(null);

      try {
        const cleanEmail = (email || "").trim().toLowerCase();
        const fName = (first_name || firstName || "").trim();
        const lName = (last_name || lastName || "").trim();
        const cleanRole = (role || "patient").toLowerCase();
        const cleanUsername = (
          username ||
          (cleanEmail ? cleanEmail.split("@")[0] : "")
        ).trim();
        const cleanPassword = password || "";
        const cleanConfirm = confirm_password || confirmPassword || cleanPassword;

        const payload = {
          email: cleanEmail,
          username: cleanUsername,
          first_name: fName,
          last_name: lName,
          role: cleanRole,
          password: cleanPassword,
          confirm_password: cleanConfirm,
        };

        const response = await api.post("/auth/register/", payload);

        return {
          success: true,
          data: response.data,
          status: response.status,
        };
      } catch (err) {
        let errorMsg = "Registration failed. Please check your information and try again.";
        let fieldErrors = {};

        const errorData = err.response?.data;
        if (errorData) {
          if (typeof errorData === "string") {
            errorMsg = errorData;
          } else if (errorData.error && typeof errorData.error === "object") {
            const { message, details } = errorData.error;
            if (details && typeof details === "object" && Object.keys(details).length > 0) {
              fieldErrors = details;
              const fieldMsgs = Object.entries(details).map(([k, v]) => {
                const valText = Array.isArray(v) ? v.join(" ") : String(v);
                return `${k !== "non_field_errors" && k !== "detail" ? `${k}: ` : ""}${valText}`;
              });
              errorMsg = fieldMsgs.join(" | ");
            } else if (message) {
              errorMsg = message;
            }
          } else if (errorData.detail) {
            errorMsg = errorData.detail;
          } else if (typeof errorData === "object") {
            fieldErrors = errorData;
            const fieldMsgs = Object.entries(errorData).map(([k, v]) => {
              const valText = Array.isArray(v) ? v.join(" ") : String(v);
              return `${k !== "non_field_errors" && k !== "detail" ? `${k}: ` : ""}${valText}`;
            });
            if (fieldMsgs.length > 0) {
              errorMsg = fieldMsgs.join(" | ");
            }
          }
        } else if (err.message) {
          errorMsg = err.message;
        }

        setError(errorMsg);
        return {
          success: false,
          error: errorMsg,
          fieldErrors,
          status: err.response?.status,
        };
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // --- logout ---
  // What it does: Invalidates refresh token on the server (/auth/logout/) and deletes local credentials.
  // Why it's structured this way: Flushes client-side state and broadcasts auth change event for instantaneous UI logout.
  // Parameters & Returns: None -> Clears session state.
  // ------------------------------------------------------------------------------
  const logout = useCallback(async () => {
    setLoading(true);
    try {
      const refreshToken = getRefreshToken();
      if (refreshToken) {
        try {
          await api.post("/auth/logout/", { refresh: refreshToken });
        } catch (err) {
          console.warn("Server logout notification failed:", err);
        }
      }
    } finally {
      clearTokens();
      setUser(null);
      setError(null);
      setLoading(false);
      window.dispatchEvent(new Event("medicare-auth-change"));
    }
  }, []);

  const value = {
    user,
    loading,
    error,
    isAuthenticated: Boolean(user),
    role: user?.role || null,
    login,
    register,
    logout,
    refreshUser: fetchCurrentUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


// --- useAuthContext ---
// What it does: Custom React hook consuming the AuthContext value.
// Why it's structured this way: Throws an explicit error if called outside AuthProvider to protect against improper context usage.
// Parameters & Returns: None -> AuthContext state and methods (user, login, logout, role, etc.).
// ------------------------------------------------------------------------------
export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
}

