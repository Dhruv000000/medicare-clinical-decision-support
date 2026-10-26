// ==============================================================================
// FILE: frontend/src/pages/public/patient/patient_dashboard.jsx
// PURPOSE: Central patient portal overview screen visualizing vitals, appointments, and telemetry.
// VIVA EXPLANATION: Serves as the primary patient cockpit. Integrates real database metrics from /patient/dashboard/, plots historical blood pressure trends using Recharts, highlights abnormal biomarkers, and surfaces next appointment alerts.
// ==============================================================================

import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bell,
  ChevronDown,
  ClipboardList,
  FileText,
  Heart,
  Home,
  LogIn,
  Pill,
  Search,
  Settings,
  ShieldCheck,
  Thermometer,
  UserRound,
  Droplets,
  TrendingUp,
  Info,
  Moon,
  Sun,
  Sparkles,
  AlertTriangle,
  Stethoscope,
  Brain,
  CircleDot,
} from "lucide-react";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import { useAuth } from "../../../_core/hooks/useAuth";
import patientService from "../../../services/patientService";
import PatientSidebar from "./sidebar";


/* -------------------------------------------------------
   PATIENT PAGE ROUTES
------------------------------------------------------- */

/*
  Keep all patient page paths in one place. These are based on
  the files in your pages/public/patient folder.

  If patient_routes.js uses different path names, change only
  the values below — the sidebar code does not need to change.
*/
const PATIENT_ROUTES = {
  dashboard: "/patient/dashboard",
  healthTrends: "/patient/health-trends",
  appointments: "/patient/appointments",
  medicalRecords: "/patient/medical-records",
  labTests: "/patient/reports-lab-tests",
  medications: "/patient/medications",
  symptomAnalysis: "/patient/symptom-analysis",
  predictions: "/patient/predictions",
  aiAssistant: "/patient/ai-assistant",
  settings: "/patient/settings",
  login: "/login",
};

/*
  Uses normal browser navigation so this dashboard works even
  if the pages are not rendered as children of this component.
  If you already use React Router, these links are still valid
  routes and React Router can intercept them if desired.
*/
const goToPatientPage = (path) => {
  window.location.href = path;
};

const getCurrentPatientPath = () => {
  if (typeof window === "undefined") return PATIENT_ROUTES.dashboard;
  return window.location.pathname;
};


/* -------------------------------------------------------
   SIDEBAR NAVIGATION
------------------------------------------------------- */

// Replace your navSections with this:

const navSections = [
  {
    title: "MAIN",
    items: [
      {
        label: "Dashboard",
        icon: Home,
        route: PATIENT_ROUTES.dashboard,
      },
    ],
  },
  {
    title: "HEALTH",
    items: [
      {
        label: "Health Trends",
        icon: TrendingUp,
        route: PATIENT_ROUTES.healthTrends,
      },
      {
        label: "Appointments",
        icon: Activity,
        route: PATIENT_ROUTES.appointments,
      },
    ],
  },
  {
    title: "MEDICAL",
    items: [
      {
        label: "Medical Records",
        icon: FileText,
        route: PATIENT_ROUTES.medicalRecords,
      },
      {
        label: "Reports & Lab Tests",
        icon: ClipboardList,
        route: PATIENT_ROUTES.labTests,
      },
      {
        label: "Medications",
        icon: Pill,
        route: PATIENT_ROUTES.medications,
      },
    ],
  },
  {
    title: "AI HEALTH",
    items: [
      {
        label: "Symptom Analysis",
        icon: Stethoscope,
        route: PATIENT_ROUTES.symptomAnalysis,
      },
      {
        label: "Predictions",
        icon: Brain,
        route: PATIENT_ROUTES.predictions,
      },
      {
        label: "AI Assistant",
        icon: Sparkles,
        route: PATIENT_ROUTES.aiAssistant,
      },
    ],
  },
];

/* -------------------------------------------------------
   SIDEBAR
------------------------------------------------------- */

