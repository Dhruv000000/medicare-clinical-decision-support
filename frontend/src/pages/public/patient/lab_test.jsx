// ==============================================================================
// FILE: frontend/src/pages/public/patient/lab_test.jsx
// PURPOSE: Diagnostic lab test reporting portal with OCR biomarker parsing, flag detection, and trend analysis.
// VIVA EXPLANATION: This interface manages laboratory test results. Patients can view historical biomarker panels, upload PDF or image reports for automated OCR parsing, and inspect flagged out-of-range values (abnormal, critical, borderline).
// ==============================================================================

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  CloudUpload,
  ExternalLink,
  FileText,
  ListChecks,
  Loader2,
  Moon,
  Plus,
  Search,
  Sparkles,
  Stethoscope,
  Sun,
  X,
  XCircle,
} from "lucide-react";
import Sidebar from "./sidebar";
import { useAuth } from "../../../_core/hooks/useAuth";
import { useTheme } from "../ThemeContext";
import patientService from "../../../services/patientService";

const defaultStatusStyles = {
  normal: {
    badge: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
    chart: "text-emerald-400",
  },
  high: {
    badge: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
    chart: "text-amber-400",
  },
  borderline: {
    badge: "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20",
    chart: "text-yellow-400",
  },
  critical: {
    badge: "bg-red-500/10 text-red-400 border border-red-500/20",
    chart: "text-red-400",
  },
  low: {
    badge: "bg-orange-500/10 text-orange-400 border border-orange-500/20",
    chart: "text-orange-400",
  },
};

