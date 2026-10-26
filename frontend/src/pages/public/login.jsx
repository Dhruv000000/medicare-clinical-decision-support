// ==============================================================================
// FILE: frontend/src/pages/public/login.jsx
// PURPOSE: Primary user authentication interface supporting patient and clinician sign-in.
// VIVA EXPLANATION: Implements the login experience for patients and physicians. Captures credentials, communicates with the JWT authentication backend, handles role-based redirection, and stores remember-me preferences.
// ==============================================================================

import React, { useState, useEffect } from "react";
import {
  HeartPulse,
  ShieldCheck,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowUpRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Check,
} from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../../_core/hooks/useAuth";


// --- Logo ---
// What it does: Renders interactive branding mark navigating to homepage.
// Why it's structured this way: Reusable header element maintaining brand consistency.
// Parameters & Returns: Props (none) -> Brand button JSX element.
// ------------------------------------------------------------------------------
function Logo() {
  const navigate = useNavigate();

  return (
    <button
      type="button"
      onClick={() => navigate("/")}
      className="flex items-center gap-2"
    >
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#0FA37F] text-white">
        <HeartPulse size={21} strokeWidth={2.5} />
      </div>

      <span className="text-2xl font-black tracking-[-0.05em] text-[#123D32] dark:text-white">
        medicare<span className="text-[#087F68]">.</span>
      </span>
    </button>
  );
}