function Sidebar({ darkMode, onLogout }) {
  const currentPath = getCurrentPatientPath();

  const colors = {
    sidebar: darkMode ? "bg-[#101918]" : "bg-white",
    border: darkMode ? "border-slate-800" : "border-slate-100",
    text: darkMode ? "text-slate-300" : "text-slate-600",
    heading: darkMode ? "text-slate-500" : "text-slate-500",
    hover: darkMode
      ? "hover:bg-slate-800/60"
      : "hover:bg-slate-50",
    active: "bg-emerald-500/10 text-emerald-500 font-semibold",
  };

  const isActive = (route) => {
    if (route === PATIENT_ROUTES.dashboard) {
      return (
        currentPath === route ||
        currentPath === "/patient" ||
        currentPath === "/patient/"
      );
    }

    return currentPath === route;
  };

  return (
    <aside
      className={`fixed left-0 top-0 z-50 flex h-screen w-[255px] min-w-[255px] max-w-[255px] flex-col overflow-hidden border-r ${colors.border} ${colors.sidebar} px-4 py-5`}
    >
      {/* LOGO */}
      <button
        type="button"
        onClick={() => goToPatientPage(PATIENT_ROUTES.dashboard)}
        className="mb-6 flex shrink-0 items-center gap-4 px-4 text-left"
        aria-label="Go to patient dashboard"
      >
        <div className="flex h-[50px] w-[50px] items-center justify-center rounded-full bg-emerald-500 shadow-sm">
          <Heart
            size={28}
            strokeWidth={2.2}
            className="text-white"
          />
        </div>

        <span
          className={`text-[25px] font-bold tracking-[-0.7px] ${
            darkMode ? "text-white" : "text-emerald-900"
          }`}
        >
          medicare.
        </span>
      </button>

      {/* NAVIGATION */}
      <nav
        className="min-h-0 flex-1 overflow-hidden pr-1"
        aria-label="Patient navigation"
      >
        <div className="space-y-3">
          {navSections.map((section) => (
            <div key={section.title}>
              <p
                className={`mb-1.5 px-4 text-[12px] font-bold tracking-[0.09em] ${colors.heading}`}
              >
                {section.title}
              </p>

              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(item.route);

                  return (
                    <button
                      key={item.label}
                      type="button"
                      onClick={() => goToPatientPage(item.route)}
                      aria-current={active ? "page" : undefined}
                      className={`relative flex h-[40px] w-full items-center gap-4 rounded-lg px-4 text-left text-[15px] transition-all duration-200 ${
                        active
                          ? colors.active
                          : `${colors.text} ${colors.hover}`
                      }`}
                    >
                      {active && (
                        <span className="absolute left-0 top-1/2 h-[27px] w-[4px] -translate-y-1/2 rounded-r-full bg-emerald-500" />
                      )}

                      <Icon
                        size={22}
                        strokeWidth={1.8}
                        className={
                          active
                            ? "text-emerald-500"
                            : darkMode
                              ? "text-slate-400"
                              : "text-slate-500"
                        }
                      />

                      <span className="truncate">
                        {item.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </nav>

      {/* BOTTOM NAV */}
      <div
        className={`mt-3 shrink-0 border-t pt-3 ${
          darkMode ? "border-slate-800" : "border-slate-100"
        }`}
      >
        <button
          type="button"
          onClick={() => goToPatientPage(PATIENT_ROUTES.settings)}
          className={`flex h-[40px] w-full items-center gap-4 rounded-lg px-4 text-[15px] transition ${
            isActive(PATIENT_ROUTES.settings)
              ? colors.active
              : `${colors.text} ${colors.hover}`
          }`}
        >
          <Settings size={22} strokeWidth={1.8} />
          Settings
        </button>

        <button
          type="button"
          onClick={onLogout}
          className={`flex h-[40px] w-full items-center gap-4 rounded-lg px-4 text-[15px] transition ${colors.text} ${colors.hover}`}
        >
          <LogIn size={22} strokeWidth={1.8} />
          Logout
        </button>
      </div>
    </aside>
  );
}

/* -------------------------------------------------------
   HEADER
------------------------------------------------------- */

function Header({ darkMode, setDarkMode }) {
  const { user } = useAuth();
  const displayName =
    user?.full_name ||
    (user?.first_name ? `${user.first_name} ${user.last_name || ""}`.trim() : null) ||
    user?.name ||
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
      {/* TITLE */}
      <h1
        className={`text-[28px] font-bold tracking-[-0.8px] ${
          darkMode ? "text-white" : "text-emerald-950"
        }`}
      >
        Dashboard
      </h1>

      {/* RIGHT SIDE */}
      <div className="flex items-center gap-5">
        {/* SEARCH */}
        <div
          className={`flex h-10 w-[300px] items-center gap-3 rounded-xl border px-4 ${
            darkMode
              ? "border-slate-700 bg-slate-900/40"
              : "border-slate-200 bg-white"
          }`}
        >
          <input
            placeholder="Search anything..."
            className={`w-full bg-transparent text-sm outline-none ${
              darkMode
                ? "text-white placeholder:text-slate-500"
                : "text-slate-700 placeholder:text-slate-400"
            }`}
          />

          <Search
            size={19}
            className="text-slate-500"
          />
        </div>

        {/* THEME TOGGLE */}
        <button
          onClick={() => setDarkMode((value) => !value)}
          className={`flex h-10 w-10 items-center justify-center rounded-xl border transition ${
            darkMode
              ? "border-slate-700 bg-slate-900 text-yellow-300 hover:bg-slate-800"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
          }`}
          title={
            darkMode
              ? "Switch to light mode"
              : "Switch to dark mode"
          }
        >
          {darkMode ? (
            <Sun size={19} />
          ) : (
            <Moon size={19} />
          )}
        </button>

        {/* NOTIFICATIONS */}
        <button
          className={`relative ${
            darkMode
              ? "text-slate-300"
              : "text-slate-700"
          }`}
        >
          <Bell size={22} strokeWidth={1.7} />

          <span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-emerald-500" />
        </button>

        {/* PROFILE */}
        <button className="flex items-center gap-3">
          <div
            className={`flex h-10 w-10 items-center justify-center overflow-hidden rounded-full ${
              darkMode
                ? "bg-emerald-800 text-white"
                : "bg-emerald-100 text-emerald-800 font-bold"
            }`}
          >
            <span className="text-sm font-bold uppercase">{displayName.charAt(0) || "P"}</span>
          </div>

          <span
            className={`text-[14px] font-semibold ${
              darkMode
                ? "text-slate-200"
                : "text-slate-800"
            }`}
          >
            {displayName}
          </span>

          <ChevronDown
            size={16}
            className={
              darkMode
                ? "text-slate-400"
                : "text-slate-600"
            }
          />
        </button>
      </div>
    </header>
  );
}

/* -------------------------------------------------------
   ICON WRAPPER
------------------------------------------------------- */

function MetricIcon({ children, darkMode }) {
  return (
    <div
      className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full ${
        darkMode
          ? "bg-emerald-500/10"
          : "bg-emerald-50"
      }`}
    >
      {children}
    </div>
  );
}

/* -------------------------------------------------------
   METRIC CARD
------------------------------------------------------- */

function MetricCard({
  icon,
  title,
  value,
  unit,
  darkMode,
}) {
  return (
    <div
      className={`relative min-h-[190px] rounded-[18px] border p-5 shadow-[0_3px_15px_rgba(15,23,42,0.025)] ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between">
        <MetricIcon darkMode={darkMode}>
          {icon}
        </MetricIcon>

        <span
          className={`rounded-full px-3 py-1.5 text-[12px] font-medium ${
            darkMode
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-emerald-50 text-emerald-700"
          }`}
        >
          Normal
        </span>
      </div>

      <div className="mt-4">
        <p
          className={`text-[14px] font-medium ${
            darkMode
              ? "text-slate-300"
              : "text-slate-700"
          }`}
        >
          {title}
        </p>

        <div className="mt-2 flex items-baseline gap-2">
          <span
            className={`text-[32px] font-semibold leading-none tracking-[-1px] ${
              darkMode
                ? "text-white"
                : "text-emerald-950"
            }`}
          >
            {value}
          </span>

          <span
            className={`text-[13px] ${
              darkMode
                ? "text-slate-400"
                : "text-slate-600"
            }`}
          >
            {unit}
          </span>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------
   PATIENT CARD
------------------------------------------------------- */

function PatientCard({ darkMode, user, summary }) {
  const patientName =
    user?.full_name ||
    (user?.first_name ? `${user.first_name} ${user.last_name || ""}`.trim() : null) ||
    user?.name ||
    user?.email ||
    "Patient";

  const nextSession = summary?.next_appointment
    ? `${summary.next_appointment.doctor_name}`
    : "No upcoming visits";

  return (
    <div
      className={`min-h-[190px] rounded-[18px] border p-5 shadow-[0_3px_15px_rgba(15,23,42,0.025)] ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between">
        <MetricIcon darkMode={darkMode}>
          <UserRound
            size={25}
            strokeWidth={1.7}
            className="text-emerald-500"
          />
        </MetricIcon>

        <Info
          size={19}
          className={
            darkMode
              ? "text-slate-500"
              : "text-slate-400"
          }
        />
      </div>

      <div className="mt-4">
        <p
          className={`text-[14px] font-medium ${
            darkMode
              ? "text-slate-300"
              : "text-slate-700"
          }`}
        >
          Patient Profile
        </p>

        <h2
          className={`mt-1 text-[21px] font-bold leading-tight truncate ${
            darkMode
              ? "text-white"
              : "text-emerald-950"
          }`}
        >
          {patientName}
        </h2>

        <div
          className={`mt-2 flex items-center gap-2 text-[13px] ${
            darkMode
              ? "text-slate-400"
              : "text-slate-500"
          }`}
        >
          <span className="truncate">{user?.email || "Verified Patient"}</span>
        </div>

        <div
          className={`mt-1.5 flex items-center gap-2 text-[13px] ${
            darkMode
              ? "text-slate-400"
              : "text-slate-500"
          }`}
        >
          <span className="truncate text-emerald-500 font-medium">Next: {nextSession}</span>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------
   BLOOD PRESSURE CHART
------------------------------------------------------- */

function BloodPressureChart({ darkMode, data = [] }) {
  const gridColor = darkMode
    ? "#263936"
    : "#e5e7eb";

  const textColor = darkMode
    ? "#94a3b8"
    : "#64748b";

  return (
    <div
      className={`flex min-h-0 h-full flex-col overflow-hidden rounded-[18px] border p-6 shadow-[0_3px_15px_rgba(15,23,42,0.025)] ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white"
      }`}
    >
      {/* HEADER */}
      <div className="flex shrink-0 items-start justify-between">
        <div className="flex items-start gap-4">
          <TrendingUp
            size={25}
            strokeWidth={1.8}
            className="mt-1 text-emerald-500"
          />

          <div>
            <h3
              className={`text-[17px] font-bold ${
                darkMode
                  ? "text-white"
                  : "text-emerald-950"
              }`}
            >
              Blood Pressure History
            </h3>

            <p
              className={`mt-1 text-[13px] ${
                darkMode
                  ? "text-slate-500"
                  : "text-slate-500"
              }`}
            >
              {data.length > 0 ? "Clinical measurements" : "Measured blood pressure readings"}
            </p>
          </div>
        </div>
      </div>

      {data.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center py-10 text-center">
          <Activity size={32} className="text-slate-400 mb-2 opacity-50" />
          <p className={`text-[14px] font-semibold ${darkMode ? "text-slate-300" : "text-slate-700"}`}>
            No health measurements available yet.
          </p>
          <p className={`mt-1 text-[12px] max-w-xs ${darkMode ? "text-slate-500" : "text-slate-400"}`}>
            Upload diagnostic reports to visualize your blood pressure trends.
          </p>
        </div>
      ) : (
        <>
          {/* LEGEND */}
          <div className="mt-3 flex shrink-0 justify-end gap-6 text-[11px]">
            <div
              className={`flex items-center gap-2 ${
                darkMode
                  ? "text-slate-400"
                  : "text-slate-600"
              }`}
            >
              <span className="h-[3px] w-4 rounded-full bg-emerald-700" />
              Systolic
            </div>

            <div
              className={`flex items-center gap-2 ${
                darkMode
                  ? "text-slate-400"
                  : "text-slate-600"
              }`}
            >
              <span className="h-[3px] w-4 rounded-full bg-emerald-300" />
              Diastolic
            </div>
          </div>

          {/* GRAPH */}
          <div className="mt-1 min-h-0 flex-1">
            <ResponsiveContainer
              width="100%"
              height="100%"
            >
              <LineChart
                data={data}
                margin={{
                  top: 8,
                  right: 0,
                  left: -20,
                  bottom: 0,
                }}
              >
                <CartesianGrid
                  strokeDasharray="2 4"
                  vertical
                  horizontal
                  stroke={gridColor}
                />

                <XAxis
                  dataKey="day"
                  axisLine={false}
                  tickLine={false}
                  tick={{
                    fontSize: 11,
                    fill: textColor,
                  }}
                  dy={8}
                />

                <YAxis
                  domain={[0, 180]}
                  ticks={[
                    0,
                    40,
                    80,
                    120,
                    160,
                  ]}
                  axisLine={false}
                  tickLine={false}
                  tick={{
                    fontSize: 11,
                    fill: textColor,
                  }}
                />

                <Tooltip
                  content={({
                    active,
                    payload,
                    label,
                  }) => {
                    if (
                      !active ||
                      !payload?.length
                    ) {
                      return null;
                    }

                    return (
                      <div
                        className={`rounded-xl border px-4 py-3 shadow-lg ${
                          darkMode
                            ? "border-slate-700 bg-[#101918] text-slate-200"
                            : "border-slate-200 bg-white text-slate-700"
                        }`}
                      >
                        <p className="mb-2 text-[12px] font-semibold">
                          {label}
                        </p>

                        <div className="space-y-1 text-[11px]">
                          <p>
                            <span className="mr-2 text-emerald-700">
                              ●
                            </span>
                            Systolic
                            <strong className="ml-5">
                              {payload[0]?.value} mmHg
                            </strong>
                          </p>

                          {payload[1] && (
                            <p>
                              <span className="mr-2 text-emerald-300">
                                ●
                              </span>
                              Diastolic
                              <strong className="ml-5">
                                {payload[1]?.value} mmHg
                              </strong>
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  }}
                />

                <Line
                  type="monotone"
                  dataKey="systolic"
                  stroke="#087f63"
                  strokeWidth={2.5}
                  dot={{
                    r: 3,
                    fill: darkMode
                      ? "#15211f"
                      : "#fff",
                    stroke: "#087f63",
                    strokeWidth: 2,
                  }}
                />

                <Line
                  type="monotone"
                  dataKey="diastolic"
                  stroke="#69ceb0"
                  strokeWidth={2}
                  dot={{
                    r: 3,
                    fill: darkMode
                      ? "#15211f"
                      : "#fff",
                    stroke: "#69ceb0",
                    strokeWidth: 2,
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

/* -------------------------------------------------------
   HEALTH SUMMARY
------------------------------------------------------- */

function HealthSummary({ darkMode, metrics = [] }) {
  const hasAbnormal = metrics.some((m) => m.flag && m.flag.toLowerCase() !== "normal");
  const overallLabel = metrics.length === 0 ? "PENDING" : hasAbnormal ? "ATTENTION" : "STABLE";
  const overallColor = metrics.length === 0 ? "text-slate-400" : hasAbnormal ? "text-amber-500" : "text-emerald-500";

  return (
    <div
      className={`flex h-full min-h-0 flex-col rounded-[18px] border p-6 shadow-[0_3px_15px_rgba(15,23,42,0.025)] ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white"
      }`}
    >
      {/* HEADER */}
      <div className="flex shrink-0 items-center gap-4">
        <MetricIcon darkMode={darkMode}>
          <ShieldCheck
            size={25}
            strokeWidth={1.7}
            className="text-emerald-500"
          />
        </MetricIcon>

        <h3
          className={`text-[17px] font-bold ${
            darkMode
              ? "text-white"
              : "text-emerald-950"
          }`}
        >
          Health Summary
        </h3>
      </div>

      {/* OVERALL */}
      <div
        className={`mt-5 flex shrink-0 items-center justify-between border-b pb-5 ${
          darkMode
            ? "border-slate-800"
            : "border-slate-100"
        }`}
      >
        <div>
          <p
            className={`text-[13px] ${
              darkMode
                ? "text-slate-400"
                : "text-slate-600"
            }`}
          >
            Overall Status
          </p>

          <p className={`mt-1 text-[30px] font-bold leading-none tracking-[-1px] ${overallColor}`}>
            {overallLabel}
          </p>
        </div>

        <div
          className={`flex h-[60px] w-[60px] shrink-0 items-center justify-center rounded-full ${
            darkMode
              ? "bg-emerald-500/10"
              : "bg-emerald-50"
          }`}
        >
          <Heart
            size={30}
            fill="currentColor"
            className={overallColor}
          />
        </div>
      </div>

      {/* STATUS */}
      <div className="flex-1 overflow-y-auto mt-2">
        {metrics.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No health measurements available yet.
          </div>
        ) : (
          metrics.map((row, idx) => (
            <div
              key={idx}
              className={`flex items-center justify-between border-b py-3 last:border-b-0 ${
                darkMode
                  ? "border-slate-800"
                  : "border-slate-100"
              }`}
            >
              <div
                className={`flex items-center gap-3 ${
                  darkMode
                    ? "text-slate-300"
                    : "text-slate-700"
                }`}
              >
                <Activity size={17} className="text-emerald-500 shrink-0" />
                <div>
                  <span className="text-[13px] font-medium block">{row.test_name}</span>
                  {row.value && (
                    <span className="text-[11px] text-slate-400">
                      {row.value} {row.unit || ""}
                    </span>
                  )}
                </div>
              </div>

              <div className={`flex items-center gap-1.5 text-[12px] font-medium ${
                (row.flag || "").toLowerCase() === "high" || (row.flag || "").toLowerCase() === "critical"
                  ? "text-red-400"
                  : (row.flag || "").toLowerCase() === "low"
                  ? "text-amber-400"
                  : "text-emerald-500"
              }`}>
                <span className={`h-2 w-2 rounded-full ${
                  (row.flag || "").toLowerCase() === "high" || (row.flag || "").toLowerCase() === "critical"
                    ? "bg-red-400"
                    : (row.flag || "").toLowerCase() === "low"
                    ? "bg-amber-400"
                    : "bg-emerald-400"
                }`} />
                {row.flag ? row.flag.toUpperCase() : "RECORDED"}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// --- PatientDashboard ---
// What it does: Master patient dashboard component fetching telemetry, extracting blood pressure trends, and rendering clinical metric cards.
// Why it's structured this way: Concurrently requests dashboard metrics and lab reports to populate health cards and interactive charts.
// Parameters & Returns: Props (none) -> Rendered patient portal dashboard JSX.
// ------------------------------------------------------------------------------
export default function PatientDashboard() {
  const { user, logout } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [bpMeasurements, setBpMeasurements] = useState([]);
  const [recentMetrics, setRecentMetrics] = useState([]);

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        setLoadingSummary(true);
        const [dashData, labData] = await Promise.all([
          patientService.getDashboardSummary().catch(() => null),
          patientService.getLabReports().catch(() => []),
        ]);
        if (!isMounted) return;

        if (dashData) setSummary(dashData);

        const reportsList = Array.isArray(labData) ? labData : labData?.results || [];
        const extractedBp = [];
        const extractedMetrics = [];

        reportsList.forEach((report) => {
          const results = report.results || [];
          results.forEach((res) => {
            extractedMetrics.push(res);
            const name = (res.test_name || "").toLowerCase();
            if (name.includes("blood pressure") || name.includes("bp")) {
              const parts = String(res.value).split("/");
              if (parts.length === 2) {
                const sys = parseInt(parts[0], 10);
                const dia = parseInt(parts[1], 10);
                if (!isNaN(sys) && !isNaN(dia)) {
                  const d = report.uploaded_at ? new Date(report.uploaded_at) : new Date();
                  extractedBp.push({
                    day: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
                    systolic: sys,
                    diastolic: dia,
                  });
                }
              }
            }
          });
        });

        setBpMeasurements(extractedBp);
        setRecentMetrics(extractedMetrics.slice(0, 4));
      } catch (err) {
        console.warn("Could not load dashboard summary:", err);
      } finally {
        if (isMounted) setLoadingSummary(false);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, []);


  const firstName =
    user?.first_name ||
    (user?.full_name ? user.full_name.split(" ")[0] : null) ||
    user?.name ||
    "Patient";

  /* -------------------------
     DARK MODE
  ------------------------- */

  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window === "undefined") return false;

    const savedTheme = window.localStorage.getItem(
      "medicare-theme"
    );

    if (savedTheme === "dark") return true;
    if (savedTheme === "light") return false;

    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false;
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    window.localStorage.setItem(
      "medicare-theme",
      darkMode ? "dark" : "light"
    );

    // Keep the global document theme in sync so Tailwind `dark:`
    // classes used by the other patient pages work consistently.
    document.documentElement.classList.toggle("dark", darkMode);
    document.documentElement.style.colorScheme = darkMode
      ? "dark"
      : "light";
    document.body.style.backgroundColor = darkMode
      ? "#0b1413"
      : "#f8faf9";
  }, [darkMode]);

  const [showLogoutConfirmation, setShowLogoutConfirmation] =
    useState(false);

  /* -------------------------
     THEME CLASSES
  ------------------------- */

  const pageClasses = useMemo(
    () =>
      darkMode
        ? "bg-[#0b1413] text-white"
        : "bg-[#f8faf9] text-slate-900",
    [darkMode]
  );

  return (
    <div
      data-theme={darkMode ? "dark" : "light"}
      className={`min-h-screen w-full ${pageClasses}`}
    >
      {/* SIDEBAR — fixed universal width: 255px */}
      <PatientSidebar
        darkMode={darkMode}
        onLogout={() => setShowLogoutConfirmation(true)}
      />

      {/* MAIN — always starts after the 255px sidebar */}
      <main className="ml-[255px] flex min-h-screen min-w-0 flex-col overflow-hidden">
          {/* HEADER */}
          <Header
            darkMode={darkMode}
            setDarkMode={setDarkMode}
          />

          {/* CONTENT */}
          <div className="flex min-h-0 flex-1 flex-col px-8 py-5">
            {/* WELCOME */}
            <div className="mb-4 shrink-0">
              <h2
                className={`text-[24px] font-bold tracking-[-0.5px] ${
                  darkMode
                    ? "text-white"
                    : "text-emerald-950"
                }`}
              >
                Welcome back, {firstName}!
              </h2>

              <p
                className={`mt-1 text-[14px] ${
                  darkMode
                    ? "text-slate-500"
                    : "text-slate-500"
                }`}
              >
                Here’s your health overview.
              </p>
            </div>

            {/* TOP CARDS */}
            <div className="grid shrink-0 grid-cols-4 gap-4">
              <PatientCard darkMode={darkMode} user={user} summary={summary} />

              <MetricCard
                darkMode={darkMode}
                icon={
                  <Activity
                    size={27}
                    strokeWidth={1.7}
                    className="text-emerald-500"
                  />
                }
                title="Upcoming Appointments"
                value={loadingSummary ? "…" : (summary?.upcoming_appointments_count ?? 0)}
                unit={summary?.upcoming_appointments_count === 1 ? "Session" : "Sessions"}
              />

              <MetricCard
                darkMode={darkMode}
                icon={
                  <Pill
                    size={27}
                    strokeWidth={1.7}
                    className="text-emerald-500"
                  />
                }
                title="Active Prescriptions"
                value={loadingSummary ? "…" : (summary?.active_medications_count ?? 0)}
                unit="Medications"
              />

              <MetricCard
                darkMode={darkMode}
                icon={
                  <FileText
                    size={27}
                    strokeWidth={1.7}
                    className="text-emerald-500"
                  />
                }
                title="Lab Reports & Records"
                value={loadingSummary ? "…" : ((summary?.medical_records_count ?? 0) + (summary?.lab_reports_count ?? 0))}
                unit="Reports"
              />
            </div>

            {/* LOWER CONTENT */}
            <div className="mt-4 grid min-h-0 flex-1 grid-cols-[1.7fr_1fr] gap-4">
              <BloodPressureChart
                darkMode={darkMode}
                data={bpMeasurements}
              />

              <HealthSummary
                darkMode={darkMode}
                metrics={recentMetrics}
              />
            </div>
        </div>
      </main>

      {/* LOGOUT CONFIRMATION */}
      {showLogoutConfirmation && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-[2px]"
          role="dialog"
          aria-modal="true"
          aria-labelledby="logout-title"
        >
          <div
            className={`w-full max-w-[430px] rounded-2xl border p-7 shadow-2xl ${
              darkMode
                ? "border-slate-700 bg-[#101918] text-white"
                : "border-slate-200 bg-white text-slate-900"
            }`}
          >
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10">
              <LogIn
                size={30}
                strokeWidth={1.8}
                className="text-emerald-500"
              />
            </div>

            <div className="mt-5 text-center">
              <h2
                id="logout-title"
                className={`text-xl font-bold ${
                  darkMode ? "text-white" : "text-slate-900"
                }`}
              >
                Sign out?
              </h2>

              <p
                className={`mt-2 text-sm ${
                  darkMode ? "text-slate-400" : "text-slate-500"
                }`}
              >
                Are you sure you want to sign out of Medicare?
              </p>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setShowLogoutConfirmation(false)}
                className={`rounded-xl border px-4 py-3 text-sm font-semibold transition ${
                  darkMode
                    ? "border-slate-700 bg-slate-900/50 text-slate-300 hover:bg-slate-800"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={async () => {
                  await logout();
                  goToPatientPage(PATIENT_ROUTES.login);
                }}
                className="rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

