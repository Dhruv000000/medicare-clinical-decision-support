// ==============================================================================
// FILE: frontend/src/pages/public/doctor/logout.jsx
// PURPOSE: Doctor session invalidation and cleanup transition page.
// VIVA EXPLANATION: This component coordinates secure sign-out for medical staff. It invalidates authentication tokens across state and local storage, ensures memory-safe cleanup, and redirects practitioners to the login view.
// ==============================================================================

import React from "react";
import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../ThemeContext";

import { useAuth } from "../../../_core/hooks/useAuth";

// --- Logout ---
// What it does: Executes provider session revocation, clears persisted storage, and redirects to login.
// Why it's structured this way: Uses useEffect with an active unmount flag to prevent race conditions during asynchronous logout.
// Parameters & Returns: None. Returns sign-out transition spinner JSX.
// ------------------------------------------------------------------------------
export default function Logout() {
  const navigate = useNavigate();
  const { isDark } = useTheme();
  const { logout } = useAuth();

  React.useEffect(() => {
    let active = true;
    (async () => {
      try {
        await logout();
      } finally {
        if (active) {
          localStorage.removeItem("medicare-doctor-session");
          navigate("/login", { replace: true });
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [navigate, logout]);

  return (
    <div
      className="flex min-h-dvh items-center justify-center bg-[var(--bg)] px-6 text-[var(--text)]"
      style={{ colorScheme: isDark ? "dark" : "light" }}
    >
      <div className="w-full max-w-sm rounded-2xl border border-[var(--border)] bg-[var(--card)] p-8 text-center shadow-sm">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--accent-soft)] text-[var(--accent)]">
          <LogOut size={21} />
        </div>
        <h1 className="mt-5 text-xl font-bold">Signing out...</h1>
        <p className="mt-2 text-sm text-[var(--muted)]">You will be redirected to the login page.</p>
      </div>
    </div>
  );
}