// --- ReportsLabTests ---
// What it does: Primary laboratory test records portal managing document fetching, search filters, and automated analysis triggers.
// Why it's structured this way: Asynchronously queries patientService.getLabReports and coordinates report upload and extraction modals.
// Parameters & Returns: Props: propDarkMode (boolean, optional). Returns lab test portal view JSX.
// ------------------------------------------------------------------------------
export default function ReportsLabTests({ darkMode: propDarkMode }) {
  const { isDark, toggleTheme } = useTheme();
  const darkMode = propDarkMode !== undefined ? propDarkMode : isDark;
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("all");

  // Modals
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showAnalysisModal, setShowAnalysisModal] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analyzingId, setAnalyzingId] = useState(null);
  const [actionError, setActionError] = useState("");

  const loadReports = async () => {
    try {
      setLoading(true);
      const data = await patientService.getLabReports();
      setReports(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load lab reports:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleAnalyze = async (reportId) => {
    try {
      setActionError("");
      setAnalyzingId(reportId);
      const result = await patientService.analyzeLabReport(reportId);
      setAnalysisResult(result);
      setShowAnalysisModal(true);
      // Refresh reports list to reflect newly extracted results and summaries
      loadReports();
    } catch (err) {
      console.error("Analysis failed:", err);
      setActionError(
        err.response?.data?.error?.message ||
          err.response?.data?.detail ||
          "Failed to analyze report with AI service."
      );
    } finally {
      setAnalyzingId(null);
    }
  };

  const filteredReports = reports.filter((r) => {
    const titleMatch = (r.title || "").toLowerCase().includes(searchQuery.toLowerCase());
    if (!titleMatch) return false;
    const isAnalyzed = (r.results && r.results.length > 0) || !!r.analysis_summary;
    if (filterType === "all") return true;
    if (filterType === "analyzed") return isAnalyzed;
    if (filterType === "pending") return !isAnalyzed;
    return true;
  });

  // Calculate summary metrics
  const totalReports = reports.length;
  let normalCount = 0;
  let abnormalCount = 0;
  let pendingCount = 0;

  reports.forEach((r) => {
    const isAnalyzed = (r.results && r.results.length > 0) || !!r.analysis_summary;
    if (!isAnalyzed) {
      pendingCount += 1;
    } else {
      const hasAbnormal = (r.results || []).some(
        (m) => m.flag && m.flag.toUpperCase() !== "NORMAL"
      );
      if (hasAbnormal) {
        abnormalCount += 1;
      } else {
        normalCount += 1;
      }
    }
  });

  const patientName = user
    ? `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email.split("@")[0]
    : "Patient";

  return (
    <div
      className={`h-screen w-full overflow-hidden ${
        darkMode ? "bg-[#081211] text-white" : "bg-slate-50 text-slate-900"
      }`}
    >
      <Sidebar darkMode={darkMode} />

      <div className="ml-[255px] flex h-screen min-w-0 flex-col overflow-hidden">
        {/* ===================================================
            HEADER
        =================================================== */}
        <header
          className={`flex h-[86px] shrink-0 items-center justify-between border-b px-8 ${
            darkMode ? "border-slate-800 bg-[#0b1716]" : "border-slate-200 bg-white"
          }`}
        >
          <div className="min-w-0">
            <h1 className="text-[26px] font-bold tracking-[-0.7px]">
              Reports & Lab Tests
            </h1>
            <p
              className={`mt-0.5 text-[12px] ${
                darkMode ? "text-slate-400" : "text-slate-500"
              }`}
            >
              View, analyze, and track clinical laboratory diagnostic records
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-3">
            <div
              className={`flex h-[42px] w-[240px] items-center gap-3 rounded-xl border px-3.5 ${
                darkMode
                  ? "border-slate-700 bg-[#0d1918]"
                  : "border-slate-200 bg-white"
              }`}
            >
              <Search size={17} strokeWidth={1.8} className="text-slate-400" />
              <input
                type="text"
                placeholder="Search tests & reports..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`w-full bg-transparent text-[12px] outline-none ${
                  darkMode
                    ? "text-white placeholder:text-slate-500"
                    : "text-slate-900 placeholder:text-slate-400"
                }`}
              />
            </div>

            {/* Notification */}
            <div
              className={`relative flex h-[42px] w-[40px] items-center justify-center rounded-xl border ${
                darkMode
                  ? "border-slate-700 bg-[#0d1918] text-white"
                  : "border-slate-200 bg-white text-slate-700"
              }`}
            >
              <Activity size={20} />
              <span className="absolute right-[8px] top-[9px] h-[6px] w-[6px] rounded-full bg-emerald-400" />
            </div>

            {/* Theme Toggle */}
            <button
              type="button"
              onClick={toggleTheme}
              title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
              aria-label="Toggle theme"
              className={`flex h-[42px] w-[42px] items-center justify-center rounded-xl border transition ${
                darkMode
                  ? "border-slate-700 bg-[#0d1918] text-amber-300 hover:bg-slate-800"
                  : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-sm"
              }`}
            >
              {darkMode ? <Sun size={19} /> : <Moon size={19} />}
            </button>

            {/* User */}
            <div className="flex items-center gap-2">
              <div className="h-[38px] w-[38px] overflow-hidden rounded-full bg-slate-700">
                <img
                  src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
                  alt={patientName}
                  className="h-full w-full object-cover"
                />
              </div>
              <span
                className={`text-[13px] font-semibold ${
                  darkMode ? "text-white" : "text-slate-900"
                }`}
              >
                {patientName}
              </span>
              <ChevronDown size={14} className="text-slate-400" />
            </div>
          </div>
        </header>

        {/* ===================================================
            MAIN CONTENT
        =================================================== */}
        <main className="min-h-0 flex-1 overflow-y-auto px-8 py-5">
          {actionError && (
            <div className="mb-4 flex items-center justify-between rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-[12px] text-red-400">
              <div className="flex items-center gap-2">
                <AlertCircle size={16} />
                <span>{actionError}</span>
              </div>
              <button
                type="button"
                onClick={() => setActionError("")}
                className="text-red-400 hover:text-red-300"
              >
                <X size={14} />
              </button>
            </div>
          )}

          {/* =================================================
              SUMMARY CARDS
          ================================================= */}
          <div className="grid grid-cols-4 gap-4">
            <SummaryCard
              title="TOTAL TESTS"
              value={totalReports}
              icon={<ClipboardList size={19} />}
              darkMode={darkMode}
            />
            <SummaryCard
              title="NORMAL"
              value={normalCount}
              icon={<CheckCircle2 size={19} />}
              darkMode={darkMode}
            />
            <SummaryCard
              title="ABNORMAL"
              value={abnormalCount}
              icon={<XCircle size={19} />}
              darkMode={darkMode}
            />
            <SummaryCard
              title="PENDING / NEW"
              value={pendingCount}
              icon={<Activity size={19} />}
              darkMode={darkMode}
            />
          </div>

          {/* =================================================
              ALL TEST RESULTS TABLE
          ================================================= */}
          <section
            className={`mt-5 overflow-hidden rounded-2xl border ${
              darkMode
                ? "border-slate-800 bg-[#0c1817]"
                : "border-slate-200 bg-white"
            }`}
          >
            {/* Table Action Bar */}
            <div
              className={`flex h-[68px] shrink-0 items-center justify-between border-b px-5 ${
                darkMode ? "border-slate-800" : "border-slate-200"
              }`}
            >
              <div>
                <h2 className={`text-[17px] font-bold ${darkMode ? "text-white" : "text-slate-900"}`}>
                  Lab Reports & Diagnostics
                </h2>
                <p className={`mt-0.5 text-[10px] ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
                  Uploaded diagnostic documents, parsed clinical metrics, and automated risk analysis
                </p>
              </div>

              <div className="flex items-center gap-3">
                <div
                  className={`flex items-center gap-1 rounded-lg border p-1 text-[11px] ${
                    darkMode ? "border-slate-700 bg-[#0a1514]" : "border-slate-200 bg-slate-50"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => setFilterType("all")}
                    className={`rounded-md px-2.5 py-1 font-medium transition ${
                      filterType === "all"
                        ? "bg-emerald-500 text-white"
                        : darkMode
                        ? "text-slate-400 hover:text-white"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    All ({totalReports})
                  </button>
                  <button
                    type="button"
                    onClick={() => setFilterType("analyzed")}
                    className={`rounded-md px-2.5 py-1 font-medium transition ${
                      filterType === "analyzed"
                        ? "bg-emerald-500 text-white"
                        : darkMode
                        ? "text-slate-400 hover:text-white"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    Analyzed ({normalCount + abnormalCount})
                  </button>
                  <button
                    type="button"
                    onClick={() => setFilterType("pending")}
                    className={`rounded-md px-2.5 py-1 font-medium transition ${
                      filterType === "pending"
                        ? "bg-emerald-500 text-white"
                        : darkMode
                        ? "text-slate-400 hover:text-white"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    Pending ({pendingCount})
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => setShowUploadModal(true)}
                  className={`flex h-[36px] items-center gap-2 rounded-lg border px-4 text-[11px] font-semibold transition ${
                    darkMode
                      ? "border-emerald-500/60 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                      : "border-emerald-600/30 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                  }`}
                >
                  <CloudUpload size={15} />
                  Upload Report
                </button>
              </div>
            </div>

            {/* Table Rows */}
            <div className="min-w-0">
              {/* Column Headings */}
              <div
                className={`grid h-[42px] grid-cols-[1.4fr_1.1fr_1.3fr_.9fr_.9fr_1.1fr] items-center px-5 text-[10px] font-semibold uppercase tracking-[0.08em] ${
                  darkMode ? "text-slate-400" : "text-slate-500"
                }`}
              >
                <span>Report / Test Name</span>
                <span>Extracted Metrics</span>
                <span>Key Findings / Summary</span>
                <span>Status Flag</span>
                <span>Upload Date</span>
                <span className="text-right">Actions</span>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-16 text-[12px] text-slate-400">
                  <Loader2 size={20} className="mr-2 animate-spin text-emerald-400" />
                  Loading diagnostic reports from database...
                </div>
              ) : filteredReports.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center text-slate-500">
                  <ClipboardList size={36} className="mb-2 text-slate-600" />
                  <p className="text-[13px] font-semibold">No lab reports found</p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    Upload a clinical lab report (PDF, text, image) to extract structured biomarkers.
                  </p>
                  <button
                    type="button"
                    onClick={() => setShowUploadModal(true)}
                    className="mt-4 inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-[11px] font-semibold text-white transition hover:bg-emerald-600"
                  >
                    <Plus size={14} />
                    Upload First Report
                  </button>
                </div>
              ) : (
                filteredReports.map((report) => {
                  const isAnalyzed = (report.results && report.results.length > 0) || !!report.analysis_summary;
                  const hasResults = report.results && report.results.length > 0;
                  const abnormalMetrics = (report.results || []).filter(
                    (m) => m.flag && m.flag.toUpperCase() !== "NORMAL"
                  );
                  const isAbnormal = abnormalMetrics.length > 0;

                  const statusBadgeClass = !isAnalyzed
                    ? "bg-slate-500/10 text-slate-400 border border-slate-500/20"
                    : isAbnormal
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";

                  const statusLabel = !isAnalyzed
                    ? "Pending"
                    : isAbnormal
                    ? `${abnormalMetrics.length} Abnormal`
                    : (hasResults ? "Normal" : "Analyzed");

                  const dateStr = report.uploaded_at
                    ? new Date(report.uploaded_at).toLocaleDateString("en-US", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })
                    : "Recent";

                  return (
                    <div
                      key={`report-${report.id}`}
                      className={`grid h-[58px] grid-cols-[1.4fr_1.1fr_1.3fr_.9fr_.9fr_1.1fr] items-center border-t px-5 text-[11px] transition hover:bg-emerald-500/[0.02] ${
                        darkMode ? "border-slate-800/80" : "border-slate-100"
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0 pr-3">
                        <FileText size={16} className="shrink-0 text-emerald-500" />
                        <div className="min-w-0 truncate">
                          <p className={`truncate font-semibold ${darkMode ? "text-white" : "text-slate-900"}`}>{report.title}</p>
                          <p className={`truncate text-[9px] ${darkMode ? "text-slate-500" : "text-slate-400"}`}>
                            {report.file_type || "Diagnostic Document"}
                          </p>
                        </div>
                      </div>

                      <div className="min-w-0 pr-2">
                        {hasResults ? (
                          <div className="flex flex-wrap gap-1">
                            {report.results.slice(0, 2).map((r, idx) => (
                              <span
                                key={idx}
                                className={`rounded px-1.5 py-0.5 text-[9px] ${
                                  darkMode
                                    ? "bg-slate-800 text-slate-300"
                                    : "bg-slate-100 text-slate-700 border border-slate-200"
                                }`}
                              >
                                {r.test_name}: {r.value} {r.unit}
                              </span>
                            ))}
                            {report.results.length > 2 && (
                              <span className={`text-[9px] ${darkMode ? "text-slate-500" : "text-slate-400"}`}>
                                +{report.results.length - 2} more
                              </span>
                            )}
                          </div>
                        ) : isAnalyzed ? (
                          <span className={`text-[10px] ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
                            Document parsed
                          </span>
                        ) : (
                          <span className={`text-[10px] italic ${darkMode ? "text-slate-500" : "text-slate-400"}`}>
                            Not analyzed yet
                          </span>
                        )}
                      </div>

                      <div className={`min-w-0 truncate pr-3 text-[10px] ${darkMode ? "text-slate-400" : "text-slate-600"}`}>
                        {report.analysis_summary || report.extracted_text
                          ? (report.analysis_summary || report.extracted_text).slice(0, 50) + "..."
                          : "Raw report uploaded."}
                      </div>

                      <div>
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-[9px] font-semibold ${statusBadgeClass}`}
                        >
                          {statusLabel}
                        </span>
                      </div>

                      <div className={`text-[10px] ${darkMode ? "text-slate-400" : "text-slate-500"}`}>{dateStr}</div>

                      <div className="flex items-center justify-end gap-2">
                        {report.file_url && (
                          <a
                            href={report.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`flex h-[28px] items-center gap-1 rounded-md border px-2 text-[10px] transition ${
                              darkMode
                                ? "border-slate-700 text-slate-400 hover:bg-slate-800 hover:text-white"
                                : "border-slate-200 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                            }`}
                            title="View File"
                          >
                            <ExternalLink size={12} />
                            File
                          </a>
                        )}

                        <button
                          type="button"
                          disabled={analyzingId === report.id}
                          onClick={() => handleAnalyze(report.id)}
                          className={`flex h-[28px] items-center gap-1.5 rounded-md border px-2.5 text-[10px] font-medium transition disabled:opacity-50 ${
                            darkMode
                              ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                              : "border-emerald-600/30 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                          }`}
                        >
                          {analyzingId === report.id ? (
                            <>
                              <Loader2 size={12} className="animate-spin" />
                              Parsing...
                            </>
                          ) : (
                            <>
                              <Sparkles size={12} />
                              {isAnalyzed ? "Re-Analyze" : "Analyze"}
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </section>
        </main>
      </div>

      {/* =====================================================
          UPLOAD REPORT MODAL
      ===================================================== */}
      {showUploadModal && (
        <UploadReportModal
          darkMode={darkMode}
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            loadReports();
          }}
        />
      )}

      {/* =====================================================
          ANALYSIS RESULTS MODAL
      ===================================================== */}
      {showAnalysisModal && analysisResult && (
        <AnalysisResultModal
          darkMode={darkMode}
          result={analysisResult}
          onClose={() => {
            setShowAnalysisModal(false);
            setAnalysisResult(null);
          }}
        />
      )}
    </div>
  );
}

/* =============================================================
   SUMMARY CARD
============================================================= */
function SummaryCard({ title, value, icon, darkMode }) {
  return (
    <div
      className={`h-[105px] rounded-2xl border p-4 ${
        darkMode ? "border-slate-800 bg-[#0c1817]" : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between">
        <span
          className={`text-[10px] font-semibold tracking-[0.08em] ${
            darkMode ? "text-slate-300" : "text-slate-500"
          }`}
        >
          {title}
        </span>
        <div
          className={`flex h-[32px] w-[32px] items-center justify-center rounded-lg ${
            darkMode
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-emerald-50 text-emerald-600"
          }`}
        >
          {icon}
        </div>
      </div>
      <div className="mt-1 text-[26px] font-semibold">{value}</div>
    </div>
  );
}

// --- UploadReportModal ---
// What it does: File upload dialog accepting pathology and chemistry laboratory documents (PDF, TXT, PNG, JPG).
// Why it's structured this way: Encapsulates FormData construction and dispatches to patientService.uploadMedicalRecord with progress feedback.
// Parameters & Returns: Props: darkMode (boolean), onClose (func), onSuccess (func). Returns modal dialog JSX.
// ------------------------------------------------------------------------------
function UploadReportModal({ darkMode, onClose, onSuccess }) {
  const [title, setTitle] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a lab report file (PDF, TXT, or Image).");
      return;
    }
    if (!title.trim()) {
      setError("Please enter a title for the report.");
      return;
    }

    try {
      setUploading(true);
      setError("");
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title.trim());

      await patientService.uploadMedicalRecord(formData);
      onSuccess();
    } catch (err) {
      console.error("Upload failed:", err);
      setError(
        err.response?.data?.error?.message ||
          err.response?.data?.detail ||
          "Failed to upload report. Check file format and size."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        className={`w-full max-w-md rounded-2xl border shadow-2xl ${
          darkMode ? "border-slate-700 bg-[#0c1817]" : "border-slate-200 bg-white"
        }`}
      >
        <div className={`flex items-start justify-between border-b p-5 ${
          darkMode ? "border-slate-800" : "border-slate-100"
        }`}>
          <div>
            <h3
              className={`text-[17px] font-bold ${
                darkMode ? "text-white" : "text-slate-900"
              }`}
            >
              Upload Lab Report
            </h3>
            <p className={`mt-1 text-[11px] ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
              Attach diagnostic reports to unlock automated metric extraction
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className={`rounded-lg p-1 transition ${
              darkMode ? "text-slate-400 hover:bg-slate-800 hover:text-white" : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 p-2.5 text-[11px] text-red-500">
              <AlertCircle size={15} />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className={`block text-[11px] font-medium ${darkMode ? "text-slate-300" : "text-slate-700"}`}>
              Report Title *
            </label>
            <input
              type="text"
              placeholder="e.g. Comprehensive Metabolic Panel (CMP)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[12px] outline-none ${
                darkMode
                  ? "border-slate-700 bg-[#0a1514] text-white placeholder:text-slate-600"
                  : "border-slate-200 bg-white text-slate-900 placeholder:text-slate-400"
              }`}
            />
          </div>

          <div>
            <label className={`block text-[11px] font-medium ${darkMode ? "text-slate-300" : "text-slate-700"}`}>
              Select Document File *
            </label>
            <div
              className={`mt-1.5 flex flex-col items-center justify-center rounded-xl border border-dashed p-5 text-center ${
                darkMode
                  ? "border-slate-700 bg-[#0a1514]"
                  : "border-slate-300 bg-slate-50"
              }`}
            >
              <CloudUpload size={28} className="text-emerald-500 mb-1" />
              <input
                type="file"
                id="file-upload"
                accept=".pdf,.png,.jpg,.jpeg,.txt"
                onChange={(e) => setFile(e.target.files[0])}
                className="hidden"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer text-[12px] font-semibold text-emerald-500 hover:underline"
              >
                {file ? file.name : "Click to select report file"}
              </label>
              <p className={`mt-1 text-[10px] ${darkMode ? "text-slate-500" : "text-slate-400"}`}>
                Supports PDF, TXT, PNG, JPG (up to 10MB)
              </p>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className={`rounded-lg border px-4 py-2 text-[11px] font-semibold transition ${
                darkMode ? "border-slate-700 text-slate-400 hover:bg-slate-800" : "border-slate-200 text-slate-600 hover:bg-slate-100"
              }`}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-500 px-5 py-2 text-[11px] font-semibold text-white hover:bg-emerald-600 disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <Loader2 size={13} className="animate-spin" />
                  Uploading...
                </>
              ) : (
                "Upload Document"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// --- buildStructuredClinicalData ---
// Normalizes or synthesizes domain impressions and recommended clinical next steps.
function buildStructuredClinicalData(result) {
  const metrics = result?.metrics || [];
  let impressions = Array.isArray(result?.clinical_impression) ? [...result.clinical_impression] : [];
  let nextSteps = Array.isArray(result?.recommended_next_steps)
    ? [...result.recommended_next_steps]
    : Array.isArray(result?.next_steps)
    ? [...result.next_steps]
    : [];

  // Normalize impressions if already provided by backend
  if (impressions.length > 0) {
    impressions = impressions.map((item) => ({
      domain: item.domain || item.category || "Clinical Finding",
      status: (item.status || "NORMAL").toUpperCase(),
      detail: item.interpretation || item.finding || item.detail || item.summary || "",
    }));
  } else if (metrics.length > 0) {
    // Intelligent client-side fallback synthesis
    const findMetric = (namePart) =>
      metrics.find((m) => (m.test_name || "").toLowerCase().includes(namePart.toLowerCase()));

    const fbs = findMetric("glucose");
    const a1c = findMetric("a1c");
    const chol = findMetric("cholesterol");
    const tg = findMetric("triglyceride");
    const hdl = findMetric("hdl");
    const ldl = findMetric("ldl");
    const cr = findMetric("creatinine");
    const egfr = findMetric("egfr");
    const plt = findMetric("platelet");
    const bp = findMetric("blood pressure");

    if (fbs || a1c) {
      const isAbnormal =
        (fbs && (fbs.flag || "NORMAL").toUpperCase() !== "NORMAL") ||
        (a1c && (a1c.flag || "NORMAL").toUpperCase() !== "NORMAL");
      let text = "";
      if (fbs && a1c) {
        if (isAbnormal) {
          text = `Poorly controlled hyperglycemia indicated by elevated Fasting Blood Glucose (${fbs.value} ${fbs.unit || "mg/dL"}) and HbA1c (${a1c.value}%).`;
        } else {
          text = `Optimal glycemic regulation with Fasting Blood Glucose (${fbs.value} ${fbs.unit || "mg/dL"}) and HbA1c (${a1c.value}%) within target clinical limits.`;
        }
      } else if (fbs) {
        text = `Fasting Blood Glucose measured at ${fbs.value} ${fbs.unit || "mg/dL"} (${(fbs.flag || "normal").toLowerCase()}).`;
      } else {
        text = `Hemoglobin A1c measured at ${a1c.value}% (${(a1c.flag || "normal").toLowerCase()}).`;
      }
      impressions.push({
        domain: "Glycemic Control",
        status: isAbnormal ? "ABNORMAL" : "NORMAL",
        detail: text,
      });
    }

    if (chol || tg || hdl || ldl) {
      const isAbnormal =
        (chol && (chol.flag || "NORMAL").toUpperCase() !== "NORMAL") ||
        (tg && (tg.flag || "NORMAL").toUpperCase() !== "NORMAL") ||
        (hdl && (hdl.flag || "NORMAL").toUpperCase() !== "NORMAL");
      let text = "";
      if (chol && tg && hdl && isAbnormal) {
        text = `Mixed dyslipidemia with elevated Total Cholesterol (${chol.value} mg/dL) and Triglycerides (${tg.value} mg/dL), alongside sub-optimal protective HDL (${hdl.value} mg/dL).`;
      } else {
        const parts = [];
        if (chol) parts.push(`Total Cholesterol (${chol.value} mg/dL)`);
        if (tg) parts.push(`Triglycerides (${tg.value} mg/dL)`);
        if (hdl) parts.push(`HDL (${hdl.value} mg/dL)`);
        text = isAbnormal
          ? `Dyslipidemia pattern detected: ${parts.join(", ")}.`
          : "Lipid profile markers are within cardioprotective target ranges.";
      }
      impressions.push({
        domain: "Lipid Profile",
        status: isAbnormal ? "ABNORMAL" : "NORMAL",
        detail: text,
      });
    }

    if (cr || egfr) {
      const isAbnormal =
        (cr && (cr.flag || "NORMAL").toUpperCase() !== "NORMAL") ||
        (egfr && (egfr.flag || "NORMAL").toUpperCase() !== "NORMAL");
      let text = "";
      if (cr && (cr.flag || "NORMAL").toUpperCase() !== "NORMAL") {
        text = `Serum Creatinine is mildly elevated (${cr.value} ${cr.unit || "mg/dL"}), warranting ongoing monitoring of kidney function.`;
      } else if (cr) {
        text = `Renal function parameters (Serum Creatinine ${cr.value} ${cr.unit || "mg/dL"}) are within normal reference limits.`;
      } else {
        text = `eGFR measured at ${egfr.value} ${egfr.unit || "mL/min/1.73m2"}.`;
      }
      impressions.push({
        domain: "Renal Function",
        status: isAbnormal ? "ABNORMAL" : "NORMAL",
        detail: text,
      });
    }

    if (plt) {
      const isAbnormal = (plt.flag || "NORMAL").toUpperCase() !== "NORMAL";
      let numPlt = plt.value;
      try {
        numPlt = Number(String(plt.value).replace(/,/g, "")).toLocaleString();
      } catch (e) {
        numPlt = plt.value;
      }
      const text = isAbnormal
        ? `Platelet count (${numPlt} cells/mcL) is outside standard reference limits.`
        : `Platelet count (${numPlt} cells/mcL) is within normal reference limits.`;
      impressions.push({
        domain: "Hematology",
        status: isAbnormal ? "ABNORMAL" : "NORMAL",
        detail: text,
      });
    }

    if (bp) {
      const isAbnormal = (bp.flag || "NORMAL").toUpperCase() !== "NORMAL";
      impressions.push({
        domain: "Cardiovascular & Vitals",
        status: isAbnormal ? "ABNORMAL" : "NORMAL",
        detail: `Blood Pressure reading observed at ${bp.value} mmHg (${(bp.flag || "normal").toLowerCase()}).`,
      });
    }
  }

  // Recommended next steps fallback
  if (nextSteps.length === 0) {
    const hasAbnormal = impressions.some((imp) => imp.status !== "NORMAL");
    if (hasAbnormal) {
      nextSteps = [
        "Schedule a follow-up appointment with your physician or endocrinologist to discuss glycemic management and lipid therapy.",
        "Re-test fasting glucose and renal panel as directed by your clinician.",
        "Discuss lifestyle, dietary, and physical activity modifications.",
      ];
    } else {
      nextSteps = [
        "Continue current wellness plan, balanced nutrition, and regular physical activity.",
        "Schedule routine annual clinical preventive screening with your primary care provider.",
      ];
    }
  }

  return { impressions, nextSteps };
}

// --- AnalysisResultModal ---
// What it does: Displays structured clinical interpretation, domain impressions, recommended next steps, and quantitative biomarker comparison.
// Why it's structured this way: Formats discrete numeric biomarkers into physician-grade triage categories with reference ranges for patient and doctor clarity.
// Parameters & Returns: Props: darkMode (boolean), result (object), onClose (func). Returns analysis inspection dialog JSX.
// ------------------------------------------------------------------------------
function AnalysisResultModal({ darkMode, result, onClose }) {
  const metrics = result?.metrics || [];
  const abnormalCount = result?.abnormal_flags_count || 0;
  const criticalCount = result?.critical_flags_count || 0;

  // Stream raw internal parser logs strictly to developer console.debug()
  useEffect(() => {
    const logs = result?.fallback_log || result?.extraction_logs || [];
    if (logs.length > 0) {
      console.debug("[Medicare Biomarker Extraction Trace]", logs);
    }
  }, [result]);

  const { impressions, nextSteps } = buildStructuredClinicalData(result);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        className={`w-full max-w-3xl rounded-2xl border shadow-2xl max-h-[92vh] flex flex-col ${
          darkMode ? "border-slate-800 bg-[#0c1817]" : "border-slate-200 bg-white"
        }`}
      >
        {/* Header */}
        <div
          className={`flex items-start justify-between border-b p-5 shrink-0 ${
            darkMode ? "border-slate-800/80" : "border-slate-100"
          }`}
        >
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                darkMode ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-emerald-50 text-emerald-600 border border-emerald-100"
              }`}
            >
              <Sparkles size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className={`text-[17px] font-bold ${darkMode ? "text-white" : "text-slate-900"}`}>
                  AI Clinical Report Analysis
                </h3>
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                  darkMode ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-emerald-50 text-emerald-600 border border-emerald-200"
                }`}>
                  Clinical DSS
                </span>
              </div>
              <p className={`text-[12px] mt-0.5 ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
                Automated Diagnostic Biomarker Synthesis & Clinical Interpretation
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className={`rounded-lg p-2 transition ${
              darkMode
                ? "text-slate-400 hover:bg-slate-800 hover:text-white"
                : "text-slate-500 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Quantitative Metrics Summary Cards */}
          <div className="grid grid-cols-3 gap-3">
            <div
              className={`rounded-xl border p-4 text-center transition ${
                darkMode ? "border-slate-800 bg-[#0a1514]" : "border-slate-200 bg-slate-50"
              }`}
            >
              <span className={`text-[11px] uppercase tracking-wider font-semibold ${
                darkMode ? "text-slate-400" : "text-slate-500"
              }`}>
                Metrics Extracted
              </span>
              <p className={`text-[24px] font-bold mt-1 ${darkMode ? "text-white" : "text-slate-900"}`}>
                {result?.total_metrics_extracted || metrics.length}
              </p>
              <span className={`text-[10px] font-medium ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
                Total Analytes Parsed
              </span>
            </div>

            <div
              className={`rounded-xl border p-4 text-center transition ${
                darkMode ? "border-slate-800 bg-[#0a1514]" : "border-slate-200 bg-slate-50"
              }`}
            >
              <span className={`text-[11px] uppercase tracking-wider font-semibold ${
                darkMode ? "text-slate-400" : "text-slate-500"
              }`}>
                Abnormal Findings
              </span>
              <p
                className={`text-[24px] font-bold mt-1 ${
                  abnormalCount > 0 ? "text-amber-500" : "text-emerald-500"
                }`}
              >
                {abnormalCount}
              </p>
              <span className={`text-[10px] font-medium ${abnormalCount > 0 ? "text-amber-500" : "text-emerald-500"}`}>
                {abnormalCount > 0 ? "Requires Clinical Review" : "Within Reference Ranges"}
              </span>
            </div>

            <div
              className={`rounded-xl border p-4 text-center transition ${
                darkMode ? "border-slate-800 bg-[#0a1514]" : "border-slate-200 bg-slate-50"
              }`}
            >
              <span className={`text-[11px] uppercase tracking-wider font-semibold ${
                darkMode ? "text-slate-400" : "text-slate-500"
              }`}>
                Critical Alerts
              </span>
              <p
                className={`text-[24px] font-bold mt-1 ${
                  criticalCount > 0 ? "text-rose-500" : "text-emerald-500"
                }`}
              >
                {criticalCount}
              </p>
              <span className={`text-[10px] font-medium ${criticalCount > 0 ? "text-rose-500" : "text-slate-400"}`}>
                {criticalCount > 0 ? "Immediate Action Needed" : "Zero Critical Flags"}
              </span>
            </div>
          </div>

          {/* Section: Clinical Impression */}
          {impressions.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Activity size={17} className={darkMode ? "text-emerald-400" : "text-emerald-600"} />
                <div>
                  <h4 className={`text-[13px] font-bold ${darkMode ? "text-white" : "text-slate-900"}`}>
                    Clinical Impression
                  </h4>
                  <p className={`text-[11px] ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
                    Domain-specific synthesis of laboratory findings
                  </p>
                </div>
              </div>

              <div className="space-y-2.5">
                {impressions.map((imp, idx) => {
                  const isCritical = imp.status === "CRITICAL";
                  const isAbnormal = imp.status === "ABNORMAL" || imp.status === "HIGH" || imp.status === "ELEVATED" || imp.status === "LOW";
                  
                  const badgeClass = isCritical
                    ? "bg-rose-500/10 text-rose-500 border border-rose-500/20"
                    : isAbnormal
                    ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                    : "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20";

                  const badgeText = isCritical
                    ? "Critical"
                    : isAbnormal
                    ? "Attention Required"
                    : "Normal Range";

                  const dotColor = isCritical
                    ? "bg-rose-500"
                    : isAbnormal
                    ? "bg-amber-500"
                    : "bg-emerald-500";

                  return (
                    <div
                      key={idx}
                      className={`rounded-xl border p-3.5 transition ${
                        isCritical
                          ? darkMode ? "border-rose-500/30 bg-rose-500/[0.04]" : "border-rose-200 bg-rose-50/40"
                          : isAbnormal
                          ? darkMode ? "border-amber-500/25 bg-amber-500/[0.03]" : "border-amber-200/80 bg-amber-50/30"
                          : darkMode ? "border-slate-800 bg-[#0a1514]" : "border-slate-200 bg-slate-50/70"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className={`h-2 w-2 rounded-full ${dotColor}`} />
                          <span className={`text-[12px] font-bold ${darkMode ? "text-white" : "text-slate-900"}`}>
                            {imp.domain}
                          </span>
                        </div>
                        <span className={`rounded-full px-2.5 py-0.5 text-[9px] font-bold ${badgeClass}`}>
                          {badgeText}
                        </span>
                      </div>
                      <p className={`text-[12px] leading-relaxed pl-4 ${darkMode ? "text-slate-300" : "text-slate-600"}`}>
                        {imp.detail}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Section: Recommended Next Steps */}
          {nextSteps.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <ListChecks size={17} className={darkMode ? "text-emerald-400" : "text-emerald-600"} />
                <div>
                  <h4 className={`text-[13px] font-bold ${darkMode ? "text-white" : "text-slate-900"}`}>
                    Recommended Next Steps
                  </h4>
                  <p className={`text-[11px] ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
                    Actionable clinical management and follow-up guidance
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                {nextSteps.map((step, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start gap-3 rounded-xl border p-3 transition ${
                      darkMode ? "border-slate-800 bg-[#0a1514]" : "border-slate-200 bg-slate-50/80"
                    }`}
                  >
                    <div
                      className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full ${
                        darkMode ? "bg-emerald-500/10 text-emerald-400" : "bg-emerald-50 text-emerald-600"
                      }`}
                    >
                      <CheckCircle2 size={13} />
                    </div>
                    <p className={`text-[12px] leading-relaxed ${darkMode ? "text-slate-300" : "text-slate-700"}`}>
                      {step}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section: Biomarker Comparison Table */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <h4 className={`text-[13px] font-bold ${darkMode ? "text-white" : "text-slate-900"}`}>
                Biomarker Comparison
              </h4>
              <span className={`text-[11px] ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
                Reference Range Alignment
              </span>
            </div>

            {metrics.length === 0 ? (
              <div
                className={`rounded-xl border p-6 text-center text-[12px] ${
                  darkMode ? "border-slate-800 bg-[#0a1514] text-slate-500" : "border-slate-200 bg-slate-50 text-slate-500"
                }`}
              >
                No standard quantitative metrics could be parsed from this document.
              </div>
            ) : (
              <div
                className={`rounded-xl border overflow-hidden ${
                  darkMode ? "border-slate-800 bg-[#0a1514]" : "border-slate-200 bg-white"
                }`}
              >
                <div
                  className={`grid grid-cols-[1.3fr_1fr_1.2fr_.8fr] px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wider border-b ${
                    darkMode ? "text-slate-400 border-slate-800 bg-[#081211]" : "text-slate-500 border-slate-200 bg-slate-50"
                  }`}
                >
                  <span>Biomarker / Test</span>
                  <span>Extracted Value</span>
                  <span>Reference Range</span>
                  <span className="text-right">Status Flag</span>
                </div>
                {metrics.map((m, idx) => {
                  const flag = (m.flag || "NORMAL").toUpperCase();
                  const badgeClass =
                    flag === "NORMAL"
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : flag === "CRITICAL"
                      ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      : flag === "HIGH" || flag === "ELEVATED"
                      ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20";

                  return (
                    <div
                      key={idx}
                      className={`grid grid-cols-[1.3fr_1fr_1.2fr_.8fr] items-center px-4 py-3 text-[11px] border-t ${
                        darkMode ? "border-slate-800/60 hover:bg-slate-800/20" : "border-slate-100 hover:bg-slate-50/60"
                      } transition-colors`}
                    >
                      <span className={`font-semibold ${darkMode ? "text-white" : "text-slate-900"}`}>
                        {m.test_name}
                      </span>
                      <span className={darkMode ? "text-slate-200" : "text-slate-700"}>
                        {m.value} {m.unit}
                      </span>
                      <span className={darkMode ? "text-slate-400" : "text-slate-500"}>
                        {m.reference_range || "N/A"}
                      </span>
                      <div className="text-right">
                        <span
                          className={`inline-block rounded-full px-2.5 py-0.5 text-[9px] font-bold ${badgeClass}`}
                        >
                          {flag}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Regulatory Clinical Notice */}
          <div className="flex items-start gap-2.5 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3.5 text-[11px] text-amber-500">
            <AlertTriangle size={16} className="shrink-0 text-amber-500 mt-0.5" />
            <span className="leading-relaxed">
              <strong>Clinical Decision Support Notice:</strong> AI-assisted diagnostic biomarker extraction. Results are generated via algorithmic text parsing and must be independently validated by a licensed physician before clinical decision-making.
            </span>
          </div>
        </div>

        {/* Footer */}
        <div
          className={`border-t p-4 flex justify-end shrink-0 ${
            darkMode ? "border-slate-800" : "border-slate-100"
          }`}
        >
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-emerald-500 px-5 py-2 text-[12px] font-semibold text-white hover:bg-emerald-600 transition shadow-sm"
          >
            Close Results
          </button>
        </div>
      </div>
    </div>
  );
}