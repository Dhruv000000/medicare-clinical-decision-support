import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useTheme } from "../ThemeContext";

import {
  Activity,
  AlertTriangle,
  Brain,
  ClipboardList,
  CircleDot,
  FileText,
  Heart,
  Home,
  LogIn,
  Pill,
  Settings,
  Sparkles,
  Stethoscope,
  TrendingUp,
} from "lucide-react";

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
    items: [
      {
        label: "Dashboard",
        icon: Home,
        route: ROUTES.dashboard,
      },
    ],
  },
  {
    title: "HEALTH",
    items: [
      {
        label: "Health Trends",
        icon: TrendingUp,
        route: ROUTES.healthTrends,
      },
      {
        label: "Appointments",
        icon: Activity,
        route: ROUTES.appointments,
      },
    ],
  },
  {
    title: "MEDICAL",
    items: [
      {
        label: "Medical Records",
        icon: FileText,
        route: ROUTES.medicalRecords,
      },
      {
        label: "Reports & Lab Tests",
        icon: ClipboardList,
        route: ROUTES.labTests,
      },
      {
        label: "Medications",
        icon: Pill,
        route: ROUTES.medications,
      },
    ],
  },
  {
    title: "AI HEALTH",
    items: [
      {
        label: "Symptom Analysis",
        icon: Stethoscope,
        route: ROUTES.symptomAnalysis,
      },
      {
        label: "Predictions",
        icon: Brain,
        route: ROUTES.predictions,
      },
      {
        label: "AI Assistant",
        icon: Sparkles,
        route: ROUTES.aiAssistant,
      },
    ],
  },
  {
    title: "MEDICINES",
    items: [
      {
        label: "Medicine Search",
        icon: CircleDot,
        route: ROUTES.medicineSearch,
      },
      {
        label: "Drug Interactions",
        icon: AlertTriangle,
        route: ROUTES.drugInteractions,
      },
    ],
  },
];

function isActivePath(pathname, route) {
  return (
    pathname.replace(/\/$/, "") ===
    route.replace(/\/$/, "")
  );
}

export default function Sidebar({ darkMode: propDarkMode, onLogout }) {
  const location = useLocation();
  const themeContext = useTheme();
  const darkMode = propDarkMode !== undefined ? propDarkMode : (themeContext?.isDark ?? true);

  return (
    <aside
      className={`fixed left-0 top-0 z-50 flex h-screen w-[255px] min-w-[255px] max-w-[255px] flex-col overflow-hidden border-r ${
        darkMode
          ? "border-slate-800 bg-[#0d1817]"
          : "border-slate-200 bg-white"
      }`}
    >
      {/* =========================
          LOGO
      ========================== */}

      <div className="shrink-0 px-7 pt-4 pb-4">
        <Link
          to={ROUTES.dashboard}
          className="flex items-center gap-4"
        >
          <div className="flex h-[50px] w-[50px] shrink-0 items-center justify-center rounded-full bg-emerald-500">
            <Heart
              size={28}
              strokeWidth={2.2}
              className="text-white"
            />
          </div>

          <span
            className={`text-[25px] font-bold tracking-[-0.7px] ${
              darkMode
                ? "text-white"
                : "text-slate-900"
            }`}
          >
            medicare.
          </span>
        </Link>
      </div>

      {/* =========================
          NAVIGATION
      ========================== */}

      <nav className="min-h-0 flex-1 overflow-hidden px-3">
        <div className="space-y-1">
          {navSections.map((section) => (
            <div key={section.title}>
              <div
                className={`px-4 pb-0.5 pt-1 text-[12px] font-bold tracking-[0.09em] ${
                  darkMode
                    ? "text-slate-200"
                    : "text-slate-700"
                }`}
              >
                {section.title}
              </div>

              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActivePath(
                    location.pathname,
                    item.route
                  );

                  return (
                    <Link
                      key={item.label}
                      to={item.route}
                      className={`relative flex h-[36px] w-full items-center gap-4 rounded-lg px-4 text-[15px] transition-all duration-150 ${
                        active
                          ? darkMode
                            ? "bg-[#0b3027] font-semibold text-white"
                            : "bg-emerald-50 font-semibold text-emerald-700"
                          : darkMode
                            ? "text-white hover:bg-white/[0.04]"
                            : "text-slate-700 hover:bg-slate-50"
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
                            ? "text-white"
                            : darkMode
                              ? "text-white"
                              : "text-slate-600"
                        }
                      />

                      <span className="truncate">
                        {item.label}
                      </span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </nav>

      {/* =========================
          BOTTOM MENU
      ========================== */}

      <div
        className={`shrink-0 border-t px-3 py-3 ${
          darkMode
            ? "border-slate-800"
            : "border-slate-200"
        }`}
      >
        {/* Settings */}

        <Link
          to={ROUTES.settings}
          className={`flex h-[36px] w-full items-center gap-4 rounded-lg px-4 text-[15px] transition ${
            isActivePath(
              location.pathname,
              ROUTES.settings
            )
              ? darkMode
                ? "bg-[#0b3027] font-semibold text-white"
                : "bg-emerald-50 font-semibold text-emerald-700"
              : darkMode
                ? "text-white hover:bg-white/[0.04]"
                : "text-slate-700 hover:bg-slate-50"
          }`}
        >
          <Settings
            size={22}
            strokeWidth={1.8}
          />

          <span>Settings</span>
        </Link>

        {/* Logout */}

        {onLogout ? (
          <button
            type="button"
            onClick={onLogout}
            className={`mt-2 flex h-[36px] w-full items-center gap-4 rounded-lg px-4 text-left text-[15px] transition ${
              darkMode
                ? "text-white hover:bg-white/[0.04]"
                : "text-slate-700 hover:bg-slate-50"
            }`}
          >
            <LogIn
              size={22}
              strokeWidth={1.8}
            />

            <span>Logout</span>
          </button>
        ) : (
          <Link
            to="/login"
          className={`mt-1 flex h-[36px] w-full items-center gap-4 rounded-lg px-4 text-[15px] transition ${
            darkMode
              ? "text-white hover:bg-white/[0.04]"
              : "text-slate-700 hover:bg-slate-50"
          }`}
        >
          <LogIn
            size={22}
            strokeWidth={1.8}
          />

          <span>Logout</span>
          </Link>
        )}
      </div>
    </aside>
  );
}