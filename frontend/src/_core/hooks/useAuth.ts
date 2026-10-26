// ==============================================================================
// FILE: frontend/src/_core/hooks/useAuth.ts
// PURPOSE: Custom React hook exposing canonical authentication state and session handlers.
// VIVA EXPLANATION: This custom hook encapsulates consumer access to AuthContext. It abstracts user identity, role permissions, and session actions (login, register, logout, token refresh) for easy consumption across components.
// ==============================================================================

import { useCallback, useEffect } from "react";
import { useAuthContext } from "../../context/AuthContext";

// --- useAuth ---
// What it does: Returns user credentials, authentication flags, and token manipulation procedures.
// Why it's structured this way: Encapsulates context extraction into a reusable hook with fallback role resolutions.
// Parameters & Returns: options (object, optional). Returns session context interface object.
// ------------------------------------------------------------------------------
export function useAuth(options: any = {}) {
  const { redirectOnUnauthenticated = false, redirectPath } = options;

  const authContext = useAuthContext();
  const { user, loading, error, isAuthenticated, role, login, register, logout, refreshUser } = authContext;

  const refresh = useCallback(async () => {
    const refreshed = await refreshUser();
    return { data: refreshed };
  }, [refreshUser]);

  return {
    user,
    role: user?.role || role || null,
    loading,
    error,
    isAuthenticated: Boolean(user),
    refresh,
    logout,
    login,
    register,
  };
}

