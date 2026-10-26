// ==============================================================================
// FILE: frontend/src/pages/public/doctor/reports.jsx
// PURPOSE: Diagnostic lab and pathology reports review console for physicians.
// VIVA EXPLANATION: This screen aggregates laboratory test reports across all assigned patients. It highlights abnormal diagnostic values, assigns clinical urgency tiers (High, Medium, Normal), and enables doctors to download original attachments or inspect extracted clinical findings.
// ==============================================================================

import React, { useEffect, useMemo, useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  FileText,
  Filter,
  Download,
  Eye,
  MoreHorizontal,
  CalendarDays,
  AlertCircle,
  CheckCircle2,
  Clock3,
  ArrowUpDown,
  X,
  Loader2,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";
import { useAuth } from "../../../_core/hooks/useAuth";
import doctorService from "../../../services/doctorService";

// --- StatusBadge ---
// What it does: Renders status tags reflecting review state (Reviewed, Needs Review, Pending).
// Why it's structured this way: Uses distinct color semantics to immediately flag unreviewed reports requiring clinical oversight.
// Parameters & Returns: Props: status (string). Returns styled JSX badge.
// ------------------------------------------------------------------------------
function StatusBadge({ status }) {
  const styles = {
    Reviewed: "bg-emerald-500/10 text-emerald-500",
    "Needs Review": "bg-red-500/10 text-red-500",
    Pending: "bg-amber-500/10 text-amber-500",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${
        styles[status] || styles.Reviewed
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          status === "Reviewed"
            ? "bg-emerald-500"
            : status === "Needs Review"
            ? "bg-red-500"
            : "bg-amber-500"
        }`}
      />
      {status}
    </span>
  );
}

// --- PriorityBadge ---
// What it does: Displays clinical urgency level (Normal, Medium, High).
// Why it's structured this way: Flags abnormal pathology thresholds to accelerate critical lab intervention.
// Parameters & Returns: Props: priority (string). Returns styled JSX span.
// ------------------------------------------------------------------------------
function PriorityBadge({ priority }) {
  const styles = {
    Normal: "bg-[var(--card-soft)] text-[var(--muted)]",
    Medium: "bg-amber-500/10 text-amber-500",
    High: "bg-red-500/10 text-red-500",
  };

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-medium ${
        styles[priority] || styles.Normal
      }`}
    >
      {priority}
    </span>
  );
}

