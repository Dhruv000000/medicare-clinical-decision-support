// ==============================================================================
// FILE: frontend/src/pages/public/patient/LogoutModal.jsx
// PURPOSE: Accessible modal confirmation dialog for terminating authenticated user sessions.
// VIVA EXPLANATION: Implements the user logout confirmation modal. Traps keyboard escape keys, supports backdrop clicks, and prompts the patient before terminating their session and flushing JWT authentication tokens.
// ==============================================================================

import React, { useEffect } from "react";
import { LogOut, X, ShieldAlert } from "lucide-react";


// --- LogoutModal ---
// What it does: Renders an accessible modal dialog confirming session sign-out intent.
// Why it's structured this way: Prevents accidental logouts while ensuring ARIA dialog compliance and keyboard accessibility.
// Parameters & Returns: { open, darkMode, onClose, onConfirm } -> Modal dialog JSX element or null if closed.
// ------------------------------------------------------------------------------
export default function LogoutModal({
  open,
  darkMode,
  onClose,
  onConfirm,
}) {

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        className={`w-full max-w-sm overflow-hidden rounded-2xl border shadow-2xl ${
          darkMode
            ? "border-slate-700 bg-[#15211f]"
            : "border-slate-200 bg-white"
        }`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="logout-title"
      >
        <div className="flex items-start justify-between p-5">
          <div className="flex items-start gap-3">
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
              }`}
            >
              <LogOut size={18} className="text-emerald-500" />
            </div>

            <div>
              <h2
                id="logout-title"
                className={`text-[15px] font-bold ${
                  darkMode ? "text-white" : "text-emerald-950"
                }`}
              >
                Log out of MediCare?
              </h2>

              <p
                className={`mt-1.5 text-[9px] leading-4 ${
                  darkMode ? "text-slate-500" : "text-slate-500"
                }`}
              >
                You will be returned to the login screen. Any unsaved changes
                on the current page may be lost.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className={`rounded-lg p-1.5 transition ${
              darkMode
                ? "text-slate-500 hover:bg-slate-800 hover:text-slate-300"
                : "text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            }`}
            aria-label="Close logout dialog"
          >
            <X size={17} />
          </button>
        </div>

        <div
          className={`mx-5 flex items-start gap-2 rounded-xl border p-3 ${
            darkMode
              ? "border-slate-800 bg-[#101918]"
              : "border-slate-100 bg-slate-50"
          }`}
        >
          <ShieldAlert
            size={13}
            className="mt-0.5 shrink-0 text-emerald-500"
          />

          <p
            className={`text-[8px] leading-4 ${
              darkMode ? "text-slate-500" : "text-slate-500"
            }`}
          >
            Your local theme and preference settings will remain saved.
          </p>
        </div>

        <div
          className={`mt-5 flex gap-2 border-t p-4 ${
            darkMode ? "border-slate-800" : "border-slate-100"
          }`}
        >
          <button
            type="button"
            onClick={onClose}
            className={`flex-1 rounded-lg border px-4 py-2.5 text-[10px] font-medium transition ${
              darkMode
                ? "border-slate-700 text-slate-300 hover:bg-slate-800"
                : "border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={onConfirm}
            className="flex-1 rounded-lg bg-emerald-500 px-4 py-2.5 text-[10px] font-semibold text-white transition hover:bg-emerald-600"
          >
            Log Out
          </button>
        </div>
      </div>
    </div>
  );
}