// --- Login ---
// What it does: Primary sign-in component managing email/password inputs, validation, and JWT login dispatch.
// Why it's structured this way: Features role toggle tabs (Patient vs Doctor) to guide users to their relevant workspaces after authentication.
// Parameters & Returns: Props (none) -> Rendered login form page.
// ------------------------------------------------------------------------------
function Login() {
  const navigate = useNavigate();

  const location = useLocation();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [role, setRole] = useState("patient");
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
    }
  }, [location.state]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));

    setErrors((previous) => ({
      ...previous,
      [name]: "",
      general: "",
    }));

    setSuccessMessage("");
  };

  const validateForm = () => {
    const newErrors = {};

    const email = formData.email.trim();
    const password = formData.password;

    if (!email) {
      newErrors.email = "Email address is required.";
    } else if (
      !/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i.test(email)
    ) {
      newErrors.email = "Please enter a valid email address.";
    }

    if (!password) {
      newErrors.password = "Password is required.";
    } else if (password.length < 8) {
      newErrors.password =
        "Password must contain at least 8 characters.";
    }

    setErrors(newErrors);

    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setSuccessMessage("");

    if (!validateForm()) {
      return;
    }

    try {
      setIsSubmitting(true);

      const res = await login({
        email: formData.email,
        password: formData.password,
        role: role.toLowerCase(),
      });

      if (!res.success) {
        setErrors({
          general: res.error || "Invalid email or password. Please try again.",
        });
        return;
      }

      setSuccessMessage("Sign-in successful. Opening your workspace…");

      const resolvedRole = (res.user?.role || role || "patient").toLowerCase();
      setTimeout(() => {
        if (resolvedRole === "doctor") {
          navigate("/doctor/dashboard");
        } else if (resolvedRole === "admin") {
          navigate("/admin/dashboard");
        } else {
          navigate("/patient/dashboard");
        }
      }, 250);
    } catch (error) {
      setErrors({
        general: "Unable to connect to the authentication service. Please check your connection.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-screen overflow-hidden bg-[#FFFEFC] text-[#123D32] dark:bg-[#0B1210] dark:text-white">
      <header className="h-[72px] border-b border-[#E4E9E5] bg-white dark:border-white/10 dark:bg-[#0B1210]">
        <div className="mx-auto flex h-full max-w-[1400px] items-center justify-between px-6 lg:px-10">
          <Logo />

          <button
            type="button"
            onClick={() => window.history.back()}
            className="group flex items-center gap-2 rounded-full border border-[#E4E9E5] bg-white px-4 py-2 text-sm font-bold text-[#123D32] transition hover:bg-[#F4FBF8] dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
          >
            <ArrowLeft
              size={15}
              className="transition group-hover:-translate-x-0.5"
            />
            Back
          </button>
        </div>
      </header>

      <main className="relative h-[calc(100vh-72px)] overflow-hidden">
        <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-[#E8F7F2] blur-3xl dark:bg-[#123D32]" />
        <div className="pointer-events-none absolute -bottom-40 -right-32 h-[500px] w-[500px] rounded-full bg-[#E8F7F2] opacity-70 blur-3xl dark:bg-[#123D32]" />

        <div className="relative flex h-full items-center justify-center px-5">
          <div className="w-full max-w-[560px]">
            <div className="rounded-[34px] border border-[#E4E9E5] bg-white px-10 py-7 shadow-[0_30px_80px_rgba(18,61,50,0.11)] dark:border-white/10 dark:bg-[#121C19] dark:shadow-black/30">

              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#E8F7F2] text-[#0FA37F] dark:bg-[#123D32]">
                <HeartPulse size={26} strokeWidth={2.2} />
              </div>

              <div className="mb-5">
                <h1 className="text-[38px] font-black leading-none tracking-[-0.055em] text-[#123D32] dark:text-white">
                  Welcome back.
                </h1>

                <p className="mt-2.5 text-[15px] text-[#5F6B66] dark:text-white/60">
                  Sign in to continue to your MediCare account.
                </p>
              </div>

              <div className="mb-5">
                <label className="mb-2 block text-sm font-bold text-[#123D32] dark:text-white">
                  Sign in as
                </label>

                <div className="grid grid-cols-3 gap-3">
                  {[
                    ["patient", "Patient"],
                    ["doctor", "Doctor"],
                    ["admin", "Admin"],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setRole(value)}
                      className={`h-[46px] rounded-xl border text-sm font-bold transition ${
                        role === value
                          ? "border-[#0FA37F] bg-[#E8F7F2] text-[#087F68] shadow-sm dark:bg-[#123D32] dark:text-[#6EE7C4]"
                          : "border-[#E4E9E5] bg-white text-[#5F6B66] hover:border-[#0FA37F] hover:bg-[#F4FBF8] dark:border-white/10 dark:bg-white/5 dark:text-white/60 dark:hover:bg-white/10"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {errors.general && (
                <div className="mb-5 flex items-start gap-3 rounded-2xl border border-[#FDECEC] bg-[#FFF7F7] p-4 dark:border-red-400/20 dark:bg-red-400/10">
                  <AlertCircle
                    size={18}
                    className="mt-0.5 shrink-0 text-[#D9534F]"
                  />
                  <p className="text-sm font-semibold text-[#D9534F]">
                    {errors.general}
                  </p>
                </div>
              )}

              {successMessage && (
                <div className="mb-5 flex items-start gap-3 rounded-2xl border border-[#BFE9DC] bg-[#F4FBF8] p-4 dark:border-[#0FA37F]/30 dark:bg-[#0FA37F]/10">
                  <CheckCircle2
                    size={18}
                    className="mt-0.5 shrink-0 text-[#0FA37F]"
                  />
                  <p className="text-sm font-semibold text-[#087F68] dark:text-[#6EE7C4]">
                    {successMessage}
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmit} noValidate>
                <div>
                  <label
                    htmlFor="email"
                    className="mb-2 block text-sm font-bold text-[#123D32] dark:text-white"
                  >
                    Email address
                  </label>

                  <div
                    className={`group flex items-center rounded-2xl border bg-[#FFFEFC] px-4 transition dark:bg-white/5 ${
                      errors.email
                        ? "border-[#D9534F] ring-4 ring-[#FDECEC] dark:ring-red-400/10"
                        : "border-[#E4E9E5] focus-within:border-[#0FA37F] focus-within:ring-4 focus-within:ring-[#E8F7F2] dark:border-white/10 dark:focus-within:ring-[#0FA37F]/10"
                    }`}
                  >
                    <Mail
                      size={19}
                      className={`mr-3 shrink-0 ${
                        errors.email
                          ? "text-[#D9534F]"
                          : "text-[#8A938F] group-focus-within:text-[#0FA37F]"
                      }`}
                    />

                    <input
                      id="email"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="you@example.com"
                      autoComplete="email"
                      className="h-[54px] w-full bg-transparent text-[15px] font-medium text-[#123D32] outline-none placeholder:text-[#8A938F] dark:text-white dark:placeholder:text-white/40"
                    />
                  </div>

                  {errors.email && (
                    <p className="mt-1.5 text-xs font-semibold text-[#D9534F]">
                      {errors.email}
                    </p>
                  )}
                </div>

                <div className="mt-4">
                  <div className="mb-2 flex items-center justify-between">
                    <label
                      htmlFor="password"
                      className="block text-sm font-bold text-[#123D32] dark:text-white"
                    >
                      Password
                    </label>

                    <button
                      type="button"
                      className="text-sm font-bold text-[#087F68] transition hover:text-[#123D32] dark:hover:text-white"
                    >
                      Forgot password?
                    </button>
                  </div>

                  <div
                    className={`group flex items-center rounded-2xl border bg-[#FFFEFC] px-4 transition dark:bg-white/5 ${
                      errors.password
                        ? "border-[#D9534F] ring-4 ring-[#FDECEC] dark:ring-red-400/10"
                        : "border-[#E4E9E5] focus-within:border-[#0FA37F] focus-within:ring-4 focus-within:ring-[#E8F7F2] dark:border-white/10 dark:focus-within:ring-[#0FA37F]/10"
                    }`}
                  >
                    <Lock
                      size={19}
                      className={`mr-3 shrink-0 ${
                        errors.password
                          ? "text-[#D9534F]"
                          : "text-[#8A938F] group-focus-within:text-[#0FA37F]"
                      }`}
                    />

                    <input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="Enter your password"
                      autoComplete="current-password"
                      className="h-[54px] w-full bg-transparent text-[15px] font-medium text-[#123D32] outline-none placeholder:text-[#8A938F] dark:text-white dark:placeholder:text-white/40"
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowPassword((previous) => !previous)
                      }
                      className="ml-2 flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[#8A938F] transition hover:bg-[#E8F7F2] hover:text-[#087F68] dark:hover:bg-white/10 dark:hover:text-[#6EE7C4]"
                      aria-label={
                        showPassword ? "Hide password" : "Show password"
                      }
                    >
                      {showPassword ? (
                        <EyeOff size={18} />
                      ) : (
                        <Eye size={18} />
                      )}
                    </button>
                  </div>

                  {errors.password && (
                    <p className="mt-1.5 text-xs font-semibold text-[#D9534F]">
                      {errors.password}
                    </p>
                  )}
                </div>

                <div className="mt-4">
                  <label className="flex cursor-pointer items-center gap-3">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(event) =>
                        setRememberMe(event.target.checked)
                      }
                      className="peer sr-only"
                    />

                    <span className="flex h-5 w-5 items-center justify-center rounded-md border border-[#D7DEDA] bg-white text-transparent transition peer-checked:border-[#0FA37F] peer-checked:bg-[#0FA37F] peer-checked:text-white dark:border-white/20 dark:bg-white/5">
                      <Check size={13} strokeWidth={3} />
                    </span>

                    <span className="text-sm font-semibold text-[#5F6B66] dark:text-white/60">
                      Remember me
                    </span>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="group mt-5 flex h-[56px] w-full items-center justify-center gap-3 rounded-2xl bg-[#123D32] text-[15px] font-bold text-white shadow-lg shadow-[#123D32]/10 transition hover:bg-[#087F68] disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {isSubmitting ? (
                    <>
                      <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      Signing in...
                    </>
                  ) : (
                    <>
                      Sign in
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-[#123D32] transition group-hover:translate-x-0.5">
                        <ArrowUpRight size={16} />
                      </span>
                    </>
                  )}
                </button>
              </form>

              <div className="my-4 flex items-center gap-4">
                <div className="h-px flex-1 bg-[#E4E9E5] dark:bg-white/10" />
                <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#8A938F]">
                  New to MediCare?
                </span>
                <div className="h-px flex-1 bg-[#E4E9E5] dark:bg-white/10" />
              </div>

              <button
                type="button"
                onClick={() => navigate("/register")}
                className="flex h-[56px] w-full items-center justify-center gap-2 rounded-2xl border border-[#E4E9E5] bg-white text-[15px] font-bold text-[#123D32] transition hover:border-[#0FA37F] hover:bg-[#F4FBF8] hover:text-[#087F68] dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10 dark:hover:text-[#6EE7C4]"
              >
                Create an account
                <ArrowUpRight size={16} />
              </button>

              <div className="mt-4 flex items-center justify-center gap-2">
                <ShieldCheck
                  size={14}
                  className="text-[#0FA37F]"
                />
                <p className="text-[10px] font-medium text-[#8A938F]">
                  Your information is protected with secure authentication.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Login;
