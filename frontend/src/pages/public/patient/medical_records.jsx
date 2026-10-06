import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Sidebar from "../patient/sidebar";
import {
  Activity,
  AlertTriangle,
  ArrowDownToLine,
  Brain,
  ChevronDown,
  ClipboardList,
  Eye,
  FileText,
  Heart,
  Home,
  LogIn,
  Moon,
  Pill,
  Search,
  Settings,
  Sparkles,
  Stethoscope,
  Sun,
  TrendingUp,
  X,
} from "lucide-react";
import { useAuth } from "../../../_core/hooks/useAuth";
import { useTheme } from "../ThemeContext";
import patientService from "../../../services/patientService";

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
        icon: Pill,
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

const tabs = [
  "All",
  "Lab Reports",
  "Prescriptions",
  "Imaging",
  "Doctor Notes",
  "Other",
];

const records = [];

function isActivePath(pathname, route) {
  return (
    pathname.replace(/\/$/, "") ===
    route.replace(/\/$/, "")
  );
}

function Header({
  darkMode,
  toggleTheme,
}) {
  const { user } = useAuth();
  const displayName =
    user?.full_name ||
    (user?.first_name ? `${user.first_name} ${user.last_name || ""}`.trim() : null) ||
    user?.email ||
    "Patient";

  return (
    <header
      className={`flex h-[82px] shrink-0 items-center justify-between border-b px-8 ${
        darkMode
          ? "border-slate-800 bg-[#111c1b]"
          : "border-slate-100 bg-white"
      }`}
    >
      {/* Page title */}
      <div>
        <h1
          className={`text-[28px] font-bold tracking-[-0.7px] ${
            darkMode
              ? "text-white"
              : "text-emerald-950"
          }`}
        >
          Medical Records
        </h1>

        <p
          className={`mt-1 text-[13px] ${
            darkMode
              ? "text-slate-500"
              : "text-slate-500"
          }`}
        >
          All your medical documents in one place
        </p>
      </div>

      {/* Header controls */}
      <div className="flex items-center gap-4">
        <div
          className={`flex h-11 w-[270px] items-center gap-3 rounded-xl border px-4 ${
            darkMode
              ? "border-slate-700 bg-slate-900/40"
              : "border-slate-200 bg-white"
          }`}
        >
          <Search
            size={18}
            className="text-slate-500"
          />

          <input
            placeholder="Search records..."
            className={`w-full bg-transparent text-[13px] outline-none ${
              darkMode
                ? "text-white placeholder:text-slate-500"
                : "text-slate-700 placeholder:text-slate-400"
            }`}
          />
        </div>

        {/* Theme */}
        <button
          type="button"
          onClick={toggleTheme}
          className={`flex h-11 w-11 items-center justify-center rounded-xl border transition ${
            darkMode
              ? "border-slate-700 bg-slate-900 text-yellow-300 hover:bg-slate-800"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
          }`}
          aria-label="Toggle theme"
        >
          {darkMode ? (
            <Sun size={20} />
          ) : (
            <Moon size={20} />
          )}
        </button>

        {/* Notifications */}
        <button
          type="button"
          className={`relative ${
            darkMode
              ? "text-slate-300"
              : "text-slate-700"
          }`}
        >
          <svg
            className="h-[22px] w-[22px]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
          >
            <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
            <path d="M10 21h4" />
          </svg>

          <span
            className={`absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 ${
              darkMode
                ? "border-[#111c1b]"
                : "border-white"
            } bg-emerald-500`}
          />
        </button>

        {/* User */}
        <Link
          to={ROUTES.settings}
          className="flex items-center gap-3"
        >
          <div
            className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 text-white font-semibold text-xs"
          >
            {displayName.slice(0, 2).toUpperCase()}
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
            size={17}
            className={
              darkMode
                ? "text-slate-400"
                : "text-slate-600"
            }
          />
        </Link>
      </div>
    </header>
  );
}

