// ==============================================================================
// FILE: frontend/src/pages/public/admin-login.jsx
// PURPOSE: Dedicated administrative authentication portal and credential verification screen.
// VIVA EXPLANATION: Implements the restricted administrator login console. Validates JWT login credentials and enforces role verification checking that user.role === 'admin' before navigating to /admin/dashboard.
// ==============================================================================

import React, { useState } from "react";
import { ShieldCheck, Lock, HeartPulse, ArrowLeft, ArrowUpRight, Mail } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../_core/hooks/useAuth";


// --- AdminLogin ---
// What it does: Renders administrative login form, invokes login() hook, and confirms role is 'admin'.
// Why it's structured this way: Separates high-privilege administrator entrance from standard patient/doctor portals.
// Parameters & Returns: Props (none) -> Admin login JSX page.
// ------------------------------------------------------------------------------
export default function AdminLogin() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login({ email: email.trim(), password });
      if (res.success) {
        if (res.user?.role === "admin") {
          navigate("/admin/dashboard");
        } else {
          setError("Access restricted. This account does not possess administrator credentials.");
        }
      } else {
        setError(res.error || "Authentication failed. Invalid email or password.");
      }
    } catch (err) {
      setError("Unable to reach the authentication server. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f7faf9] px-5 py-8 text-[#123d32] dark:bg-[#0b1210] dark:text-white">
      <div className="mx-auto max-w-[560px]">
        <button
          type="button"
          onClick={() => navigate("/login")}
          className="mb-8 flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-emerald-600 transition"
        >
          <ArrowLeft size={16} /> Back to standard sign in
        </button>
        <div className="rounded-[32px] border border-slate-200 bg-white p-8 shadow-[0_30px_80px_rgba(18,61,50,0.10)] dark:border-white/10 dark:bg-[#121c19]">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10">
            <ShieldCheck size={26} />
          </div>
          <p className="mt-6 text-xs font-bold uppercase tracking-[0.2em] text-emerald-600">Restricted access</p>
          <h1 className="mt-2 text-4xl font-black tracking-[-0.05em]">Admin console</h1>
          <p className="mt-3 text-sm leading-6 text-slate-500">
            Review user registry, platform analytics, and security audit logs. Clinical records are not displayed here.
          </p>
          <form onSubmit={submit} className="mt-8 space-y-4">
            <div>
              <label className="block text-sm font-bold mb-1">Administrator email</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  required
                  className="h-13 w-full rounded-2xl border border-slate-200 bg-white pl-11 pr-4 outline-none focus:border-emerald-500 dark:border-white/10 dark:bg-white/5"
                  placeholder="admin@medicare.local"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-bold mb-1">Administrator password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  type="password"
                  required
                  className="h-13 w-full rounded-2xl border border-slate-200 bg-white pl-11 pr-4 outline-none focus:border-emerald-500 dark:border-white/10 dark:bg-white/5"
                  placeholder="Enter admin password"
                />
              </div>
            </div>
            {error && <p className="text-sm font-semibold text-rose-600 dark:text-rose-400">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="flex h-13 w-full items-center justify-center gap-3 rounded-2xl bg-[#0d4639] font-bold text-white transition hover:bg-[#0a3b30] disabled:opacity-60 cursor-pointer"
            >
              {loading ? "Verifying credentials…" : "Enter admin console"}
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-[#0d4639]">
                <ArrowUpRight size={17} />
              </span>
            </button>
          </form>
          <div className="mt-8 flex items-center gap-2 text-xs text-slate-500">
            <HeartPulse size={14} className="text-emerald-500" /> Secure administrative authentication
          </div>
        </div>
      </div>
    </div>
  );
}

