import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Bell,
  Brain,
  ChevronDown,
  CircleDot,
  ClipboardList,
  FileText,
  Heart,
  Home,
  LogIn,
  Lock,
  Mail,
  Moon,
  Pill,
  Save,
  Search,
  Settings as SettingsIcon,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Sun,
  TrendingUp,
  UserRound,
  X,
} from "lucide-react";
import { useAuth } from "../../../_core/hooks/useAuth";
import patientService from "../../../services/patientService";
import PatientSidebar from "./sidebar";

const ROUTES = {
  dashboard: "/patient/dashboard",
  healthTrends: "/patient/health-trends",
  appointments: "/patient/appointments",
  medicalRecords: "/patient/medical-records",
  labTests: "/patient/reports-lab-tests",
  medications: "/patient/medications",
  symptomAnalysis: "/patient/symptom-analysis",
  predictions: "/patient/predictions",
  aiAssistant: "/patient/ai-assistant",
  medicineSearch: "/patient/medicine-search",
  drugInteractions: "/patient/drug-interactions",
  settings: "/patient/settings",
};

const navSections = [
  {
    title: "MAIN",
    items: [{ label: "Dashboard", icon: Home, route: ROUTES.dashboard }],
  },
  {
    title: "HEALTH",
    items: [
      { label: "Health Trends", icon: TrendingUp, route: ROUTES.healthTrends },
      { label: "Appointments", icon: Activity, route: ROUTES.appointments },
    ],
  },
  {
    title: "MEDICAL",
    items: [
      { label: "Medical Records", icon: FileText, route: ROUTES.medicalRecords },
      { label: "Reports & Lab Tests", icon: ClipboardList, route: ROUTES.labTests },
      { label: "Medications", icon: Pill, route: ROUTES.medications },
    ],
  },
  {
    title: "AI HEALTH",
    items: [
      { label: "Symptom Analysis", icon: Stethoscope, route: ROUTES.symptomAnalysis },
      { label: "Predictions", icon: Brain, route: ROUTES.predictions },
      { label: "AI Assistant", icon: Sparkles, route: ROUTES.aiAssistant },
    ],
  },
  {
    title: "MEDICINES",
    items: [
      { label: "Medicine Search", icon: CircleDot, route: ROUTES.medicineSearch },
      { label: "Drug Interactions", icon: AlertTriangle, route: ROUTES.drugInteractions },
    ],
  },
];

function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window === "undefined") return false;
    const saved = localStorage.getItem("medicare-theme");
    if (saved === "dark") return true;
    if (saved === "light") return false;
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  });

  useEffect(() => {
    localStorage.setItem("medicare-theme", darkMode ? "dark" : "light");
    document.documentElement.classList.toggle("dark", darkMode);
    document.documentElement.style.colorScheme = darkMode ? "dark" : "light";
    document.body.style.background = darkMode ? "#0b1413" : "#f8faf9";
  }, [darkMode]);

  return [darkMode, setDarkMode];
}

function isActivePath(pathname, route) {
  return pathname.replace(/\/$/, "") === route.replace(/\/$/, "");
}