function UploadModal({
  darkMode,
  onClose,
  onUpload,
}) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("Lab Reports");
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const submit = async () => {
    if (!file) return;

    try {
      setIsUploading(true);
      setErrorMsg("");
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title || file.name);
      await patientService.uploadMedicalRecord(formData);
      if (onUpload) onUpload();
      onClose();
    } catch (err) {
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        "Upload failed. Please ensure file is valid (PDF/PNG/JPG).";
      setErrorMsg(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div
        className={`w-full max-w-md rounded-2xl border p-6 shadow-2xl ${
          darkMode
            ? "border-slate-700 bg-[#15211f]"
            : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-start justify-between">
          <div>
            <h3
              className={`text-[18px] font-bold ${
                darkMode
                  ? "text-white"
                  : "text-emerald-950"
              }`}
            >
              Upload Medical Record
            </h3>

            <p
              className={`mt-1 text-[12px] ${
                darkMode
                  ? "text-slate-500"
                  : "text-slate-500"
              }`}
            >
              Add a verified diagnostic report or document to your records.
            </p>
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
            <X size={19} />
          </button>
        </div>

        {errorMsg && (
          <div className="mt-3 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-[11px] text-red-500">
            {errorMsg}
          </div>
        )}

        <div className="mt-6 space-y-4">
          <label
            className={`block text-[12px] font-medium ${
              darkMode
                ? "text-slate-300"
                : "text-slate-700"
            }`}
          >
            Document File
            <div
              className={`mt-2 flex cursor-pointer items-center gap-3 rounded-lg border border-dashed px-3 py-3 ${
                darkMode
                  ? "border-slate-700 bg-[#101918]"
                  : "border-slate-200 bg-slate-50"
              }`}
            >
              <ArrowDownToLine
                size={19}
                className="text-emerald-500"
              />

              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => {
                  const f = e.target.files?.[0] ?? null;
                  setFile(f);
                  if (f && !title) setTitle(f.name.replace(/\.[^/.]+$/, ""));
                }}
                className="w-full text-[11px]"
              />
            </div>
          </label>

          <label
            className={`block text-[12px] font-medium ${
              darkMode
                ? "text-slate-300"
                : "text-slate-700"
            }`}
          >
            Document Title
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., CBC Blood Test Report"
              className={`mt-2 w-full rounded-lg border px-3 py-2.5 text-[12px] outline-none ${
                darkMode
                  ? "border-slate-700 bg-[#101918] text-slate-200"
                  : "border-slate-200 bg-white text-slate-700"
              }`}
            />
          </label>

          <label
            className={`block text-[12px] font-medium ${
              darkMode
                ? "text-slate-300"
                : "text-slate-700"
            }`}
          >
            Category
            <select
              value={category}
              onChange={(e) =>
                setCategory(e.target.value)
              }
              className={`mt-2 w-full rounded-lg border px-3 py-2.5 text-[12px] outline-none ${
                darkMode
                  ? "border-slate-700 bg-[#101918] text-slate-200"
                  : "border-slate-200 bg-white text-slate-700"
              }`}
            >
              <option>Lab Reports</option>
              <option>Prescriptions</option>
              <option>Imaging</option>
              <option>Doctor Notes</option>
              <option>Other</option>
            </select>
          </label>

          <button
            type="button"
            onClick={submit}
            disabled={!file || isUploading}
            className={`mt-2 w-full rounded-lg px-4 py-3 text-[12px] font-semibold text-white transition ${
              file && !isUploading
                ? "bg-emerald-500 hover:bg-emerald-600"
                : "cursor-not-allowed bg-slate-400 opacity-60"
            }`}
          >
            {isUploading ? "Uploading..." : "Upload Record"}
          </button>
        </div>
      </div>
    </div>
  );
}

function RecordPreview({
  record,
  darkMode,
  onClose,
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div
        className={`w-full max-w-lg rounded-2xl border shadow-2xl ${
          darkMode
            ? "border-slate-700 bg-[#15211f]"
            : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-start justify-between border-b p-6">
          <div>
            <h3
              className={`text-[18px] font-bold ${
                darkMode
                  ? "text-white"
                  : "text-emerald-950"
              }`}
            >
              {record.document}
            </h3>

            <p
              className={`mt-1 text-[12px] ${
                darkMode
                  ? "text-slate-500"
                  : "text-slate-500"
              }`}
            >
              {record.type} · {record.date}
            </p>
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
            <X size={19} />
          </button>
        </div>

        <div className="p-6">
          <div
            className={`flex items-center gap-3 rounded-xl border p-4 ${
              darkMode
                ? "border-slate-800 bg-[#101918]"
                : "border-slate-100 bg-slate-50"
            }`}
          >
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                darkMode
                  ? "bg-emerald-500/10"
                  : "bg-emerald-50"
              }`}
            >
              <FileText
                size={19}
                className="text-emerald-500"
              />
            </div>

            <div>
              <p
                className={`text-[12px] font-semibold ${
                  darkMode
                    ? "text-slate-200"
                    : "text-slate-700"
                }`}
              >
                Attending Doctor
              </p>

              <p
                className={`mt-0.5 text-[11px] ${
                  darkMode
                    ? "text-slate-500"
                    : "text-slate-500"
                }`}
              >
                {record.doctor}
              </p>
            </div>
          </div>

          <div className="mt-5 grid grid-cols-3 gap-3">
            {[
              ["TYPE", record.type],
              ["DATE", record.date],
              ["CATEGORY", record.category],
            ].map(([label, value]) => (
              <div
                key={label}
                className={`rounded-xl border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#101918]"
                    : "border-slate-100 bg-slate-50"
                }`}
              >
                <p className="text-[9px] text-slate-500">
                  {label}
                </p>

                <p
                  className={`mt-1.5 text-[11px] font-medium ${
                    darkMode
                      ? "text-slate-200"
                      : "text-slate-700"
                  }`}
                >
                  {value}
                </p>
              </div>
            ))}
          </div>

          <div
            className={`mt-5 rounded-xl border p-5 ${
              darkMode
                ? "border-slate-800 bg-[#101918]"
                : "border-slate-100 bg-slate-50"
            }`}
          >
            <p className="text-[9px] uppercase tracking-[0.08em] text-slate-500">
              Summary
            </p>

            <p
              className={`mt-2 text-[12px] leading-6 ${
                darkMode
                  ? "text-slate-300"
                  : "text-slate-600"
              }`}
            >
              {record.summary}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function MedicalRecords() {
  const { isDark: darkMode, toggleTheme } = useTheme();

  const [activeTab, setActiveTab] =
    useState("All");

  const [search, setSearch] =
    useState("");

  const [page, setPage] =
    useState(1);

  const [showUpload, setShowUpload] =
    useState(false);

  const [preview, setPreview] =
    useState(null);

  const [allRecords, setAllRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      const [recRes, labRes] = await Promise.allSettled([
        patientService.getMedicalRecords(),
        patientService.getLabReports(),
      ]);
      const list = [];
      if (recRes.status === "fulfilled") {
        const raw = recRes.value?.results || recRes.value || [];
        if (Array.isArray(raw)) {
          raw.forEach((r) => {
            list.push({
              id: `rec-${r.id}`,
              document: r.title || "Clinical Medical Record",
              type: r.record_type || "Clinical Note",
              doctor: r.doctor_name || "Attending Physician",
              date: r.recorded_at
                ? new Date(r.recorded_at).toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" })
                : "Recorded",
              category: r.record_type === "Prescription" ? "Prescriptions" : "Doctor Notes",
              summary: r.description || "Clinical patient encounter documentation.",
            });
          });
        }
      }
      if (labRes.status === "fulfilled") {
        const raw = labRes.value?.results || labRes.value || [];
        if (Array.isArray(raw)) {
          raw.forEach((l) => {
            list.push({
              id: `lab-${l.id}`,
              document: l.title || "Diagnostic Report",
              type: l.file_type || "Lab Report",
              doctor: "Pathology / Diagnostic Lab",
              date: l.uploaded_at
                ? new Date(l.uploaded_at).toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" })
                : "Uploaded",
              category: "Lab Reports",
              summary: l.analysis_summary || l.extracted_text || "Diagnostic test documentation.",
            });
          });
        }
      }
      setAllRecords(list);
    } catch (err) {
      console.warn("Failed to load records:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, []);

  const filteredRecords = useMemo(() => {
    const term =
      search.trim().toLowerCase();

    return allRecords.filter((record) => {
      const matchesTab =
        activeTab === "All" ||
        record.category === activeTab;

      const matchesSearch =
        !term ||
        record.document
          .toLowerCase()
          .includes(term) ||
        record.type
          .toLowerCase()
          .includes(term) ||
        record.doctor
          .toLowerCase()
          .includes(term);

      return (
        matchesTab &&
        matchesSearch
      );
    });
  }, [
    activeTab,
    search,
    allRecords,
  ]);

  const pageSize = 8;

  const pageCount = Math.max(
    1,
    Math.ceil(
      filteredRecords.length /
        pageSize
    )
  );

  const currentRecords =
    filteredRecords.slice(
      (page - 1) * pageSize,
      page * pageSize
    );

  useEffect(() => {
    setPage(1);
  }, [activeTab, search]);

  const downloadRecord = (record) => {
    const content = [
      "MediCare Medical Record",
      `Document: ${record.document}`,
      `Type: ${record.type}`,
      `Doctor: ${record.doctor}`,
      `Date: ${record.date}`,
      `Category: ${record.category}`,
      "",
      record.summary,
    ].join("\n");

    const blob = new Blob(
      [content],
      {
        type: "text/plain;charset=utf-8",
      }
    );

    const url =
      URL.createObjectURL(blob);

    const anchor =
      document.createElement("a");

    anchor.href = url;

    anchor.download = `${record.document.replace(
      /\s+/g,
      "_"
    )}.txt`;

    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();

    URL.revokeObjectURL(url);
  };

  return (
    /*
     * FULL SCREEN
     */
    <div
      className={`h-screen w-full overflow-hidden ${
        darkMode
          ? "bg-[#0b1413] text-white"
          : "bg-[#f8faf9] text-slate-900"
      }`}
    >
      <div
        className={`flex h-full w-full overflow-hidden ${
          darkMode
            ? "bg-[#111c1b]"
            : "bg-white"
        }`}
      >
        {/* Sidebar */}
        <Sidebar darkMode={darkMode} />

        {/* Main */}
        <main className="ml-[255px] flex h-full min-w-0 flex-1 flex-col overflow-hidden">
          {/* Header */}
          <Header
            darkMode={darkMode}
            toggleTheme={toggleTheme}
          />

          {/*
           * MAIN CONTENT
           */}
          <div className="flex min-h-0 flex-1 flex-col overflow-y-auto px-8 py-6">

            {/* Search + Date */}
            <div className="flex items-center gap-3">
              <div
                className={`flex h-11 min-w-0 flex-1 items-center gap-3 rounded-xl border px-4 ${
                  darkMode
                    ? "border-slate-700 bg-[#101918]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <Search
                  size={18}
                  className="text-slate-500"
                />

                <input
                  value={search}
                  onChange={(e) =>
                    setSearch(
                      e.target.value
                    )
                  }
                  placeholder="Search medical records..."
                  className={`w-full bg-transparent text-[13px] outline-none ${
                    darkMode
                      ? "text-white placeholder:text-slate-500"
                      : "text-slate-700 placeholder:text-slate-400"
                  }`}
                />
              </div>

              <select
                defaultValue="All Dates"
                className={`h-11 rounded-xl border px-4 text-[12px] outline-none ${
                  darkMode
                    ? "border-slate-700 bg-[#101918] text-slate-300"
                    : "border-slate-200 bg-white text-slate-700"
                }`}
              >
                <option>
                  All Dates
                </option>

                <option>
                  Last 30 Days
                </option>

                <option>
                  Last 3 Months
                </option>

                <option>
                  This Year
                </option>
              </select>
            </div>

            {/* Tabs + Upload button */}
            <div className="mt-4 flex items-center justify-between gap-4">
              <div className="flex flex-wrap gap-2">
                {tabs.map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() =>
                      setActiveTab(tab)
                    }
                    className={`rounded-lg px-4 py-2 text-[11px] font-medium transition ${
                      activeTab === tab
                        ? "bg-emerald-500 text-white"
                        : darkMode
                          ? "border border-slate-800 bg-[#15211f] text-slate-400 hover:text-white"
                          : "border border-slate-200 bg-white text-slate-500 hover:text-slate-800"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Upload is intentionally lower */}
              <button
                type="button"
                onClick={() =>
                  setShowUpload(true)
                }
                className="shrink-0 rounded-lg bg-emerald-500 px-5 py-2.5 text-[11px] font-semibold text-white transition hover:bg-emerald-600"
              >
                + Upload Record
              </button>
            </div>

            {/* Records table */}
            <section
              className={`mt-4 flex min-h-0 flex-1 flex-col overflow-hidden rounded-[14px] border ${
                darkMode
                  ? "border-slate-800 bg-[#15211f]"
                  : "border-slate-200 bg-white"
              }`}
            >
              {/* Table header */}
              <div
                className={`grid shrink-0 grid-cols-[1.6fr_1fr_1.1fr_0.9fr_0.65fr] px-5 py-4 text-[10px] font-semibold uppercase tracking-[0.08em] ${
                  darkMode
                    ? "text-slate-600"
                    : "text-slate-400"
                }`}
              >
                <span>
                  Document
                </span>

                <span>
                  Type
                </span>

                <span>
                  Doctor
                </span>

                <span>
                  Date
                </span>

                <span className="text-right">
                  Action
                </span>
              </div>

              {/* Scrollable table */}
              <div className="min-h-0 flex-1 overflow-y-auto">
                {currentRecords.length ===
                0 ? (
                  <div
                    className={`border-t px-4 py-12 text-center text-[13px] ${
                      darkMode
                        ? "border-slate-800 text-slate-500"
                        : "border-slate-100 text-slate-500"
                    }`}
                  >
                    No medical records
                    found.
                  </div>
                ) : (
                  currentRecords.map(
                    (
                      record,
                      index
                    ) => (
                      <div
                        key={
                          record.id
                        }
                        className={`grid grid-cols-[1.6fr_1fr_1.1fr_0.9fr_0.65fr] items-center px-5 py-4 ${
                          index !==
                          currentRecords.length -
                            1
                            ? `border-t ${
                                darkMode
                                  ? "border-slate-800"
                                  : "border-slate-100"
                              }`
                            : ""
                        }`}
                      >
                        {/* Document */}
                        <div className="flex min-w-0 items-center gap-3">
                          <div
                            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
                              darkMode
                                ? "bg-emerald-500/10"
                                : "bg-emerald-50"
                            }`}
                          >
                            <FileText
                              size={17}
                              className="text-emerald-500"
                            />
                          </div>

                          <div className="min-w-0">
                            <p
                              className={`truncate text-[12px] font-semibold ${
                                darkMode
                                  ? "text-slate-200"
                                  : "text-slate-700"
                              }`}
                            >
                              {
                                record.document
                              }
                            </p>

                            <p
                              className={`mt-1 text-[10px] ${
                                darkMode
                                  ? "text-slate-600"
                                  : "text-slate-400"
                              }`}
                            >
                              {
                                record.category
                              }
                            </p>
                          </div>
                        </div>

                        {/* Type */}
                        <span
                          className={`text-[11px] ${
                            darkMode
                              ? "text-slate-400"
                              : "text-slate-500"
                          }`}
                        >
                          {
                            record.type
                          }
                        </span>

                        {/* Doctor */}
                        <span
                          className={`truncate text-[11px] ${
                            darkMode
                              ? "text-slate-400"
                              : "text-slate-500"
                          }`}
                        >
                          {
                            record.doctor
                          }
                        </span>

                        {/* Date */}
                        <span
                          className={`text-[11px] ${
                            darkMode
                              ? "text-slate-400"
                              : "text-slate-500"
                          }`}
                        >
                          {
                            record.date
                          }
                        </span>

                        {/* Actions */}
                        <div className="flex justify-end gap-2">
                          <button
                            type="button"
                            onClick={() =>
                              setPreview(
                                record
                              )
                            }
                            className={`rounded-md p-2 ${
                              darkMode
                                ? "text-slate-400 hover:bg-slate-800"
                                : "text-slate-500 hover:bg-slate-100"
                            }`}
                            title="View"
                          >
                            <Eye
                              size={16}
                            />
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              downloadRecord(
                                record
                              )
                            }
                            className={`rounded-md p-2 ${
                              darkMode
                                ? "text-slate-400 hover:bg-slate-800"
                                : "text-slate-500 hover:bg-slate-100"
                            }`}
                            title="Download"
                          >
                            <ArrowDownToLine
                              size={16}
                            />
                          </button>
                        </div>
                      </div>
                    )
                  )
                )}
              </div>

              {/* Pagination */}
              <div
                className={`flex shrink-0 items-center justify-between border-t px-5 py-4 text-[10px] ${
                  darkMode
                    ? "border-slate-800 text-slate-500"
                    : "border-slate-100 text-slate-500"
                }`}
              >
                <span>
                  Showing{" "}
                  {filteredRecords.length ===
                  0
                    ? 0
                    : (page - 1) *
                        pageSize +
                      1}
                  –
                  {Math.min(
                    page * pageSize,
                    filteredRecords.length
                  )}{" "}
                  of{" "}
                  {
                    filteredRecords.length
                  }{" "}
                  records
                </span>

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() =>
                      setPage((p) =>
                        Math.max(
                          1,
                          p - 1
                        )
                      )
                    }
                    disabled={page === 1}
                    className={`rounded-md px-2.5 py-1.5 text-[11px] ${
                      page === 1
                        ? "cursor-not-allowed opacity-30"
                        : darkMode
                          ? "hover:bg-slate-800"
                          : "hover:bg-slate-100"
                    }`}
                  >
                    ‹
                  </button>

                  {Array.from(
                    {
                      length:
                        pageCount,
                    },
                    (_, index) =>
                      index + 1
                  ).map(
                    (pageNumber) => (
                      <button
                        key={
                          pageNumber
                        }
                        type="button"
                        onClick={() =>
                          setPage(
                            pageNumber
                          )
                        }
                        className={`min-w-7 rounded-md px-2.5 py-1.5 text-[11px] ${
                          page ===
                          pageNumber
                            ? "bg-emerald-500 text-white"
                            : darkMode
                              ? "hover:bg-slate-800"
                              : "hover:bg-slate-100"
                        }`}
                      >
                        {
                          pageNumber
                        }
                      </button>
                    )
                  )}

                  <button
                    type="button"
                    onClick={() =>
                      setPage((p) =>
                        Math.min(
                          pageCount,
                          p + 1
                        )
                      )
                    }
                    disabled={
                      page ===
                      pageCount
                    }
                    className={`rounded-md px-2.5 py-1.5 text-[11px] ${
                      page ===
                      pageCount
                        ? "cursor-not-allowed opacity-30"
                        : darkMode
                          ? "hover:bg-slate-800"
                          : "hover:bg-slate-100"
                    }`}
                  >
                    ›
                  </button>
                </div>
              </div>
            </section>
          </div>
        </main>
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <UploadModal
          darkMode={darkMode}
          onClose={() =>
            setShowUpload(false)
          }
          onUpload={() => {
            fetchRecords();
          }}
        />
      )}

      {/* Preview Modal */}
      {preview && (
        <RecordPreview
          record={preview}
          darkMode={darkMode}
          onClose={() =>
            setPreview(null)
          }
        />
      )}
    </div>
  );
}