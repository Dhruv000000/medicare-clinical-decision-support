// ==============================================================================
// FILE: frontend/src/pages/public/doctor/clinicalnotes.jsx
// PURPOSE: Doctor Clinical Notes interface for reviewing historical patient observations and recording signed diagnostic assessments.
// VIVA EXPLANATION: This view handles electronic health record (EHR) progress notes. Doctors can review previous longitudinal notes written for their authorized patient roster, search and filter entries, and author new notes with clinical categories and diagnostic findings.
// ==============================================================================

import React, { useEffect, useMemo, useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  FileText,
  UserRound,
  CalendarDays,
  Clock3,
  Plus,
  MoreHorizontal,
  Edit3,
  Eye,
  CheckCircle2,
  FilePenLine,
  Stethoscope,
  Save,
  X,
  Loader2,
  AlertCircle,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";
import { useAuth } from "../../../_core/hooks/useAuth";
import doctorService from "../../../services/doctorService";

// --- StatusBadge ---
// What it does: Renders a visual tag distinguishing signed progress notes from preliminary drafts.
// Why it's structured this way: Clearly communicates the legal and verification status of clinical documentation.
// Parameters & Returns: Props: status (string). Returns styled JSX span badge.
// ------------------------------------------------------------------------------
function StatusBadge({ status }) {
  if (status === "Signed") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-[10px] font-medium text-emerald-500">
        <CheckCircle2 size={12} />
        Signed
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-[10px] font-medium text-amber-500">
      <FilePenLine size={12} />
      Draft
    </span>
  );
}