function Sidebar({ darkMode }) {
  const location = useLocation();

  const colors = {
    sidebar: darkMode ? "bg-[#101918]" : "bg-white",
    border: darkMode ? "border-slate-800" : "border-slate-100",
    text: darkMode ? "text-slate-300" : "text-slate-600",
    hover: darkMode ? "hover:bg-slate-800/60" : "hover:bg-slate-50",
    active: "bg-emerald-500/10 text-emerald-500 font-semibold",
  };

  return (
    <aside
      className={`flex h-full w-[255px] shrink-0 flex-col overflow-y-auto border-r ${colors.border} ${colors.sidebar} px-4 py-5`}
    >
      <Link
        to={ROUTES.dashboard}
        className="mb-5 flex shrink-0 items-center gap-3 px-3"
      >
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 shadow-sm">
          <Heart size={21} strokeWidth={2.5} className="text-white" />
        </div>
        <span
          className={`text-[21px] font-bold tracking-[-0.5px] ${
            darkMode ? "text-white" : "text-emerald-900"
          }`}
        >
          medicare.
        </span>
      </Link>

      <nav className="min-h-0 flex-1">
        <div className="space-y-3">
          {navSections.map((section) => (
            <div key={section.title}>
              <p className="mb-1.5 px-3 text-[10px] font-semibold tracking-[0.12em] text-slate-500">
                {section.title}
              </p>

              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActivePath(location.pathname, item.route);

                  return (
                    <Link
                      key={item.label}
                      to={item.route}
                      aria-current={active ? "page" : undefined}
                      className={`relative flex w-full items-center gap-3 rounded-lg px-3 py-[8px] text-left text-[13px] transition ${
                        active ? colors.active : `${colors.text} ${colors.hover}`
                      }`}
                    >
                      {active && (
                        <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-emerald-500" />
                      )}

                      <Icon
                        size={18}
                        strokeWidth={1.8}
                        className={
                          active
                            ? "text-emerald-500"
                            : darkMode
                              ? "text-slate-400"
                              : "text-slate-500"
                        }
                      />

                      <span className="truncate">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </nav>

      <div
        className={`mt-3 shrink-0 border-t pt-3 ${
          darkMode ? "border-slate-800" : "border-slate-100"
        }`}
      >
        <Link
          to={ROUTES.settings}
          className={`flex w-full items-center gap-3 rounded-lg px-3 py-[8px] text-[13px] transition ${
            isActivePath(location.pathname, ROUTES.settings)
              ? colors.active
              : `${colors.text} ${colors.hover}`
          }`}
        >
          <SettingsIcon size={18} strokeWidth={1.8} />
          Settings
        </Link>

        <Link
          to="/login"
          className={`flex w-full items-center gap-3 rounded-lg px-3 py-[8px] text-[13px] transition ${colors.text} ${colors.hover}`}
        >
          <LogIn size={18} strokeWidth={1.8} />
          Logout
        </Link>
      </div>
    </aside>
  );
}

function Header({ darkMode, setDarkMode }) {
  const { user } = useAuth();
  const displayName =
    user?.full_name ||
    (user?.first_name ? `${user.first_name} ${user.last_name || ""}`.trim() : null) ||
    user?.email ||
    "Patient";

  return (
    <header
      className={`flex h-[78px] shrink-0 items-center justify-between border-b px-8 ${
        darkMode
          ? "border-slate-800 bg-[#111c1b]"
          : "border-slate-100 bg-white"
      }`}
    >
      <div>
        <h1
          className={`text-[26px] font-bold tracking-[-0.7px] ${
            darkMode ? "text-white" : "text-emerald-950"
          }`}
        >
          Settings
        </h1>

        <p
          className={`mt-1 text-[12px] ${
            darkMode ? "text-slate-500" : "text-slate-500"
          }`}
        >
          Manage your account, preferences and privacy
        </p>
      </div>

      <div className="flex items-center gap-4">
        <div
          className={`flex h-10 w-[250px] items-center gap-3 rounded-xl border px-4 ${
            darkMode
              ? "border-slate-700 bg-slate-900/40"
              : "border-slate-200 bg-white"
          }`}
        >
          <Search size={17} className="text-slate-500" />
          <input
            placeholder="Search settings..."
            className={`w-full bg-transparent text-sm outline-none ${
              darkMode
                ? "text-white placeholder:text-slate-500"
                : "text-slate-700 placeholder:text-slate-400"
            }`}
          />
        </div>

        <button
          type="button"
          onClick={() => setDarkMode((value) => !value)}
          className={`flex h-10 w-10 items-center justify-center rounded-xl border transition ${
            darkMode
              ? "border-slate-700 bg-slate-900 text-yellow-300 hover:bg-slate-800"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
          }`}
          aria-label="Toggle theme"
        >
          {darkMode ? <Sun size={19} /> : <Moon size={19} />}
        </button>

        <button
          type="button"
          className={`relative ${
            darkMode ? "text-slate-300" : "text-slate-700"
          }`}
          aria-label="Notifications"
        >
          <Bell size={21} strokeWidth={1.7} />
          <span
            className={`absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 ${
              darkMode ? "border-[#111c1b]" : "border-white"
            } bg-emerald-500`}
          />
        </button>

        <Link to={ROUTES.settings} className="flex items-center gap-3">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 text-white font-semibold text-xs"
          >
            {displayName.slice(0, 2).toUpperCase()}
          </div>

          <span
            className={`text-[14px] font-semibold ${
              darkMode ? "text-slate-200" : "text-slate-800"
            }`}
          >
            {displayName}
          </span>

          <ChevronDown
            size={16}
            className={darkMode ? "text-slate-400" : "text-slate-600"}
          />
        </Link>
      </div>
    </header>
  );
}

function Field({ label, value, onChange, darkMode, type = "text" }) {
  return (
    <label
      className={`block text-[9px] font-medium ${
        darkMode ? "text-slate-300" : "text-slate-700"
      }`}
    >
      {label}

      <div
        className={`mt-1.5 flex items-center rounded-lg border px-3 ${
          darkMode
            ? "border-slate-700 bg-[#101918]"
            : "border-slate-200 bg-white"
        }`}
      >
        <input
          type={type}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className={`w-full bg-transparent py-2 text-[10px] outline-none ${
            darkMode ? "text-slate-200" : "text-slate-700"
          }`}
        />
      </div>
    </label>
  );
}

function Toggle({ checked, onChange, darkMode }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className={`relative h-5 w-9 rounded-full transition ${
        checked ? "bg-emerald-500" : darkMode ? "bg-slate-700" : "bg-slate-300"
      }`}
      aria-pressed={checked}
    >
      <span
        className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition ${
          checked ? "left-[18px]" : "left-0.5"
        }`}
      />
    </button>
  );
}

function SectionCard({ darkMode, title, description, children }) {
  return (
    <section
      className={`rounded-[14px] border p-4 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white"
      }`}
    >
      <h2
        className={`text-[13px] font-bold ${
          darkMode ? "text-white" : "text-emerald-950"
        }`}
      >
        {title}
      </h2>

      {description && (
        <p
          className={`mt-1 text-[9px] ${
            darkMode ? "text-slate-500" : "text-slate-500"
          }`}
        >
          {description}
        </p>
      )}

      <div className="mt-4">{children}</div>
    </section>
  );
}

export default function Settings() {
  const [darkMode, setDarkMode] = useDarkMode();
  const { user, refresh } = useAuth();

  const [profile, setProfile] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    dateOfBirth: "",
    bloodGroup: "",
    gender: "",
    address: "",
    emergencyContact: "",
  });

  const [notifications, setNotifications] = useState({
    appointments: true,
    medications: true,
    reports: true,
    aiInsights: true,
    marketing: false,
  });

  const [privacy, setPrivacy] = useState({
    shareAnalytics: true,
    personalizedInsights: true,
  });

  const [language, setLanguage] = useState("English");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      try {
        const res = await patientService.getProfile();
        if (res) {
          setProfile({
            firstName: res.first_name || user?.first_name || "",
            lastName: res.last_name || user?.last_name || "",
            email: res.email || user?.email || "",
            phone: res.phone || "",
            dateOfBirth: res.date_of_birth || "",
            bloodGroup: res.blood_group || "",
            gender: res.gender || "",
            address: res.address || "",
            emergencyContact: res.emergency_contact || "",
          });
        }
      } catch (err) {
        console.warn("Could not load backend patient profile:", err);
        if (user) {
          setProfile((prev) => ({
            ...prev,
            firstName: user.first_name || "",
            lastName: user.last_name || "",
            email: user.email || "",
          }));
        }
      }
    }
    loadProfile();

    try {
      const storedNotifications = localStorage.getItem("medicare-notification-settings");
      const storedPrivacy = localStorage.getItem("medicare-privacy-settings");
      const storedLanguage = localStorage.getItem("medicare-language");

      if (storedNotifications) setNotifications(JSON.parse(storedNotifications));
      if (storedPrivacy) setPrivacy(JSON.parse(storedPrivacy));
      if (storedLanguage) setLanguage(storedLanguage);
    } catch {
      // Ignore malformed localStorage values.
    }
  }, [user]);

  const saveChanges = async () => {
    try {
      setSaving(true);
      setSaveError("");
      await patientService.updateProfile({
        first_name: profile.firstName,
        last_name: profile.lastName,
        phone: profile.phone,
        date_of_birth: profile.dateOfBirth || null,
        blood_group: profile.bloodGroup || "",
        gender: profile.gender || "",
        address: profile.address || "",
        emergency_contact: profile.emergencyContact || "",
      });

      if (typeof refresh === "function") {
        await refresh();
      }

      localStorage.setItem("medicare-notification-settings", JSON.stringify(notifications));
      localStorage.setItem("medicare-privacy-settings", JSON.stringify(privacy));
      localStorage.setItem("medicare-language", language);

      setSaved(true);
      window.setTimeout(() => setSaved(false), 2200);
    } catch (err) {
      console.error("Failed to update profile:", err);
      const errorDetails = err.response?.data?.error?.details;
      let errorMsg = "";
      if (errorDetails && typeof errorDetails === "object") {
        errorMsg = Object.entries(errorDetails)
          .map(([field, errs]) => `${field.replace(/_/g, " ")}: ${Array.isArray(errs) ? errs.join(" ") : errs}`)
          .join(" | ");
      } else {
        errorMsg =
          err.response?.data?.error?.message ||
          err.response?.data?.message ||
          err.response?.data?.detail ||
          "Failed to save profile changes. Please try again.";
      }
      setSaveError(errorMsg);
    } finally {
      setSaving(false);
    }
  };

  const displayName =
    user?.full_name ||
    (profile.firstName ? `${profile.firstName} ${profile.lastName}`.trim() : null) ||
    profile.email ||
    "Patient";

  return (
    <div
      className={`h-screen w-full overflow-hidden p-2 ${
        darkMode
          ? "bg-[#0b1413] text-white"
          : "bg-[#f8faf9] text-slate-900"
      }`}
    >
      <div
        className={`flex h-full w-full overflow-hidden rounded-[18px] border ${
          darkMode
            ? "border-slate-800 bg-[#111c1b]"
            : "border-slate-200 bg-white"
        }`}
      >
        <PatientSidebar darkMode={darkMode} />

        <main className="ml-[255px] flex min-w-0 flex-1 flex-col overflow-hidden">
          <Header darkMode={darkMode} setDarkMode={setDarkMode} />

          <div className="min-h-0 flex-1 overflow-y-auto px-8 py-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2
                  className={`text-[19px] font-bold ${
                    darkMode ? "text-white" : "text-emerald-950"
                  }`}
                >
                  Account Settings
                </h2>

                <p
                  className={`mt-1 text-[11px] ${
                    darkMode ? "text-slate-500" : "text-slate-500"
                  }`}
                >
                  Update your personal information and preferences
                </p>
              </div>

              <button
                type="button"
                onClick={saveChanges}
                disabled={saving}
                className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-[10px] font-semibold text-white hover:bg-emerald-600 disabled:opacity-50"
              >
                <Save size={13} />
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>

            {saved && (
              <div
                className={`mt-3 flex items-center gap-2 rounded-xl border px-3 py-2 text-[9px] ${
                  darkMode
                    ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-400"
                    : "border-emerald-100 bg-emerald-50 text-emerald-700"
                }`}
              >
                <ShieldCheck size={12} />
                Profile changes saved successfully to your health record.
              </div>
            )}

            {saveError && (
              <div
                className={`mt-3 flex items-center gap-2 rounded-xl border px-3 py-2 text-[9px] ${
                  darkMode
                    ? "border-red-500/20 bg-red-500/5 text-red-400"
                    : "border-red-100 bg-red-50 text-red-700"
                }`}
              >
                <AlertTriangle size={12} />
                {saveError}
              </div>
            )}

            <div className="mt-4 grid grid-cols-[1fr_1fr] gap-3">
              <SectionCard
                darkMode={darkMode}
                title="Profile Information"
                description="Keep your contact and profile details up to date."
              >
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500 text-white font-semibold text-sm shadow-sm"
                  >
                    {displayName.slice(0, 2).toUpperCase()}
                  </div>

                  <div>
                    <p
                      className={`text-[11px] font-semibold ${
                        darkMode ? "text-slate-200" : "text-slate-700"
                      }`}
                    >
                      {displayName}
                    </p>

                    <p
                      className={`mt-1 text-[8px] ${
                        darkMode ? "text-slate-600" : "text-slate-400"
                      }`}
                    >
                      Patient account &bull; {profile.email || "Active"}
                    </p>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3">
                  <Field
                    label="First Name"
                    value={profile.firstName}
                    onChange={(value) =>
                      setProfile((current) => ({
                        ...current,
                        firstName: value,
                      }))
                    }
                    darkMode={darkMode}
                  />

                  <Field
                    label="Last Name"
                    value={profile.lastName}
                    onChange={(value) =>
                      setProfile((current) => ({
                        ...current,
                        lastName: value,
                      }))
                    }
                    darkMode={darkMode}
                  />

                  <Field
                    label="Email"
                    type="email"
                    value={profile.email}
                    onChange={(value) =>
                      setProfile((current) => ({
                        ...current,
                        email: value,
                      }))
                    }
                    darkMode={darkMode}
                  />

                  <Field
                    label="Phone"
                    value={profile.phone}
                    onChange={(value) =>
                      setProfile((current) => ({
                        ...current,
                        phone: value,
                      }))
                    }
                    darkMode={darkMode}
                  />

                  <Field
                    label="Date of Birth"
                    type="date"
                    value={profile.dateOfBirth}
                    onChange={(value) =>
                      setProfile((current) => ({
                        ...current,
                        dateOfBirth: value,
                      }))
                    }
                    darkMode={darkMode}
                  />

                  <Field
                    label="Blood Group"
                    value={profile.bloodGroup}
                    onChange={(value) =>
                      setProfile((current) => ({
                        ...current,
                        bloodGroup: value,
                      }))
                    }
                    darkMode={darkMode}
                  />

                  <Field
                    label="Gender"
                    value={profile.gender}
                    onChange={(value) =>
                      setProfile((current) => ({
                        ...current,
                        gender: value,
                      }))
                    }
                    darkMode={darkMode}
                  />

                  <Field
                    label="Emergency Contact"
                    value={profile.emergencyContact}
                    onChange={(value) =>
                      setProfile((current) => ({
                        ...current,
                        emergencyContact: value,
                      }))
                    }
                    darkMode={darkMode}
                  />

                  <div className="col-span-2">
                    <Field
                      label="Address"
                      value={profile.address}
                      onChange={(value) =>
                        setProfile((current) => ({
                          ...current,
                          address: value,
                        }))
                      }
                      darkMode={darkMode}
                    />
                  </div>

                  <label
                    className={`col-span-2 block text-[9px] font-medium ${
                      darkMode ? "text-slate-300" : "text-slate-700"
                    }`}
                  >
                    Language
                    <select
                      value={language}
                      onChange={(event) => setLanguage(event.target.value)}
                      className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[10px] outline-none ${
                        darkMode
                          ? "border-slate-700 bg-[#101918] text-slate-200"
                          : "border-slate-200 bg-white text-slate-700"
                      }`}
                    >
                      <option>English</option>
                      <option>Hindi</option>
                      <option>Marathi</option>
                    </select>
                  </label>
                </div>
              </SectionCard>

              <SectionCard
                darkMode={darkMode}
                title="Security"
                description="Protect your account with strong authentication controls."
              >
                <div className="space-y-3">
                  <div
                    className={`flex items-center justify-between rounded-xl border p-3 ${
                      darkMode
                        ? "border-slate-800 bg-[#101918]"
                        : "border-slate-100 bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                          darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
                        }`}
                      >
                        <Lock size={15} className="text-emerald-500" />
                      </div>

                      <div>
                        <p
                          className={`text-[10px] font-semibold ${
                            darkMode ? "text-slate-200" : "text-slate-700"
                          }`}
                        >
                          Password
                        </p>

                        <p
                          className={`mt-1 text-[8px] ${
                            darkMode ? "text-slate-600" : "text-slate-400"
                          }`}
                        >
                          Last changed 60 days ago
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setShowPasswordModal(true)}
                      className="rounded-lg border border-emerald-500/20 px-3 py-1.5 text-[8px] font-medium text-emerald-500"
                    >
                      Change
                    </button>
                  </div>

                  <div
                    className={`flex items-center justify-between rounded-xl border p-3 ${
                      darkMode
                        ? "border-slate-800 bg-[#101918]"
                        : "border-slate-100 bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                          darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
                        }`}
                      >
                        <ShieldCheck
                          size={15}
                          className="text-emerald-500"
                        />
                      </div>

                      <div>
                        <p
                          className={`text-[10px] font-semibold ${
                            darkMode ? "text-slate-200" : "text-slate-700"
                          }`}
                        >
                          Two-factor authentication
                        </p>

                        <p
                          className={`mt-1 text-[8px] ${
                            darkMode ? "text-slate-600" : "text-slate-400"
                          }`}
                        >
                          Add an extra verification step
                        </p>
                      </div>
                    </div>

                    <span className="rounded-full bg-amber-500/10 px-2 py-1 text-[8px] font-medium text-amber-500">
                      Coming soon
                    </span>
                  </div>
                </div>
              </SectionCard>
            </div>

            <div className="mt-3 grid grid-cols-[1fr_1fr] gap-3">
              <SectionCard
                darkMode={darkMode}
                title="Notifications"
                description="Choose which patient updates you want to receive."
              >
                <div className="space-y-1">
                  {[
                    ["appointments", "Appointment reminders", "Upcoming visits and changes"],
                    ["medications", "Medication reminders", "Scheduled dose reminders"],
                    ["reports", "Reports & lab results", "New report availability"],
                    ["aiInsights", "AI health insights", "New trend or prediction insights"],
                    ["marketing", "Product updates", "Optional MediCare announcements"],
                  ].map(([key, title, description]) => (
                    <div
                      key={key}
                      className={`flex items-center justify-between rounded-xl border px-3 py-2.5 ${
                        darkMode ? "border-slate-800" : "border-slate-100"
                      }`}
                    >
                      <div>
                        <p
                          className={`text-[9px] font-semibold ${
                            darkMode ? "text-slate-200" : "text-slate-700"
                          }`}
                        >
                          {title}
                        </p>
                        <p
                          className={`mt-0.5 text-[8px] ${
                            darkMode ? "text-slate-600" : "text-slate-400"
                          }`}
                        >
                          {description}
                        </p>
                      </div>

                      <Toggle
                        checked={notifications[key]}
                        onChange={(checked) =>
                          setNotifications((current) => ({
                            ...current,
                            [key]: checked,
                          }))
                        }
                        darkMode={darkMode}
                      />
                    </div>
                  ))}
                </div>
              </SectionCard>

              <SectionCard
                darkMode={darkMode}
                title="Privacy & Data"
                description="Control how your dashboard uses data for personalization."
              >
                <div className="space-y-1">
                  <div
                    className={`flex items-center justify-between rounded-xl border px-3 py-2.5 ${
                      darkMode ? "border-slate-800" : "border-slate-100"
                    }`}
                  >
                    <div>
                      <p
                        className={`text-[9px] font-semibold ${
                          darkMode ? "text-slate-200" : "text-slate-700"
                        }`}
                      >
                        Anonymous usage analytics
                      </p>
                      <p
                        className={`mt-0.5 text-[8px] ${
                          darkMode ? "text-slate-600" : "text-slate-400"
                        }`}
                      >
                        Help improve the product using aggregated usage data
                      </p>
                    </div>

                    <Toggle
                      checked={privacy.shareAnalytics}
                      onChange={(checked) =>
                        setPrivacy((current) => ({
                          ...current,
                          shareAnalytics: checked,
                        }))
                      }
                      darkMode={darkMode}
                    />
                  </div>

                  <div
                    className={`flex items-center justify-between rounded-xl border px-3 py-2.5 ${
                      darkMode ? "border-slate-800" : "border-slate-100"
                    }`}
                  >
                    <div>
                      <p
                        className={`text-[9px] font-semibold ${
                          darkMode ? "text-slate-200" : "text-slate-700"
                        }`}
                      >
                        Personalized AI insights
                      </p>
                      <p
                        className={`mt-0.5 text-[8px] ${
                          darkMode ? "text-slate-600" : "text-slate-400"
                        }`}
                      >
                        Use your available dashboard data to personalize insights
                      </p>
                    </div>

                    <Toggle
                      checked={privacy.personalizedInsights}
                      onChange={(checked) =>
                        setPrivacy((current) => ({
                          ...current,
                          personalizedInsights: checked,
                        }))
                      }
                      darkMode={darkMode}
                    />
                  </div>
                </div>

                <div
                  className={`mt-3 flex items-start gap-2 rounded-xl border p-3 ${
                    darkMode
                      ? "border-amber-500/20 bg-amber-500/5"
                      : "border-amber-100 bg-amber-50/60"
                  }`}
                >
                  <ShieldCheck
                    size={13}
                    className="mt-0.5 shrink-0 text-amber-500"
                  />
                  <p
                    className={`text-[8px] leading-4 ${
                      darkMode ? "text-slate-500" : "text-slate-600"
                    }`}
                  >
                    These settings are stored locally in this frontend demo.
                    A production backend should enforce the corresponding
                    privacy and security controls.
                  </p>
                </div>
              </SectionCard>
            </div>

            <section
              className={`mt-3 rounded-[14px] border p-4 ${
                darkMode
                  ? "border-red-500/15 bg-[#15211f]"
                  : "border-red-100 bg-white"
              }`}
            >
              <h2
                className={`text-[13px] font-bold ${
                  darkMode ? "text-white" : "text-emerald-950"
                }`}
              >
                Danger Zone
              </h2>

              <p
                className={`mt-1 text-[9px] ${
                  darkMode ? "text-slate-500" : "text-slate-500"
                }`}
              >
                Actions here can affect access to your patient account.
              </p>

              <div className="mt-4 flex items-center justify-between gap-4">
                <div>
                  <p
                    className={`text-[10px] font-semibold ${
                      darkMode ? "text-slate-200" : "text-slate-700"
                    }`}
                  >
                    Delete account
                  </p>

                  <p
                    className={`mt-1 text-[8px] ${
                      darkMode ? "text-slate-600" : "text-slate-400"
                    }`}
                  >
                    Permanently remove the account in a production workflow.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setShowDeleteModal(true)}
                  className="rounded-lg border border-red-200 px-3 py-2 text-[9px] font-medium text-red-500 hover:bg-red-50 dark:border-red-500/20 dark:hover:bg-red-500/5"
                >
                  Delete Account
                </button>
              </div>
            </section>
          </div>
        </main>
      </div>

      {showPasswordModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div
            className={`w-full max-w-md rounded-2xl border shadow-2xl ${
              darkMode
                ? "border-slate-700 bg-[#15211f]"
                : "border-slate-200 bg-white"
            }`}
          >
            <div className="flex items-start justify-between border-b p-5">
              <div>
                <h3
                  className={`text-[16px] font-bold ${
                    darkMode ? "text-white" : "text-emerald-950"
                  }`}
                >
                  Change Password
                </h3>
                <p
                  className={`mt-1 text-[10px] ${
                    darkMode ? "text-slate-500" : "text-slate-500"
                  }`}
                >
                  Password changes are represented as a frontend demo here.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setShowPasswordModal(false)}
                className={`rounded-lg p-1.5 ${
                  darkMode
                    ? "text-slate-400 hover:bg-slate-800"
                    : "text-slate-500 hover:bg-slate-100"
                }`}
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 p-5">
              <Field
                label="Current Password"
                type="password"
                value=""
                onChange={() => {}}
                darkMode={darkMode}
              />
              <Field
                label="New Password"
                type="password"
                value=""
                onChange={() => {}}
                darkMode={darkMode}
              />
              <Field
                label="Confirm Password"
                type="password"
                value=""
                onChange={() => {}}
                darkMode={darkMode}
              />

              <button
                type="button"
                onClick={() => setShowPasswordModal(false)}
                className="mt-2 w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-[10px] font-semibold text-white hover:bg-emerald-600"
              >
                Update Password
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div
            className={`w-full max-w-sm rounded-2xl border shadow-2xl ${
              darkMode
                ? "border-slate-700 bg-[#15211f]"
                : "border-slate-200 bg-white"
            }`}
          >
            <div className="p-5 text-center">
              <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-red-500/10 text-red-500">
                <AlertTriangle size={20} />
              </div>

              <h3
                className={`mt-3 text-[15px] font-bold ${
                  darkMode ? "text-white" : "text-emerald-950"
                }`}
              >
                Delete your account?
              </h3>

              <p
                className={`mt-2 text-[9px] leading-4 ${
                  darkMode ? "text-slate-500" : "text-slate-500"
                }`}
              >
                This is a demonstration confirmation. No real account will be
                deleted by this frontend action.
              </p>

              <div className="mt-5 flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowDeleteModal(false)}
                  className={`flex-1 rounded-lg border px-4 py-2.5 text-[10px] font-medium ${
                    darkMode
                      ? "border-slate-700 text-slate-400 hover:bg-slate-800"
                      : "border-slate-200 text-slate-500 hover:bg-slate-50"
                  }`}
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={() => setShowDeleteModal(false)}
                  className="flex-1 rounded-lg bg-red-500 px-4 py-2.5 text-[10px] font-semibold text-white hover:bg-red-600"
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