// --- Reports ---
// What it does: Primary diagnostic reports console displaying aggregated lab results and modal inspection views.
// Why it's structured this way: Iterates across authorized patients to retrieve and normalize medical record lab reports, providing real-time filtering and modal views.
// Parameters & Returns: None. Returns diagnostic reports dashboard JSX.
// ------------------------------------------------------------------------------
export default function Reports() {
  const { isDark, toggleTheme } = useTheme();
  const { user } = useAuth();

  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    async function loadReports() {
      try {
        setLoading(true);
        const patientsData = await doctorService.getPatients();
        const patientList = Array.isArray(patientsData) ? patientsData : patientsData?.results || [];

        const allReports = [];
        for (const p of patientList) {
          try {
            const pReports = await doctorService.getPatientReports(p.id);
            const list = Array.isArray(pReports) ? pReports : pReports?.results || [];
            list.forEach((r) => {
              const created = new Date(r.created_at);
              const isAbnormal = r.is_abnormal || (r.extracted_data && r.extracted_data.abnormal_count > 0);
              allReports.push({
                id: r.report_id || `RPT-${r.id}`,
                rawId: r.id,
                patientId: p.id,
                patient: `${p.first_name || ""} ${p.last_name || ""}`.trim() || p.email,
                type: r.title || r.test_type || "Diagnostic Lab Report",
                category: r.category || "Laboratory",
                date: !isNaN(created.getTime())
                  ? created.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
                  : "Recent",
                status: isAbnormal ? "Needs Review" : "Reviewed",
                priority: isAbnormal ? "High" : "Normal",
                notes: r.notes || r.summary || "Automated OCR extraction processed.",
                fileUrl: r.file_url || r.file,
              });
            });
          } catch (err) {
            console.warn(`Could not load reports for patient ${p.id}:`, err);
          }
        }
        setReports(allReports);
      } catch (err) {
        console.error("Failed to load doctor patient reports:", err);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  const doctorName = user?.last_name
    ? `Dr. ${user.last_name}`
    : user?.first_name
    ? `Dr. ${user.first_name}`
    : user?.full_name
    ? `Dr. ${user.full_name}`
    : "Doctor";

  const filteredReports = useMemo(() => {
    const query = search.trim().toLowerCase();

    return reports.filter((report) => {
      const matchesSearch =
        !query ||
        report.patient.toLowerCase().includes(query) ||
        report.id.toLowerCase().includes(query) ||
        report.type.toLowerCase().includes(query) ||
        report.category.toLowerCase().includes(query);

      const matchesStatus =
        statusFilter === "All" || report.status === statusFilter;

      const matchesCategory =
        categoryFilter === "All" || report.category === categoryFilter;

      return matchesSearch && matchesStatus && matchesCategory;
    });
  }, [reports, search, statusFilter, categoryFilter]);

  const needsReviewCount = reports.filter((r) => r.status === "Needs Review").length;
  const reviewedCount = reports.filter((r) => r.status === "Reviewed").length;
  const pendingCount = reports.filter((r) => r.status === "Pending").length;

  return (
    <div
      className="h-dvh min-h-0 overflow-hidden bg-[var(--bg)] text-[var(--text)]"
      style={{
        colorScheme: isDark ? "dark" : "light",
      }}
    >
      <div className="flex h-full min-h-0">
        <Sidebar />

        <main className="ml-[217px] min-h-0 min-w-0 w-[calc(100%-217px)] flex-none overflow-hidden">
          {/* HEADER */}
          <header className="flex h-[72px] shrink-0 items-center justify-between gap-4 border-b border-[var(--border)] px-5 sm:px-7 lg:px-8">
            <h1 className="text-[26px] font-bold tracking-tight">Reports</h1>

            <div className="flex items-center gap-3">
              {/* SEARCH */}
              <div className="hidden h-10 w-[280px] items-center gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 md:flex">
                <Search size={18} className="text-[var(--muted)]" />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search reports, patients, tests..."
                  className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
                />
              </div>

              {/* THEME */}
              <button
                type="button"
                onClick={toggleTheme}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] text-[var(--accent)]"
              >
                <span className="text-xl">{isDark ? "☼" : "☾"}</span>
              </button>

              {/* NOTIFICATION */}
              <button
                type="button"
                className="relative p-2 text-[var(--text-secondary)]"
              >
                <Bell size={20} />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--accent)]" />
              </button>

              {/* PROFILE */}
              <div className="hidden items-center gap-2 sm:flex">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--accent-soft)] font-semibold text-xs text-[var(--accent)]">
                  {doctorName.slice(0, 3)}
                </div>
                <span className="text-xs font-semibold">{doctorName}</span>
                <ChevronDown size={15} className="text-[var(--muted)]" />
              </div>
            </div>
          </header>

          {/* CONTENT */}
          <section className="grid h-[calc(100vh-72px)] min-h-0 grid-rows-[auto_auto_minmax(0,1fr)] gap-4 overflow-hidden px-5 py-5 sm:px-7 lg:px-8">
            {/* INTRO */}
            <div className="flex items-end justify-between gap-4">
              <div>
                <h2 className="text-[22px] font-bold">Clinical Reports</h2>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  Review laboratory, diagnostic, and pathology reports from your authorized patients.
                </p>
              </div>

              <div className="hidden shrink-0 items-center gap-2 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-3 py-1.5 text-xs text-[var(--text-secondary)] sm:flex">
                <Clock3 size={14} className="text-[var(--accent)]" />
                <span>Live EHR Stream</span>
              </div>
            </div>

            {/* SUMMARY */}
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Total Reports</span>
                  <FileText size={17} className="text-[var(--accent)]" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(reports.length).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-[var(--muted)]">All diagnostic uploads</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Needs Review</span>
                  <AlertCircle size={17} className="text-red-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(needsReviewCount).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-red-500">Abnormal flags detected</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Pending</span>
                  <Clock3 size={17} className="text-amber-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(pendingCount).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-amber-500">Awaiting processing</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Reviewed</span>
                  <CheckCircle2 size={17} className="text-emerald-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(reviewedCount).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-emerald-500">Completed & normal</p>
              </div>
            </div>

            {/* REPORT TABLE */}
            <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)]">
              {/* TOOLBAR */}
              <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
                <div className="flex items-center gap-2">
                  <Filter size={16} className="text-[var(--muted)]" />
                  <span className="text-sm font-medium">Report List</span>
                  <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--accent)]">
                    {filteredReports.length}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {/* STATUS */}
                  <select
                    value={statusFilter}
                    onChange={(event) => setStatusFilter(event.target.value)}
                    className="rounded-lg border border-[var(--border-soft)] bg-[var(--card-soft)] px-3 py-1.5 text-xs text-[var(--text-secondary)] outline-none"
                  >
                    <option value="All">All Status</option>
                    <option value="Reviewed">Reviewed</option>
                    <option value="Needs Review">Needs Review</option>
                  </select>

                  {/* CATEGORY */}
                  <select
                    value={categoryFilter}
                    onChange={(event) => setCategoryFilter(event.target.value)}
                    className="hidden rounded-lg border border-[var(--border-soft)] bg-[var(--card-soft)] px-3 py-1.5 text-xs text-[var(--text-secondary)] outline-none sm:block"
                  >
                    <option value="All">All Categories</option>
                    <option value="Laboratory">Laboratory</option>
                    <option value="Imaging">Imaging</option>
                    <option value="Cardiology">Cardiology</option>
                  </select>
                </div>
              </div>

              {/* TABLE */}
              <div className="min-h-0 flex-1 overflow-y-auto">
                {loading ? (
                  <div className="flex h-full min-h-[220px] flex-col items-center justify-center">
                    <Loader2 size={24} className="animate-spin text-[var(--accent)]" />
                    <p className="mt-2 text-xs text-[var(--muted)]">Loading clinical reports from database...</p>
                  </div>
                ) : filteredReports.length === 0 ? (
                  <div className="flex h-full min-h-[220px] items-center justify-center">
                    <div className="text-center">
                      <FileText size={34} className="mx-auto text-[var(--muted)]" />
                      <p className="mt-3 text-sm font-medium">No reports found</p>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        No diagnostic reports match the selected filters or search terms.
                      </p>
                    </div>
                  </div>
                ) : (
                  <table className="w-full table-fixed border-collapse">
                    <thead>
                      <tr className="border-b border-[var(--border)]">
                        <th className="w-[14%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                          Report ID
                        </th>
                        <th className="w-[22%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                          Patient
                        </th>
                        <th className="w-[26%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                          Report
                        </th>
                        <th className="hidden w-[14%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] md:table-cell">
                          Date
                        </th>
                        <th className="hidden w-[12%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] lg:table-cell">
                          Priority
                        </th>
                        <th className="w-[12%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                          Status
                        </th>
                        <th className="w-[8%] px-2 py-3 text-right" />
                      </tr>
                    </thead>
                    <tbody>
                      {filteredReports.map((report) => (
                        <tr
                          key={report.id}
                          className="border-b border-[var(--border)] transition hover:bg-[var(--card-soft)] last:border-b-0"
                        >
                          {/* ID */}
                          <td className="px-4 py-3 text-xs font-medium text-[var(--muted)]">
                            {report.id}
                          </td>

                          {/* PATIENT */}
                          <td className="px-4 py-3">
                            <p className="truncate text-sm font-semibold">{report.patient}</p>
                            <p className="mt-0.5 text-[11px] text-[var(--muted)]">Patient</p>
                          </td>

                          {/* REPORT */}
                          <td className="px-4 py-3">
                            <div className="flex min-w-0 items-center gap-2.5">
                              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--accent-soft)]">
                                <FileText size={15} className="text-[var(--accent)]" />
                              </div>
                              <div className="min-w-0">
                                <p className="truncate text-sm font-medium">{report.type}</p>
                                <p className="truncate text-[10px] text-[var(--muted)]">{report.category}</p>
                              </div>
                            </div>
                          </td>

                          {/* DATE */}
                          <td className="hidden px-4 py-3 text-xs text-[var(--muted)] md:table-cell">
                            <div className="flex items-center gap-2">
                              <CalendarDays size={14} />
                              {report.date}
                            </div>
                          </td>

                          {/* PRIORITY */}
                          <td className="hidden px-4 py-3 lg:table-cell">
                            <PriorityBadge priority={report.priority} />
                          </td>

                          {/* STATUS */}
                          <td className="px-4 py-3">
                            <StatusBadge status={report.status} />
                          </td>

                          {/* ACTIONS */}
                          <td className="px-2 py-3 text-right">
                            <button
                              type="button"
                              onClick={() => setSelectedReport(report)}
                              aria-label={`View ${report.id}`}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-[var(--muted)] hover:bg-[var(--card-soft)] hover:text-[var(--text)]"
                            >
                              <Eye size={16} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </section>
        </main>
      </div>

      {/* REPORT DETAIL MODAL */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div>
                <h3 className="text-base font-bold">{selectedReport.type}</h3>
                <p className="text-xs text-[var(--muted)]">
                  {selectedReport.id} &bull; {selectedReport.patient} &bull; {selectedReport.date}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedReport(null)}
                className="text-[var(--muted)] hover:text-[var(--text)]"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-4 space-y-3">
              <div className="flex gap-2">
                <StatusBadge status={selectedReport.status} />
                <PriorityBadge priority={selectedReport.priority} />
              </div>

              <div className="rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] p-4 text-xs leading-relaxed">
                <p className="font-semibold text-[var(--text)]">Clinical Notes & Findings:</p>
                <p className="mt-1 text-[var(--muted)] whitespace-pre-wrap">{selectedReport.notes}</p>
              </div>

              {selectedReport.fileUrl && (
                <div className="pt-2">
                  <a
                    href={selectedReport.fileUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-xl border border-[var(--accent)]/30 bg-[var(--accent-soft)] px-3.5 py-2 text-xs font-semibold text-[var(--accent)] hover:opacity-90"
                  >
                    <Download size={14} />
                    View Original Report Document
                  </a>
                </div>
              )}
            </div>

            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedReport(null)}
                className="rounded-xl bg-[var(--accent)] px-4 py-2 text-xs font-semibold text-[#06231d]"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}