// --- ClinicalNotes ---
// What it does: Master clinical observation documentation console managing patient notes lists and note creation dialogs.
// Why it's structured this way: Fetches patient rosters and aggregated EHR notes, supporting live filtering, full inspection modal, and note creation.
// Parameters & Returns: None. Returns clinical progress note dashboard JSX.
// ------------------------------------------------------------------------------
export default function ClinicalNotes() {
  const { isDark, toggleTheme } = useTheme();
  const { user } = useAuth();

  const [notes, setNotes] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");

  // Create Note Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [noteContent, setNoteContent] = useState("");
  const [savingNote, setSavingNote] = useState(false);
  const [modalError, setModalError] = useState("");

  // View Note Modal State
  const [viewingNote, setViewingNote] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const patientList = await doctorService.getPatients();
      const validPatients = Array.isArray(patientList) ? patientList : patientList?.results || [];
      setPatients(validPatients);

      if (validPatients.length > 0 && !selectedPatientId) {
        setSelectedPatientId(String(validPatients[0].id));
      }

      const allNotes = [];
      for (const p of validPatients) {
        try {
          const pNotes = await doctorService.getPatientNotes(p.id);
          const list = Array.isArray(pNotes) ? pNotes : [];
          list.forEach((n) => {
            const created = new Date(n.created_at);
            allNotes.push({
              id: `CN-${n.id}`,
              rawId: n.id,
              patientId: p.id,
              patient: `${p.first_name || ""} ${p.last_name || ""}`.trim() || p.email,
              patientEmail: p.email,
              date: !isNaN(created.getTime())
                ? created.toLocaleDateString("en-US", { day: "2-digit", month: "short", year: "numeric" })
                : "Recent",
              time: !isNaN(created.getTime())
                ? created.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
                : "10:00 AM",
              rawDate: created,
              type: n.diagnosis || "Observation",
              title: n.diagnosis ? `${n.diagnosis} Review` : "Clinical Observation Note",
              status: "Signed",
              preview: n.note,
            });
          });
        } catch (err) {
          console.warn(`Could not load notes for patient ${p.id}:`, err);
        }
      }
      setNotes(allNotes);
    } catch (err) {
      console.error("Failed to load clinical notes or patients:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateNote = async (e) => {
    e.preventDefault();
    if (!selectedPatientId || !noteContent.trim()) {
      setModalError("Please select a patient and enter clinical note content.");
      return;
    }

    try {
      setSavingNote(true);
      setModalError("");
      await doctorService.createClinicalNote(selectedPatientId, {
        note: noteContent.trim(),
        diagnosis: diagnosis.trim() || "General Consultation",
      });

      setIsCreateOpen(false);
      setDiagnosis("");
      setNoteContent("");
      await loadData();
    } catch (err) {
      console.error("Failed to create clinical note:", err);
      setModalError(
        err.response?.data?.message ||
        err.response?.data?.error?.message ||
        "Failed to save clinical note. Ensure doctor has active authorization for this patient."
      );
    } finally {
      setSavingNote(false);
    }
  };

  const doctorName = user?.last_name
    ? `Dr. ${user.last_name}`
    : user?.first_name
    ? `Dr. ${user.first_name}`
    : user?.full_name
    ? `Dr. ${user.full_name}`
    : "Doctor";

  const todayDateStr = new Date().toLocaleDateString("en-US", { day: "2-digit", month: "short", year: "numeric" });
  const todayNotesCount = notes.filter((n) => n.date === todayDateStr).length;

  const filteredNotes = useMemo(() => {
    const query = search.trim().toLowerCase();

    return notes.filter((note) => {
      const matchesSearch =
        !query ||
        note.patient.toLowerCase().includes(query) ||
        note.title.toLowerCase().includes(query) ||
        note.type.toLowerCase().includes(query) ||
        note.id.toLowerCase().includes(query);

      const matchesFilter = filter === "All" || note.status === filter;

      return matchesSearch && matchesFilter;
    });
  }, [notes, search, filter]);

  return (
    <div
      className="h-dvh min-h-0 overflow-hidden medicare-doctor-shell bg-[var(--bg)] text-[var(--text)]"
      style={{ colorScheme: isDark ? "dark" : "light" }}
    >
      <div className="flex h-full min-h-0">
        {/* GLOBAL SIDEBAR */}
        <Sidebar />

        <main className="ml-[217px] min-h-0 min-w-0 w-[calc(100%-217px)] flex-none overflow-hidden">
          {/* HEADER */}
          <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-[var(--border)] px-5 sm:px-7 lg:px-8">
            <h1 className="text-[26px] font-bold tracking-tight">
              Clinical Notes
            </h1>

            <div className="flex items-center gap-3">
              {/* SEARCH */}
              <div className="hidden h-10 w-[280px] items-center gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 md:flex">
                <Search size={18} className="text-[var(--muted)]" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search notes, patients, diagnosis..."
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

              {/* NOTIFICATIONS */}
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

          {/* PAGE */}
          <section className="grid h-[calc(100vh-72px)] min-h-0 grid-rows-[auto_auto_minmax(0,1fr)] gap-4 overflow-hidden px-5 py-5 sm:px-7 lg:px-8">
            {/* INTRO */}
            <div className="flex items-end justify-between gap-4">
              <div>
                <h2 className="text-[22px] font-bold">
                  Patient Clinical Notes
                </h2>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  Create, review, and manage verified EHR clinical documentation.
                </p>
              </div>

              <button
                type="button"
                onClick={() => setIsCreateOpen(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-[#06231d] shadow-sm transition hover:opacity-95"
              >
                <Plus size={17} />
                New Clinical Note
              </button>
            </div>

            {/* SUMMARY CARDS */}
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              {/* TOTAL */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Total Notes</span>
                  <FileText size={17} className="text-[var(--accent)]" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(notes.length).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-[var(--muted)]">
                  Recorded in database
                </p>
              </div>

              {/* TODAY */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Today's Notes</span>
                  <CalendarDays size={17} className="text-blue-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(todayNotesCount).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-blue-500">
                  Logged today
                </p>
              </div>

              {/* DRAFTS */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Drafts</span>
                  <Edit3 size={17} className="text-amber-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">00</p>
                <p className="mt-1 text-[10px] text-amber-500">
                  Awaiting review
                </p>
              </div>

              {/* SIGNED */}
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Signed</span>
                  <CheckCircle2 size={17} className="text-emerald-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(notes.length).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-emerald-500">
                  Completed & verified
                </p>
              </div>
            </div>

            {/* NOTES PANEL */}
            <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)]">
              {/* TOOLBAR */}
              <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
                <div className="flex items-center gap-2">
                  <FileText size={16} className="text-[var(--muted)]" />
                  <span className="text-sm font-medium">Recent Notes</span>
                  <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--accent)]">
                    {filteredNotes.length}
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  {["All", "Signed"].map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => setFilter(item)}
                      className={`
                        rounded-lg px-3 py-1.5 text-xs font-medium transition
                        ${
                          filter === item
                            ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                            : "text-[var(--muted)] hover:bg-[var(--card-soft)]"
                        }
                      `}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>

              {/* TABLE */}
              <div className="min-h-0 flex-1 overflow-y-auto">
                {loading ? (
                  <div className="flex h-full min-h-[200px] flex-col items-center justify-center">
                    <Loader2 size={24} className="animate-spin text-[var(--accent)]" />
                    <p className="mt-2 text-xs text-[var(--muted)]">Loading clinical notes from database...</p>
                  </div>
                ) : filteredNotes.length === 0 ? (
                  <div className="flex h-full min-h-[220px] items-center justify-center">
                    <div className="text-center">
                      <FileText size={34} className="mx-auto text-[var(--muted)]" />
                      <p className="mt-3 text-sm font-medium">No clinical notes found</p>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        Click "New Clinical Note" above to record a consultation note for an authorized patient.
                      </p>
                    </div>
                  </div>
                ) : (
                  <table className="w-full table-fixed border-collapse">
                    <thead>
                      <tr className="border-b border-[var(--border)]">
                        <th className="w-[22%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                          Patient
                        </th>
                        <th className="w-[28%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                          Clinical Note
                        </th>
                        <th className="hidden w-[14%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] sm:table-cell">
                          Diagnosis
                        </th>
                        <th className="hidden w-[15%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] md:table-cell">
                          Date & Time
                        </th>
                        <th className="hidden w-[11%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)] lg:table-cell">
                          Status
                        </th>
                        <th className="w-[10%] px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                          Action
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredNotes.map((note) => (
                        <tr
                          key={note.id}
                          className="border-b border-[var(--border)] transition hover:bg-[var(--card-soft)] last:border-b-0"
                        >
                          {/* PATIENT */}
                          <td className="px-4 py-3">
                            <div className="flex min-w-0 items-center gap-3">
                              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                                <UserRound size={16} className="text-[var(--accent)]" />
                              </div>
                              <div className="min-w-0">
                                <p className="truncate text-sm font-semibold">{note.patient}</p>
                                <p className="mt-0.5 text-[10px] text-[var(--muted)]">{note.id}</p>
                              </div>
                            </div>
                          </td>

                          {/* NOTE */}
                          <td className="px-4 py-3">
                            <p className="truncate text-sm font-medium">{note.title}</p>
                            <p className="mt-1 truncate text-[10px] text-[var(--muted)]">{note.preview}</p>
                          </td>

                          {/* TYPE / DIAGNOSIS */}
                          <td className="hidden px-4 py-3 sm:table-cell">
                            <span className="rounded-lg bg-[var(--card-soft)] px-2.5 py-1 text-[10px] font-medium text-[var(--text-secondary)]">
                              {note.type}
                            </span>
                          </td>

                          {/* DATE */}
                          <td className="hidden px-4 py-3 md:table-cell">
                            <div className="flex items-center gap-2">
                              <CalendarDays size={13} className="text-[var(--muted)]" />
                              <div>
                                <p className="text-xs">{note.date}</p>
                                <p className="mt-0.5 flex items-center gap-1 text-[10px] text-[var(--muted)]">
                                  <Clock3 size={10} />
                                  {note.time}
                                </p>
                              </div>
                            </div>
                          </td>

                          {/* STATUS */}
                          <td className="hidden px-4 py-3 lg:table-cell">
                            <StatusBadge status={note.status} />
                          </td>

                          {/* ACTIONS */}
                          <td className="px-4 py-3 text-right">
                            <button
                              type="button"
                              onClick={() => setViewingNote(note)}
                              title="View note"
                              className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-[var(--muted)] hover:bg-[var(--accent-soft)] hover:text-[var(--accent)]"
                            >
                              <Eye size={15} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              {/* FOOTER */}
              <div className="flex shrink-0 items-center justify-between border-t border-[var(--border)] px-4 py-2.5">
                <div className="flex items-center gap-2 text-[10px] text-[var(--muted)]">
                  <Save size={13} className="text-emerald-500" />
                  EHR notes are saved directly to PostgreSQL clinical store.
                </div>
                <div className="flex items-center gap-2 text-[10px] text-[var(--muted)]">
                  <Clock3 size={12} />
                  Connected &bull; Doctor Decision Support
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>

      {/* CREATE NOTE MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <h3 className="text-lg font-bold">New Clinical Observation Note</h3>
              <button
                type="button"
                onClick={() => setIsCreateOpen(false)}
                className="text-[var(--muted)] hover:text-[var(--text)]"
              >
                <X size={18} />
              </button>
            </div>

            {modalError && (
              <div className="mt-4 flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-500">
                <AlertCircle size={15} className="shrink-0" />
                {modalError}
              </div>
            )}

            <form onSubmit={handleCreateNote} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[var(--text)]">
                  Authorized Patient
                </label>
                <select
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(e.target.value)}
                  className="mt-1.5 w-full rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-3 py-2 text-xs outline-none"
                >
                  {patients.length === 0 ? (
                    <option value="">No authorized patients found</option>
                  ) : (
                    patients.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.first_name || p.last_name
                          ? `${p.first_name || ""} ${p.last_name || ""}`.trim()
                          : p.email}{" "}
                        (ID: {p.id})
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[var(--text)]">
                  Working Diagnosis / Clinical Category
                </label>
                <input
                  type="text"
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="e.g. Hypertension Review, Type 2 Diabetes, Upper Respiratory"
                  className="mt-1.5 w-full rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-3 py-2 text-xs outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[var(--text)]">
                  Clinical Observation & Findings
                </label>
                <textarea
                  rows={4}
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  placeholder="Enter detailed clinical observation, examination findings, medication adherence, and plan..."
                  className="mt-1.5 w-full rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] p-3 text-xs outline-none"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="rounded-xl border border-[var(--border-soft)] px-4 py-2 text-xs font-medium text-[var(--muted)] hover:bg-[var(--card-soft)]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingNote || patients.length === 0}
                  className="rounded-xl bg-[var(--accent)] px-4 py-2 text-xs font-semibold text-[#06231d] transition hover:opacity-90 disabled:opacity-50"
                >
                  {savingNote ? "Saving Note..." : "Sign & Record Note"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* VIEW NOTE MODAL */}
      {viewingNote && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div>
                <h3 className="text-base font-bold">{viewingNote.title}</h3>
                <p className="text-xs text-[var(--muted)]">
                  Patient: {viewingNote.patient} &bull; {viewingNote.date} {viewingNote.time}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setViewingNote(null)}
                className="text-[var(--muted)] hover:text-[var(--text)]"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-4 space-y-3">
              <div className="flex gap-2">
                <span className="rounded-lg bg-[var(--card-soft)] px-2.5 py-1 text-xs font-medium text-[var(--text-secondary)]">
                  Category: {viewingNote.type}
                </span>
                <StatusBadge status={viewingNote.status} />
              </div>

              <div className="rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] p-4 text-xs leading-relaxed">
                <p className="whitespace-pre-wrap">{viewingNote.preview}</p>
              </div>
            </div>

            <div className="mt-5 flex justify-end">
              <button
                type="button"
                onClick={() => setViewingNote(null)}
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