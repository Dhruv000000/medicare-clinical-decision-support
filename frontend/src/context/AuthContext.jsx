import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import api, {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
} from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCurrentUser = useCallback(async () => {
    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();

    if (!accessToken && !refreshToken) {
      setUser(null);
      setLoading(false);
      return null;
    }

    try {
      const { data } = await api.get("/auth/me/");
      // Add computed display name
      const full_name = [data.first_name, data.last_name].filter(Boolean).join(" ") || data.email;
      const enrichedUser = { ...data, full_name };

      setUser(enrichedUser);
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

  const login = useCallback(async ({ email, password }) => {
    setLoading(true);
    setError(null);

    try {
      const { data } = await api.post("/auth/login/", {
        email: email.trim().toLowerCase(),
        password,
      });

      const { access, refresh, user: loginUser } = data;
      setTokens(access, refresh);

      // Verify or enrich with full /auth/me/ profile
      let enrichedUser = loginUser;
      try {
        const meRes = await api.get("/auth/me/");
        enrichedUser = meRes.data;
      } catch {
        // Fallback to loginUser payload if /auth/me/ is delayed
      }

      const full_name =
        [enrichedUser.first_name, enrichedUser.last_name].filter(Boolean).join(" ") ||
        enrichedUser.email;
      const finalUser = { ...enrichedUser, full_name };

      setUser(finalUser);
      window.dispatchEvent(new Event("medicare-auth-change"));

      return { success: true, user: finalUser };
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail ||
        err.response?.data?.error?.message ||
        (typeof err.response?.data === "object" ? Object.values(err.response?.data).flat().join(" ") : null) ||
        "Invalid email or password. Please try again.";

      setError(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  }, []);

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

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
}
