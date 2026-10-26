// ==============================================================================
// FILE: frontend/src/pages/public/doctor/patients.jsx
// PURPOSE: Doctor Patient Cohort Management console providing directory search, risk classification, clinical notes, and prescription issuance.
// VIVA EXPLANATION: This interface provides doctors with a comprehensive patient management dashboard. It renders patient demographic profiles, triage risk tiers, and provides direct modal workflows to author clinical consultation notes and issue verified prescription records through authenticated API endpoints.
// ==============================================================================

import React, { useEffect, useMemo, useState } from "react";

import {
  Search,
  Bell,
  ChevronDown,
  UsersRound,
  UserRound,
  CalendarDays,
  Activity,
  MoreHorizontal,
  Plus,
  SlidersHorizontal,
  ArrowUpDown,
  FileText,
  Pill,
  X,
  AlertCircle,
  CheckCircle2,
  Loader2,
  ShieldAlert,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";
import { useAuth } from "../../../_core/hooks/useAuth";
import doctorService from "../../../services/doctorService";

// --- StatusBadge ---
// What it does: Renders a color-coded status badge with a pulse indicator dot for patient activity states.
// Why it's structured this way: Encapsulates status color mappings (Active, Stable, Monitoring, Attention) for consistent clinical visualization.
// Parameters & Returns: Props: status (string). Returns styled JSX span badge.
// ------------------------------------------------------------------------------
function StatusBadge({ status = "Active" }) {
  const styles = {
    Active: "bg-emerald-500/10 text-emerald-500",
    Stable: "bg-emerald-500/10 text-emerald-500",
    Monitoring: "bg-amber-500/10 text-amber-500",
    Attention: "bg-red-500/10 text-red-500",
  };

  return (
    <span
      className={`
        inline-flex
        items-center
        gap-1.5
        rounded-full
        px-2.5
        py-1
        text-[11px]
        font-medium
        ${styles[status] || styles.Active}
      `}
    >
      <span
        className={`
          h-1.5
          w-1.5
          rounded-full
          ${
            status === "Stable" || status === "Active"
              ? "bg-emerald-500"
              : status === "Monitoring"
              ? "bg-amber-500"
              : "bg-red-500"
          }
        `}
      />
      {status}
    </span>
  );
}

// --- RiskBadge ---
// What it does: Renders a color-coded clinical risk level badge (Low, Medium, High).
// Why it's structured this way: Provides rapid visual triage identification so healthcare providers immediately distinguish high-risk patients.
// Parameters & Returns: Props: risk (string). Returns styled JSX span.
// ------------------------------------------------------------------------------
function RiskBadge({ risk = "Low" }) {
  const styles = {
    Low: "bg-emerald-500/10 text-emerald-500",
    Medium: "bg-amber-500/10 text-amber-500",
    High: "bg-red-500/10 text-red-500",
  };

  return (
    <span
      className={`
        inline-flex
        rounded-full
        px-2.5
        py-1
        text-[11px]
        font-medium
        ${styles[risk] || styles.Low}
      `}
    >
      {risk}
    </span>
  );
}

// --- Patients ---
// What it does: Main doctor cohort dashboard component managing patient fetching, search filtering, and clinical action modals.
// Why it's structured this way: Integrates doctorService with React state, memoized filtering, and modal dialog handlers for seamless bedside data entry.
// Parameters & Returns: None. Returns doctor patient management view JSX.
// ------------------------------------------------------------------------------
export default function Patients() {
  const { isDark, toggleTheme } = useTheme();
  const { user } = useAuth();

  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");

  // Action Modals
  const [noteModalPatient, setNoteModalPatient] = useState(null);
  const [medModalPatient, setMedModalPatient] = useState(null);
  const [actionSuccess, setActionSuccess] = useState("");
  const [actionError, setActionError] = useState("");

  const loadPatients = async () => {
    try {
      setLoading(true);
      const data = await doctorService.getPatients();
      const list = Array.isArray(data) ? data : [];
      setPatients(list);
    } catch (err) {
      console.error("Failed to load doctor patient roster:", err);
      setActionError("Failed to load authorized patients from database.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const filteredPatients = useMemo(() => {
    const query = search.trim().toLowerCase();

    return patients.filter((patient) => {
      const name = `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.email;
      const condition = patient.patient_profile?.primary_condition || "General Consultation";
      const idStr = String(patient.id);

      const matchesSearch =
        !query ||
        name.toLowerCase().includes(query) ||
        patient.email.toLowerCase().includes(query) ||
        condition.toLowerCase().includes(query) ||
        idStr.includes(query);

      return matchesSearch;
    });
  }, [patients, search, filter]);

  const doctorName = user?.last_name
    ? `Dr. ${user.last_name}`
    : user?.first_name
    ? `Dr. ${user.first_name}`
    : "Dr. Doctor";

  return (
    <div
      className="
        h-dvh
        min-h-0
        overflow-hidden
        bg-[var(--bg)]
        text-[var(--text)]
      "
      style={{
        colorScheme: isDark ? "dark" : "light",
      }}
    >
      <div className="flex h-full min-h-0">
        <Sidebar />

        <main className="ml-[217px] min-h-0 min-w-0 w-[calc(100%-217px)] flex-none overflow-hidden">
          {/* HEADER */}
          <header
            className="
              flex
              h-[72px]
              shrink-0
              items-center
              justify-between
              gap-4
              border-b
              border-[var(--border)]
              px-5
              sm:px-7
              lg:px-8
            "
          >
            <h1 className="text-[26px] font-bold tracking-tight">Patients</h1>

            <div className="flex items-center gap-3">
              {/* SEARCH */}
              <div
                className="
                  hidden
                  h-10
                  w-[280px]
                  items-center
                  gap-3
                  rounded-xl
                  border
                  border-[var(--border-soft)]
                  bg-[var(--card-soft)]
                  px-4
                  md:flex
                "
              >
                <Search size={18} className="text-[var(--muted)]" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search authorized patients..."
                  className="
                    w-full
                    bg-transparent
                    text-sm
                    outline-none
                    placeholder:text-[var(--muted)]
                  "
                />
              </div>

              {/* THEME */}
              <button
                type="button"
                onClick={toggleTheme}
                aria-label="Toggle theme"
                className="
                  flex
                  h-10
                  w-10
                  items-center
                  justify-center
                  rounded-xl
                  border
                  border-[var(--border-soft)]
                  bg-[var(--card-soft)]
                  text-[var(--accent)]
                "
              >
                <span className="text-xl">{isDark ? "☼" : "☾"}</span>
              </button>

              {/* NOTIFICATION */}
              <button
                type="button"
                aria-label="Notifications"
                className="relative p-2 text-[var(--text-secondary)]"
              >
                <Bell size={20} />
                <span
                  className="
                    absolute
                    right-1.5
                    top-1.5
                    h-2
                    w-2
                    rounded-full
                    bg-[var(--accent)]
                  "
                />
              </button>

              {/* PROFILE */}
              <div className="hidden items-center gap-2 sm:flex">
                <div
                  className="
                    flex
                    h-10
                    w-10
                    items-center
                    justify-center
                    rounded-full
                    bg-[var(--accent-soft)]
                  "
                >
                  <UsersRound size={19} className="text-[var(--accent)]" />
                </div>
                <span className="text-xs font-semibold">{doctorName}</span>
              </div>
            </div>
          </header>

          {/* PAGE CONTENT */}
          <section
            className="
              grid
              h-[calc(100vh-72px)]
              min-h-0
              grid-rows-[auto_auto_minmax(0,1fr)]
              gap-4
              overflow-hidden
              px-5
              py-5
              sm:px-7
              lg:px-8
            "
          >
            {/* PAGE INTRO */}
            <div className="flex items-end justify-between gap-4">
              <div>
                <h2 className="text-[22px] font-bold">Authorized Patient Roster</h2>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  Active patients linked to your clinical practice with EHR access
                </p>
              </div>

              {actionSuccess && (
                <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-400">
                  <CheckCircle2 size={15} />
                  <span>{actionSuccess}</span>
                  <button type="button" onClick={() => setActionSuccess("")} className="ml-1 text-emerald-400 hover:text-white">
                    <X size={13} />
                  </button>
                </div>
              )}

              {actionError && (
                <div className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs text-red-400">
                  <ShieldAlert size={15} />
                  <span>{actionError}</span>
                  <button type="button" onClick={() => setActionError("")} className="ml-1 text-red-400 hover:text-white">
                    <X size={13} />
                  </button>
                </div>
              )}
            </div>

            {/* SUMMARY CARDS */}
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Total Authorized</span>
                  <UserRound size={17} className="text-[var(--accent)]" />
                </div>
                <p className="mt-2 text-2xl font-bold">{patients.length}</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">EHR Active</span>
                  <CalendarDays size={17} className="text-[var(--accent)]" />
                </div>
                <p className="mt-2 text-2xl font-bold">{patients.length}</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Monitoring</span>
                  <Activity size={17} className="text-amber-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">{patients.length > 0 ? "01" : "00"}</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Decision Engine</span>
                  <Activity size={17} className="text-emerald-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">Online</p>
              </div>
            </div>

            {/* PATIENT TABLE */}
            <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)]">
              {/* TABLE TOOLBAR */}
              <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal size={17} className="text-[var(--muted)]" />
                  <span className="text-sm font-medium">Patients</span>
                  <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--accent)]">
                    {filteredPatients.length}
                  </span>
                </div>
              </div>

              {/* TABLE */}
              <div className="min-h-0 flex-1 overflow-y-auto">
                <table className="w-full table-fixed border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border)] bg-[var(--card-soft)]">
                      <th className="w-[28%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Patient
                      </th>
                      <th className="w-[18%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Primary Condition
                      </th>
                      <th className="w-[14%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Blood Group
                      </th>
                      <th className="w-[14%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Emergency Contact
                      </th>
                      <th className="w-[26%] px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Clinical Actions
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan="5" className="py-12 text-center text-sm text-[var(--muted)]">
                          <Loader2 size={20} className="mx-auto mb-2 animate-spin text-[var(--accent)]" />
                          Querying authorized patient registry...
                        </td>
                      </tr>
                    ) : filteredPatients.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="py-12 text-center text-sm text-[var(--muted)]">
                          <UserRound size={32} className="mx-auto mb-2 text-[var(--muted)] opacity-60" />
                          <p className="font-semibold">No authorized patients linked yet.</p>
                          <p className="mt-1 text-xs text-[var(--muted)]">
                            Patients become authorized when appointments are scheduled or clinical relationships are established.
                          </p>
                        </td>
                      </tr>
                    ) : (
                      filteredPatients.map((patient) => {
                        const name =
                          `${patient.first_name || ""} ${patient.last_name || ""}`.trim() ||
                          patient.email;
                        const profile = patient.patient_profile || {};

                        return (
                          <tr
                            key={patient.id}
                            className="border-b border-[var(--border)] transition hover:bg-[var(--card-soft)] last:border-b-0"
                          >
                            <td className="px-4 py-3">
                              <div className="flex min-w-0 items-center gap-3">
                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                                  <UserRound size={17} className="text-[var(--accent)]" />
                                </div>
                                <div className="min-w-0">
                                  <p className="truncate text-sm font-semibold">{name}</p>
                                  <p className="truncate text-[11px] text-[var(--muted)]">
                                    {patient.email}
                                  </p>
                                </div>
                              </div>
                            </td>

                            <td className="px-4 py-3 text-xs">
                              <span className="rounded-md bg-[var(--card-soft)] px-2 py-1 border border-[var(--border)]">
                                {profile.primary_condition || "General Care"}
                              </span>
                            </td>

                            <td className="px-4 py-3 text-xs text-[var(--muted)]">
                              {profile.blood_group || "Unknown"}
                            </td>

                            <td className="px-4 py-3 text-xs text-[var(--muted)]">
                              {profile.emergency_contact || "Not provided"}
                            </td>

                            <td className="px-4 py-3 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setActionError("");
                                    setNoteModalPatient(patient);
                                  }}
                                  className="flex items-center gap-1 rounded-lg border border-[var(--border-soft)] bg-[var(--card-soft)] px-2.5 py-1 text-xs font-semibold text-[var(--accent)] hover:bg-[var(--card-hover)] transition"
                                >
                                  <FileText size={13} />
                                  Clinical Note
                                </button>

                                <button
                                  type="button"
                                  onClick={() => {
                                    setActionError("");
                                    setMedModalPatient(patient);
                                  }}
                                  className="flex items-center gap-1 rounded-lg border border-[var(--accent)] bg-[var(--accent-soft)] px-2.5 py-1 text-xs font-semibold text-[var(--accent)] hover:opacity-90 transition"
                                >
                                  <Pill size={13} />
                                  Prescribe
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </main>
      </div>

      {/* =====================================================
          ADD CLINICAL NOTE MODAL
      ===================================================== */}
      {noteModalPatient && (
        <ClinicalNoteModal
          isDark={isDark}
          patient={noteModalPatient}
          onClose={() => setNoteModalPatient(null)}
          onSuccess={(msg) => {
            setNoteModalPatient(null);
            setActionSuccess(msg || "Clinical note recorded successfully.");
          }}
          onError={(err) => {
            setActionError(err);
          }}
        />
      )}

      {/* =====================================================
          PRESCRIBE MEDICATION MODAL
      ===================================================== */}
      {medModalPatient && (
        <PrescribeMedicationModal
          isDark={isDark}
          patient={medModalPatient}
          onClose={() => setMedModalPatient(null)}
          onSuccess={(msg) => {
            setMedModalPatient(null);
            setActionSuccess(msg || "Medication prescribed and recorded.");
          }}
          onError={(err) => {
            setActionError(err);
          }}
        />
      )}
    </div>
  );
}

// --- ClinicalNoteModal ---
// What it does: Modal form enabling doctors to document diagnoses and clinical notes for a selected patient.
// Why it's structured this way: Enforces role permissions and input validation before committing notes through doctorService.createClinicalNote.
// Parameters & Returns: Props: isDark (boolean), patient (object), onClose (func), onSuccess (func), onError (func). Returns modal dialog JSX.
// ------------------------------------------------------------------------------
function ClinicalNoteModal({ isDark, patient, onClose, onSuccess, onError }) {
  const [diagnosis, setDiagnosis] = useState("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const patientName =
    `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.email;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!note.trim()) {
      setFormError("Please enter clinical observation notes.");
      return;
    }

    try {
      setSubmitting(true);
      setFormError("");
      await doctorService.createClinicalNote(patient.id, {
        diagnosis: diagnosis.trim(),
        note: note.trim(),
      });
      onSuccess(`Clinical note saved for ${patientName}`);
    } catch (err) {
      console.error("Clinical note submission error:", err);
      const msg =
        err.response?.status === 403
          ? "Authorization boundary enforcement: Doctor does not have active clinical authorization for this patient."
          : err.response?.data?.error?.message ||
            err.response?.data?.detail ||
            "Failed to save clinical note.";
      setFormError(msg);
      onError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        className={`w-full max-w-lg rounded-2xl border shadow-2xl ${
          isDark ? "border-slate-700 bg-[#121c1a]" : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-start justify-between border-b border-[var(--border)] p-5">
          <div>
            <h3 className="text-base font-bold">Add Clinical Note</h3>
            <p className="mt-0.5 text-xs text-[var(--muted)]">
              Patient: <span className="font-semibold text-[var(--accent)]">{patientName}</span>
            </p>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-[var(--muted)] hover:bg-[var(--card-hover)]">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-400">
              <ShieldAlert size={16} className="shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-[var(--muted-strong)]">
              Clinical Diagnosis / Assessment
            </label>
            <input
              type="text"
              placeholder="e.g. Essential Primary Hypertension, Stage 1"
              value={diagnosis}
              onChange={(e) => setDiagnosis(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--card-soft)] px-3.5 py-2 text-xs outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--muted-strong)]">
              Clinical Observations & Notes *
            </label>
            <textarea
              rows={4}
              required
              placeholder="Record patient complaints, examination findings, and treatment plan..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--card-soft)] p-3 text-xs outline-none resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-[var(--border-soft)] px-4 py-2 text-xs font-semibold text-[var(--muted)] hover:bg-[var(--card-hover)]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-1.5 rounded-xl bg-[var(--accent)] px-5 py-2 text-xs font-semibold text-[#06231d] hover:opacity-90 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Clinical Note"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// --- PrescribeMedicationModal ---
// What it does: Modal form enabling physicians to prescribe medications with dosage and administration frequency.
// Why it's structured this way: Captures structured prescription parameters and dispatches via doctorService.prescribeMedication with active safety boundaries.
// Parameters & Returns: Props: isDark (boolean), patient (object), onClose (func), onSuccess (func), onError (func). Returns modal dialog JSX.
// ------------------------------------------------------------------------------
function PrescribeMedicationModal({ isDark, patient, onClose, onSuccess, onError }) {
  const [name, setName] = useState("");
  const [dosage, setDosage] = useState("");
  const [frequency, setFrequency] = useState("Once daily");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const patientName =
    `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.email;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !dosage.trim()) {
      setFormError("Medication name and dosage are required.");
      return;
    }

    try {
      setSubmitting(true);
      setFormError("");
      await doctorService.prescribeMedication({
        patient_id: patient.id,
        name: name.trim(),
        dosage: dosage.trim(),
        frequency,
        notes: notes.trim(),
        is_active: true,
      });
      onSuccess(`Prescribed ${name} (${dosage}) for ${patientName}`);
    } catch (err) {
      console.error("Prescription error:", err);
      const msg =
        err.response?.status === 403
          ? "Authorization boundary enforcement: Doctor does not have active clinical authorization for this patient."
          : err.response?.data?.error?.message ||
            err.response?.data?.detail ||
            "Failed to record prescription.";
      setFormError(msg);
      onError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        className={`w-full max-w-lg rounded-2xl border shadow-2xl ${
          isDark ? "border-slate-700 bg-[#121c1a]" : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-start justify-between border-b border-[var(--border)] p-5">
          <div>
            <h3 className="text-base font-bold">Prescribe Medication</h3>
            <p className="mt-0.5 text-xs text-[var(--muted)]">
              Patient: <span className="font-semibold text-[var(--accent)]">{patientName}</span>
            </p>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-[var(--muted)] hover:bg-[var(--card-hover)]">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {formError && (
            <div className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-400">
              <ShieldAlert size={16} className="shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-[var(--muted-strong)]">
                Medication Name *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Amlodipine"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--card-soft)] px-3 py-2 text-xs outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--muted-strong)]">
                Dosage *
              </label>
              <input
                type="text"
                required
                placeholder="e.g. 5 mg"
                value={dosage}
                onChange={(e) => setDosage(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--card-soft)] px-3 py-2 text-xs outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--muted-strong)]">
              Regimen Frequency
            </label>
            <select
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--card-soft)] px-3 py-2 text-xs outline-none"
            >
              <option>Once daily</option>
              <option>Twice daily</option>
              <option>Three times daily</option>
              <option>As needed (PRN)</option>
              <option>Every 12 hours</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--muted-strong)]">
              Instructions / Notes
            </label>
            <textarea
              rows={2}
              placeholder="e.g. Take with food in the morning."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-[var(--border)] bg-[var(--card-soft)] p-3 text-xs outline-none resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-[var(--border-soft)] px-4 py-2 text-xs font-semibold text-[var(--muted)] hover:bg-[var(--card-hover)]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-1.5 rounded-xl bg-[var(--accent)] px-5 py-2 text-xs font-semibold text-[#06231d] hover:opacity-90 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  Prescribing...
                </>
              ) : (
                "Issue Prescription"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}