import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../_core/hooks/useAuth";

import {
  HeartPulse,
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ShieldCheck,
  ArrowUpRight,
  ArrowLeft,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

function Register() {
  const navigate = useNavigate();
  const { register, login } = useAuth();

  const [role, setRole] = useState("Patient");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
    terms: false,
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));

    setErrors((prev) => ({
      ...prev,
      [name]: "",
      general: "",
    }));

    setSuccessMessage("");
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.firstName.trim()) {
      newErrors.firstName = "First name is required.";
    }

    if (!formData.lastName.trim()) {
      newErrors.lastName = "Last name is required.";
    }

    if (!formData.email.trim()) {
      newErrors.email = "Email address is required.";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address.";
    }

    if (!formData.password) {
      newErrors.password = "Password is required.";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters.";
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password.";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match.";
    }

    if (!formData.terms) {
      newErrors.terms =
        "You must agree to the Terms of Service and Privacy Policy.";
    }

    setErrors(newErrors);

    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccessMessage("");

    if (!validate()) return;

    if (role === "Admin") {
      setErrors({ general: "Administrator accounts must use the administrator sign-in flow." });
      return;
    }

    setErrors({});
    setIsSubmitting(true);

    try {
      const regResult = await register({
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirmPassword,
        first_name: formData.firstName,
        last_name: formData.lastName,
        username: formData.email ? formData.email.split("@")[0] : "",
        role: role.toLowerCase(),
      });

      if (!regResult.success) {
        const nextErrors = {
          general: regResult.error || "Unable to create your account.",
        };
        if (regResult.fieldErrors && typeof regResult.fieldErrors === "object") {
          Object.entries(regResult.fieldErrors).forEach(([key, val]) => {
            const msg = Array.isArray(val) ? val.join(" ") : String(val);
            if (key === "email") nextErrors.email = msg;
            else if (key === "password") nextErrors.password = msg;
            else if (key === "confirm_password" || key === "confirmPassword")
              nextErrors.confirmPassword = msg;
            else if (key === "first_name" || key === "firstName")
              nextErrors.firstName = msg;
            else if (key === "last_name" || key === "lastName")
              nextErrors.lastName = msg;
            else if (key === "role") nextErrors.role = msg;
            else if (key === "non_field_errors" || key === "detail")
              nextErrors.general = msg;
          });
        }
        setErrors(nextErrors);
        return;
      }

      setSuccessMessage("Account created successfully! Signing in…");

      // Auto-login to obtain JWT tokens and navigate to dashboard
      const loginRes = await login({
        email: formData.email,
        password: formData.password,
      });

      if (loginRes?.success) {
        setTimeout(() => {
          if (role.toLowerCase() === "doctor") {
            navigate("/doctor/dashboard");
          } else {
            navigate("/patient/dashboard");
          }
        }, 300);
      } else {
        // Redirect to login page if auto-login fails
        setTimeout(() => {
          navigate("/login", {
            state: { message: "Account created successfully! Please sign in to continue." },
          });
        }, 800);
      }
    } catch (error) {
      setErrors({ general: error?.message || "Unable to create your account." });
    } finally {
      setIsSubmitting(false);
    }
  };


  const inputClass = (field) => `
    h-[52px] w-full rounded-xl border bg-white
    px-4 text-[15px] text-[#173f35]
    outline-none transition
    dark:border-white/10 dark:bg-white/5 dark:text-white
    dark:placeholder:text-white/40
    ${
      errors[field]
        ? "border-red-400 ring-2 ring-red-100 dark:ring-red-400/10"
        : "border-[#dfe7e4] focus:border-[#00a889] focus:ring-2 focus:ring-[#d9f5ee] dark:border-white/10 dark:focus:ring-[#00a889]/10"
    }
  `;

  return (
    <div className="min-h-screen overflow-y-auto bg-gradient-to-br from-[#effcf8] via-white to-[#f2fcf9] text-[#073d32] dark:from-[#0B1210] dark:via-[#0F1916] dark:to-[#10201B] dark:text-white">
      {/* HEADER */}
      <header className="h-[72px] border-b border-[#e4ebe8] bg-white dark:border-white/10 dark:bg-[#0B1210]">
        <div className="mx-auto flex h-full items-center justify-between px-8 lg:px-12">
          {/* LOGO */}
          <button
            type="button"
            onClick={() => navigate("/")}
            className="flex items-center gap-3"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#0eaa8a] text-white">
              <HeartPulse size={24} strokeWidth={2.5} />
            </div>

            <span className="text-[26px] font-extrabold tracking-[-1.5px] text-[#123f35] dark:text-white">
              medicare<span className="text-[#009b80]">.</span>
            </span>
          </button>

          {/* BACK */}
          <button
            type="button"
            onClick={() => navigate("/login")}
            className="flex items-center gap-2 rounded-full border border-[#dfe7e4] bg-white px-5 py-2.5 text-[14px] font-bold text-[#173f35] transition hover:bg-[#f4faf8] dark:border-white/10 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
          >
            <ArrowLeft size={16} />
            Back to login
          </button>
        </div>
      </header>

      {/* PAGE */}
      <main className="flex min-h-[calc(100vh-72px)] items-center justify-center px-6 py-8">
        {/* CARD */}
        <div className="w-full max-w-[850px] rounded-[28px] border border-[#dfe8e4] bg-white px-9 py-6 shadow-[0_20px_60px_rgba(20,70,60,0.10)] dark:border-white/10 dark:bg-[#121C19] dark:shadow-black/30">
          {/* TOP */}
          <div className="mb-4 flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#e7f8f3] text-[#00a889] dark:bg-[#123D32]">
              <HeartPulse size={25} strokeWidth={2.5} />
            </div>

            <div>
              <h1 className="text-[31px] font-extrabold leading-none tracking-[-1.5px] text-[#073d32] dark:text-white">
                Create your account.
              </h1>

              <p className="mt-1.5 text-[14px] text-[#63746f] dark:text-white/60">
                Join MediCare and take control of your healthcare journey.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            {/* ROLE */}
            <div className="mb-3.5">
              <label className="mb-1.5 block text-[14px] font-bold text-[#073d32] dark:text-white">
                I am a
              </label>

              <div className="grid grid-cols-3 gap-3">
                {["Patient", "Doctor", "Admin"].map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setRole(item)}
                    className={`h-[46px] rounded-xl border text-[15px] font-bold transition ${
                      role === item
                        ? "border-[#00a889] bg-[#e8f8f4] text-[#008f78] dark:bg-[#123D32] dark:text-[#6EE7C4]"
                        : "border-[#dfe7e4] bg-white text-[#64736f] hover:bg-[#f8fcfb] dark:border-white/10 dark:bg-white/5 dark:text-white/60 dark:hover:bg-white/10"
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>

            {errors.general && (
              <div className="mb-3.5 flex items-start gap-3 rounded-2xl border border-[#FDECEC] bg-[#FFF7F7] p-3.5 dark:border-red-400/20 dark:bg-red-400/10">
                <AlertCircle
                  size={18}
                  className="mt-0.5 shrink-0 text-[#D9534F]"
                />
                <p className="text-[13px] font-semibold text-[#D9534F]">
                  {errors.general}
                </p>
              </div>
            )}

            {successMessage && (
              <div className="mb-3.5 flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-3.5 dark:border-emerald-800/30 dark:bg-emerald-950/20">
                <CheckCircle2
                  size={18}
                  className="mt-0.5 shrink-0 text-emerald-600 dark:text-emerald-400"
                />
                <p className="text-[13px] font-semibold text-emerald-700 dark:text-emerald-300">
                  {successMessage}
                </p>
              </div>
            )}

            {/* NAME */}
            <div className="grid grid-cols-2 gap-3.5">
              <div>
                <label className="mb-1.5 block text-[14px] font-bold text-[#073d32] dark:text-white">
                  First name
                </label>

                <div className="relative">
                  <User
                    size={18}
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8a9894]"
                  />

                  <input
                    type="text"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleChange}
                    placeholder="Camila"
                    className={`${inputClass("firstName")} pl-11`}
                  />
                </div>

                {errors.firstName && (
                  <p className="mt-1 text-[11px] text-red-500">
                    {errors.firstName}
                  </p>
                )}
              </div>

              <div>
                <label className="mb-1.5 block text-[14px] font-bold text-[#073d32] dark:text-white">
                  Last name
                </label>

                <div className="relative">
                  <User
                    size={18}
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8a9894]"
                  />

                  <input
                    type="text"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleChange}
                    placeholder="Eli"
                    className={`${inputClass("lastName")} pl-11`}
                  />
                </div>

                {errors.lastName && (
                  <p className="mt-1 text-[11px] text-red-500">
                    {errors.lastName}
                  </p>
                )}
              </div>
            </div>

            {/* EMAIL */}
            <div className="mt-3">
              <label className="mb-1.5 block text-[14px] font-bold text-[#073d32] dark:text-white">
                Email address
              </label>

              <div className="relative">
                <Mail
                  size={18}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8a9894]"
                />

                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="you@example.com"
                  className={`${inputClass("email")} pl-11`}
                />
              </div>

              {errors.email && (
                <p className="mt-1 text-[11px] text-red-500">
                  {errors.email}
                </p>
              )}
            </div>

            {/* PASSWORD */}
            <div className="mt-3 grid grid-cols-2 gap-3.5">
              <div>
                <label className="mb-1.5 block text-[14px] font-bold text-[#073d32] dark:text-white">
                  Password
                </label>

                <div className="relative">
                  <Lock
                    size={18}
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8a9894]"
                  />

                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Password"
                    className={`${inputClass("password")} pl-11 pr-11`}
                  />

                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-[#8a9894] transition hover:text-[#008f78] dark:hover:text-[#6EE7C4]"
                  >
                    {showPassword ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>
                </div>

                {errors.password && (
                  <p className="mt-1 text-[11px] text-red-500">
                    {errors.password}
                  </p>
                )}
              </div>

              <div>
                <label className="mb-1.5 block text-[14px] font-bold text-[#073d32] dark:text-white">
                  Confirm password
                </label>

                <div className="relative">
                  <Lock
                    size={18}
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8a9894]"
                  />

                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    placeholder="Confirm"
                    className={`${inputClass("confirmPassword")} pl-11 pr-11`}
                  />

                  <button
                    type="button"
                    onClick={() =>
                      setShowConfirmPassword(!showConfirmPassword)
                    }
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-[#8a9894] transition hover:text-[#008f78] dark:hover:text-[#6EE7C4]"
                  >
                    {showConfirmPassword ? (
                      <EyeOff size={18} />
                    ) : (
                      <Eye size={18} />
                    )}
                  </button>
                </div>

                {errors.confirmPassword && (
                  <p className="mt-1 text-[11px] text-red-500">
                    {errors.confirmPassword}
                  </p>
                )}
              </div>
            </div>

            {/* TERMS */}
            <div className="mt-3">
              <label className="flex items-center gap-2.5">
                <input
                  type="checkbox"
                  name="terms"
                  checked={formData.terms}
                  onChange={handleChange}
                  className="h-[18px] w-[18px] accent-[#00a889]"
                />

                <span className="text-[13px] text-[#536762] dark:text-white/60">
                  I agree to the{" "}
                  <span className="font-bold text-[#008f78]">
                    Terms of Service
                  </span>{" "}
                  and{" "}
                  <span className="font-bold text-[#008f78]">
                    Privacy Policy
                  </span>
                  .
                </span>
              </label>

              {errors.terms && (
                <p className="mt-1 text-[11px] text-red-500">
                  {errors.terms}
                </p>
              )}
            </div>

            {/* BUTTON */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-3 flex h-[54px] w-full items-center justify-center gap-3 rounded-xl bg-[#0d4639] text-[15px] font-bold text-white shadow-[0_7px_18px_rgba(13,70,57,0.15)] transition hover:bg-[#0a3b30] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isSubmitting ? "Creating account…" : "Create account"}

              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-[#0d4639]">
                <ArrowUpRight size={17} strokeWidth={2.5} />
              </span>
            </button>

            {/* SIGN IN */}
            <div className="mt-3 text-center text-[14px] text-[#697873] dark:text-white/60">
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => navigate("/login")}
                className="font-bold text-[#008f78] hover:underline"
              >
                Sign in
              </button>
            </div>

            {/* SECURITY */}
            <div className="mt-2 flex items-center justify-center gap-2 text-[11px] text-[#71827d] dark:text-white/40">
              <ShieldCheck
                size={14}
                className="text-[#00a889]"
              />
              Your information is protected with secure authentication.
            </div>
          </form>
        </div>
      </main>
    </div>
  );
}

export default Register;
