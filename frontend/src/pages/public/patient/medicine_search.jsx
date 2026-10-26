// ==============================================================================
// FILE: frontend/src/pages/public/patient/medicine_search.jsx
// PURPOSE: Drug compendium search engine integrating patient prescriptions and OpenFDA public registries.
// VIVA EXPLANATION: Implements the pharmaceutical search catalog. Allows patients to search through their personal active prescriptions as well as query the US OpenFDA database for drug indications, common dosages, contraindications, and adverse reaction statistics.
// ==============================================================================

import React, { useEffect, useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Bell,
  Brain,
  CheckCircle2,
  ChevronDown,
  CircleDot,
  ClipboardList,
  FileText,
  Heart,
  Home,
  Info,
  LogIn,
  Moon,
  Pill,
  Search,
  Settings,
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

const popularSearches = [
  "Metformin",
  "Atorvastatin",
  "Amoxicillin",
  "Lisinopril",
  "Ibuprofen",
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
    heading: "text-slate-500",
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
              <p
                className={`mb-1.5 px-3 text-[10px] font-semibold tracking-[0.12em] ${colors.heading}`}
              >
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
                      className={`relative flex w-full items-center gap-3 rounded-lg px-3 py-[8px] text-left text-[13px] transition-all duration-200 ${
                        active
                          ? colors.active
                          : `${colors.text} ${colors.hover}`
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
          <Settings size={18} strokeWidth={1.8} />
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
          Medicine Search
        </h1>

        <p
          className={`mt-1 text-[12px] ${
            darkMode ? "text-slate-500" : "text-slate-500"
          }`}
        >
          Search medicine information and common uses
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
            placeholder="Search anything..."
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

function MedicineCard({ medicine, darkMode, onView }) {
  return (
    <div
      className={`rounded-[13px] border p-4 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <div
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
              darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
            }`}
          >
            <Pill size={18} className="text-emerald-500" />
          </div>

          <div className="min-w-0">
            <h3
              className={`truncate text-[12px] font-bold ${
                darkMode ? "text-white" : "text-emerald-950"
              }`}
            >
              {medicine.name}
            </h3>

            <p
              className={`mt-1 truncate text-[8px] ${
                darkMode ? "text-slate-600" : "text-slate-400"
              }`}
            >
              {medicine.generic}
            </p>
          </div>
        </div>

        <span
          className={`rounded-full px-2 py-1 text-[8px] font-medium ${
            medicine.prescription === "OTC"
              ? darkMode
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-emerald-50 text-emerald-700"
              : darkMode
                ? "bg-blue-500/10 text-blue-400"
                : "bg-blue-50 text-blue-700"
          }`}
        >
          {medicine.prescription}
        </span>
      </div>

      <p
        className={`mt-3 text-[9px] leading-4 ${
          darkMode ? "text-slate-400" : "text-slate-500"
        }`}
      >
        {medicine.description}
      </p>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {medicine.commonUses.slice(0, 3).map((use) => (
          <span
            key={use}
            className={`rounded-full px-2 py-1 text-[8px] ${
              darkMode
                ? "bg-slate-800 text-slate-400"
                : "bg-slate-100 text-slate-500"
            }`}
          >
            {use}
          </span>
        ))}
      </div>

      <div
        className={`mt-3 grid grid-cols-2 gap-3 border-t pt-3 ${
          darkMode ? "border-slate-800" : "border-slate-100"
        }`}
      >
        <div>
          <p className="text-[8px] text-slate-500">DOSAGE</p>
          <p
            className={`mt-1 text-[9px] font-medium ${
              darkMode ? "text-slate-200" : "text-slate-700"
            }`}
          >
            {medicine.dosage}
          </p>
        </div>

        <div>
          <p className="text-[8px] text-slate-500">FORM</p>
          <p
            className={`mt-1 text-[9px] font-medium ${
              darkMode ? "text-slate-200" : "text-slate-700"
            }`}
          >
            {medicine.form}
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={() => onView(medicine)}
        className="mt-3 w-full rounded-lg border border-emerald-500/20 bg-emerald-500/5 px-3 py-2 text-[9px] font-medium text-emerald-500 hover:bg-emerald-500/10"
      >
        View Medicine Details
      </button>
    </div>
  );
}

function DetailsModal({ medicine, darkMode, onClose }) {
  if (!medicine) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div
        className={`w-full max-w-lg rounded-2xl border shadow-2xl ${
          darkMode
            ? "border-slate-700 bg-[#15211f]"
            : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-start justify-between border-b p-5">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
              }`}
            >
              <Pill size={18} className="text-emerald-500" />
            </div>

            <div>
              <h3
                className={`text-[16px] font-bold ${
                  darkMode ? "text-white" : "text-emerald-950"
                }`}
              >
                {medicine.name}
              </h3>

              <p
                className={`mt-1 text-[9px] ${
                  darkMode ? "text-slate-500" : "text-slate-500"
                }`}
              >
                {medicine.generic}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className={`rounded-lg p-1.5 ${
              darkMode
                ? "text-slate-400 hover:bg-slate-800"
                : "text-slate-500 hover:bg-slate-100"
            }`}
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-5">
          <div className="grid grid-cols-3 gap-3">
            {[
              ["Category", medicine.category],
              ["Dosage", medicine.dosage],
              ["Form", medicine.form],
            ].map(([label, value]) => (
              <div
                key={label}
                className={`rounded-xl border p-3 ${
                  darkMode
                    ? "border-slate-800 bg-[#101918]"
                    : "border-slate-100 bg-slate-50"
                }`}
              >
                <p className="text-[8px] text-slate-500">{label}</p>
                <p
                  className={`mt-1 text-[10px] font-medium ${
                    darkMode ? "text-slate-200" : "text-slate-700"
                  }`}
                >
                  {value}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-4">
            <p
              className={`text-[10px] font-semibold ${
                darkMode ? "text-slate-300" : "text-slate-700"
              }`}
            >
              Common uses
            </p>

            <div className="mt-2 flex flex-wrap gap-2">
              {medicine.commonUses.map((use) => (
                <span
                  key={use}
                  className={`rounded-full px-2.5 py-1.5 text-[8px] ${
                    darkMode
                      ? "bg-slate-800 text-slate-300"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {use}
                </span>
              ))}
            </div>
          </div>

          <div
            className={`mt-4 rounded-xl border p-3 ${
              darkMode
                ? "border-slate-800 bg-[#101918]"
                : "border-slate-100 bg-slate-50"
            }`}
          >
            <p className="text-[8px] uppercase tracking-[0.08em] text-slate-500">
              Description
            </p>

            <p
              className={`mt-2 text-[9px] leading-4 ${
                darkMode ? "text-slate-400" : "text-slate-600"
              }`}
            >
              {medicine.description}
            </p>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <div
              className={`rounded-xl border p-3 ${
                darkMode
                  ? "border-slate-800 bg-[#101918]"
                  : "border-slate-100 bg-slate-50"
              }`}
            >
              <p className="text-[8px] uppercase tracking-[0.08em] text-slate-500">
                Interactions
              </p>

              <div className="mt-2 space-y-1.5">
                {medicine.interactions.map((interaction) => (
                  <div
                    key={interaction}
                    className="flex items-center gap-1.5 text-[8px] text-amber-500"
                  >
                    <AlertTriangle size={10} />
                    {interaction}
                  </div>
                ))}
              </div>
            </div>

            <div
              className={`rounded-xl border p-3 ${
                darkMode
                  ? "border-slate-800 bg-[#101918]"
                  : "border-slate-100 bg-slate-50"
              }`}
            >
              <p className="text-[8px] uppercase tracking-[0.08em] text-slate-500">
                Precaution
              </p>

              <p
                className={`mt-2 text-[8px] leading-4 ${
                  darkMode ? "text-slate-400" : "text-slate-500"
                }`}
              >
                {medicine.precautions}
              </p>
            </div>
          </div>

          {medicine.adverseReactions && medicine.adverseReactions.length > 0 && (
            <div
              className={`mt-4 rounded-xl border p-3 ${
                darkMode
                  ? "border-slate-800 bg-[#101918]"
                  : "border-slate-100 bg-slate-50"
              }`}
            >
              <p className="text-[8px] uppercase tracking-[0.08em] text-slate-500">
                OpenFDA Reported Adverse Reactions
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {medicine.adverseReactions.map((ar, idx) => (
                  <span
                    key={idx}
                    className={`rounded-md px-2 py-0.5 text-[8px] ${
                      darkMode
                        ? "bg-red-500/10 text-red-400 border border-red-500/20"
                        : "bg-red-50 text-red-700 border border-red-200"
                    }`}
                  >
                    {ar.reaction || ar}{" "}
                    {ar.reported_cases ? `(${Number(ar.reported_cases).toLocaleString()} cases)` : ""}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div
            className={`mt-4 flex items-start gap-2 rounded-xl border p-3 ${
              darkMode
                ? "border-amber-500/20 bg-amber-500/5"
                : "border-amber-100 bg-amber-50/60"
            }`}
          >
            <Info
              size={13}
              className="mt-0.5 shrink-0 text-amber-500"
            />

            <p
              className={`text-[8px] leading-4 ${
                darkMode ? "text-slate-500" : "text-slate-600"
              }`}
            >
              This information is for educational and clinical decision support use. Confirm medicine use
              with a qualified healthcare professional.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="mt-4 w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-[10px] font-semibold text-white hover:bg-emerald-600"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

// --- MedicineSearch ---
// What it does: Primary drug lookup component coordinating search queries across patient prescriptions and FDA drug registries.
// Why it's structured this way: Normalizes disparate prescription and OpenFDA data structures into a unified card interface.
// Parameters & Returns: Props (none) -> Rendered medicine search view JSX.
// ------------------------------------------------------------------------------
export default function MedicineSearch() {
  const [darkMode, setDarkMode] = useDarkMode();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [selectedMedicine, setSelectedMedicine] = useState(null);
  const [patientMeds, setPatientMeds] = useState([]);
  const [openFdaResults, setOpenFdaResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchingFda, setSearchingFda] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadMeds() {
      try {
        setLoading(true);
        const data = await patientService.getMedications();
        if (!isMounted) return;
        const list = Array.isArray(data) ? data : data?.results || [];
        const formatted = list.map((med) => ({
          id: med.id,
          name: med.name,
          generic: med.prescribed_by_name ? `Prescribed by ${med.prescribed_by_name}` : "Patient Prescription",
          prescription: med.is_active ? "Active" : "Completed",
          category: "My Prescriptions",
          description: med.notes || `Dosage: ${med.dosage || "As advised"}, Frequency: ${med.frequency || "Daily"}`,
          commonUses: [med.frequency, med.is_active ? "Active Regimen" : "Past"].filter(Boolean),
          dosage: med.dosage || "Prescription",
          form: med.frequency || "Oral",
          interactions: ["Check with prescriber before combining with new medications"],
          precautions: med.notes || "Take as directed by doctor.",
          adverseReactions: [],
        }));
        setPatientMeds(formatted);
      } catch (err) {
        console.error("Failed to load patient medications:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadMeds();
    return () => {
      isMounted = false;
    };
  }, []);

  const searchOpenFda = async (searchTerm) => {
    const term = (searchTerm !== undefined ? searchTerm : query).trim();
    if (!term) {
      setOpenFdaResults([]);
      return;
    }
    try {
      setSearchingFda(true);
      const res = await patientService.getDrugReactions(term, 8);
      if (res && (res.adverse_reactions?.length > 0 || res.boxed_warnings?.length > 0 || res.drug)) {
        const drugName = res.drug || term;
        const fdaItem = {
          id: `fda-${drugName}`,
          name: drugName.charAt(0).toUpperCase() + drugName.slice(1),
          generic: "OpenFDA Reference Registry",
          prescription: res.has_boxed_warning ? "Boxed Warning" : "FDA Monitored",
          category: "OpenFDA Clinical Data",
          description:
            res.boxed_warnings?.[0] ||
            `FDA adverse event report data for ${drugName}. Total reported cases: ${res.total_reactions || res.adverse_reactions?.length || 0}.`,
          commonUses: ["Clinical Safety", "FDA Monitored"],
          dosage: "Per prescription label",
          form: "Prescription / OTC",
          interactions: res.boxed_warnings?.length
            ? res.boxed_warnings.slice(0, 3)
            : ["Verify potential interactions with existing prescriptions"],
          precautions: res.precautions?.length
            ? res.precautions.join(". ")
            : "Review FDA prescribing information before use.",
          adverseReactions: res.adverse_reactions || [],
        };
        setOpenFdaResults([fdaItem]);
      } else {
        setOpenFdaResults([]);
      }
    } catch (err) {
      console.warn("OpenFDA search returned no results or error:", err);
      setOpenFdaResults([]);
    } finally {
      setSearchingFda(false);
    }
  };

  const allMedicines = useMemo(() => {
    return [...patientMeds, ...openFdaResults];
  }, [patientMeds, openFdaResults]);

  const categories = useMemo(() => {
    return ["All", ...new Set(allMedicines.map((item) => item.category))];
  }, [allMedicines]);

  const filteredMedicines = useMemo(() => {
    const normalized = query.trim().toLowerCase();

    return allMedicines.filter((medicine) => {
      const categoryMatch =
        category === "All" || medicine.category === category;

      const searchMatch =
        !normalized ||
        medicine.name.toLowerCase().includes(normalized) ||
        medicine.generic.toLowerCase().includes(normalized) ||
        medicine.category.toLowerCase().includes(normalized) ||
        medicine.commonUses.some((use) =>
          use.toLowerCase().includes(normalized)
        );

      return categoryMatch && searchMatch;
    });
  }, [allMedicines, query, category]);

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
          <Header
            darkMode={darkMode}
            setDarkMode={setDarkMode}
          />

          <div className="min-h-0 flex-1 overflow-y-auto px-8 py-5">
            <div>
              <h2
                className={`text-[19px] font-bold ${
                  darkMode ? "text-white" : "text-emerald-950"
                }`}
              >
                Medicine Search
              </h2>

              <p
                className={`mt-1 text-[11px] ${
                  darkMode ? "text-slate-500" : "text-slate-500"
                }`}
              >
                Search your active prescriptions and query OpenFDA drug safety profiles
              </p>
            </div>

            <div
              className={`mt-4 rounded-[14px] border p-4 ${
                darkMode
                  ? "border-slate-800 bg-[#15211f]"
                  : "border-slate-200 bg-white"
              }`}
            >
              <div className="flex items-center gap-2">
                <Search size={17} className="text-emerald-500" />

                <h3
                  className={`text-[12px] font-bold ${
                    darkMode ? "text-white" : "text-emerald-950"
                  }`}
                >
                  Find a Medicine
                </h3>
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  searchOpenFda();
                }}
                className="mt-3 flex gap-3"
              >
                <div
                  className={`flex h-11 min-w-0 flex-1 items-center gap-3 rounded-xl border px-4 ${
                    darkMode
                      ? "border-slate-700 bg-[#101918]"
                      : "border-slate-200 bg-slate-50"
                  }`}
                >
                  <Search size={16} className="text-slate-500" />

                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search by medicine name, generic name, category or use..."
                    className={`w-full bg-transparent text-[10px] outline-none ${
                      darkMode
                        ? "text-white placeholder:text-slate-600"
                        : "text-slate-700 placeholder:text-slate-400"
                    }`}
                  />

                  {query && (
                    <button
                      type="button"
                      onClick={() => {
                        setQuery("");
                        setOpenFdaResults([]);
                      }}
                      className="text-slate-500 hover:text-slate-300"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={searchingFda}
                  className="h-11 rounded-xl bg-emerald-500 px-4 text-[11px] font-medium text-white transition hover:bg-emerald-600 disabled:opacity-50"
                >
                  {searchingFda ? "Searching..." : "Search"}
                </button>

                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className={`h-11 w-[170px] rounded-xl border px-3 text-[10px] outline-none ${
                    darkMode
                      ? "border-slate-700 bg-[#101918] text-slate-300"
                      : "border-slate-200 bg-white text-slate-700"
                  }`}
                >
                  {categories.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </form>

              <div className="mt-3">
                <p className="text-[8px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                  Popular searches (OpenFDA Registry)
                </p>

                <div className="mt-2 flex flex-wrap gap-2">
                  {popularSearches.map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => {
                        setQuery(item);
                        setCategory("All");
                        searchOpenFda(item);
                      }}
                      className={`rounded-full px-2.5 py-1.5 text-[8px] transition ${
                        darkMode
                          ? "bg-slate-800 text-slate-400 hover:text-slate-200"
                          : "bg-slate-100 text-slate-500 hover:text-slate-700"
                      }`}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-3 flex items-center justify-between">
              <div>
                <h3
                  className={`text-[13px] font-bold ${
                    darkMode ? "text-white" : "text-emerald-950"
                  }`}
                >
                  Medicines
                </h3>

                <p
                  className={`mt-1 text-[9px] ${
                    darkMode ? "text-slate-500" : "text-slate-500"
                  }`}
                >
                  {filteredMedicines.length} result
                  {filteredMedicines.length === 1 ? "" : "s"}
                </p>
              </div>

              <div
                className={`flex items-center gap-1 text-[8px] ${
                  darkMode ? "text-slate-500" : "text-slate-500"
                }`}
              >
                <ShieldCheck size={11} className="text-emerald-500" />
                Live OpenFDA & Clinical Registry
              </div>
            </div>

            {loading ? (
              <section
                className={`mt-3 flex min-h-[220px] flex-col items-center justify-center rounded-[14px] border text-center ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
                <p className={`mt-2 text-[11px] ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
                  Loading medications...
                </p>
              </section>
            ) : filteredMedicines.length === 0 ? (
              <section
                className={`mt-3 flex min-h-[300px] flex-col items-center justify-center rounded-[14px] border text-center ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-full ${
                    darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
                  }`}
                >
                  <Search size={20} className="text-emerald-500" />
                </div>

                <p
                  className={`mt-3 text-[12px] font-semibold ${
                    darkMode ? "text-slate-200" : "text-slate-700"
                  }`}
                >
                  No medicines found
                </p>

                <p
                  className={`mt-1 max-w-[280px] text-[9px] leading-4 ${
                    darkMode ? "text-slate-600" : "text-slate-400"
                  }`}
                >
                  Type a medicine name and click Search to query the OpenFDA registry, or select one of the popular searches above.
                </p>
              </section>
            ) : (
              <div className="mt-3 grid grid-cols-3 gap-3">
                {filteredMedicines.map((medicine) => (
                  <MedicineCard
                    key={medicine.id}
                    medicine={medicine}
                    darkMode={darkMode}
                    onView={setSelectedMedicine}
                  />
                ))}
              </div>
            )}

            <div
              className={`mt-3 flex items-start gap-2 rounded-[14px] border p-4 ${
                darkMode
                  ? "border-amber-500/20 bg-amber-500/5"
                  : "border-amber-100 bg-amber-50/60"
              }`}
            >
              <Info
                size={14}
                className="mt-0.5 shrink-0 text-amber-500"
              />

              <p
                className={`text-[8px] leading-4 ${
                  darkMode ? "text-slate-500" : "text-slate-600"
                }`}
              >
                Medicine information on this page is retrieved from OpenFDA and clinical records.
                Always confirm dosing, suitability, contraindications and interactions with a licensed healthcare professional.
              </p>
            </div>
          </div>
        </main>
      </div>

      <DetailsModal
        medicine={selectedMedicine}
        darkMode={darkMode}
        onClose={() => setSelectedMedicine(null)}
      />
    </div>
  );
}
