// ==============================================================================
// FILE: frontend/src/pages/public/patient/medicine.jsx
// PURPOSE: Patient medication schedule manager, dosage tracker, and OpenFDA safety alert viewer.
// VIVA EXPLANATION: Implements the patient pharmacotherapy management interface. Displays active/inactive medications from /medicines/, allows recording self-administered prescriptions, and integrates on-demand OpenFDA drug label warnings and adverse reaction reports.
// ==============================================================================

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Sidebar from "../patient/sidebar";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Bell,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  Clock3,
  ExternalLink,
  Info,
  Loader2,
  Moon,
  Pill,
  Plus,
  Search,
  ShieldAlert,
  Sun,
  X,
} from "lucide-react";
import { useAuth } from "../../../_core/hooks/useAuth";
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

function useDarkMode() {
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window === "undefined") return true;
    const saved = localStorage.getItem("medicare-theme");
    if (saved === "dark") return true;
    if (saved === "light") return false;
    return true;
  });

  useEffect(() => {
    localStorage.setItem("medicare-theme", darkMode ? "dark" : "light");
    document.documentElement.classList.toggle("dark", darkMode);
    document.documentElement.style.colorScheme = darkMode ? "dark" : "light";
    document.body.style.background = darkMode ? "#0b1413" : "#f8faf9";
  }, [darkMode]);

  return [darkMode, setDarkMode];
}

function Header({ darkMode, setDarkMode }) {
  const { user } = useAuth();
  const patientName = user
    ? `${user.first_name || ""} ${user.last_name || ""}`.trim() || user.email.split("@")[0]
    : "Patient";

  return (
    <header
      className={`flex h-[78px] shrink-0 items-center justify-between border-b px-8 ${
        darkMode ? "border-slate-800 bg-[#111c1b]" : "border-slate-100 bg-white"
      }`}
    >
      <div>
        <h1
          className={`text-[26px] font-bold tracking-[-0.7px] ${
            darkMode ? "text-white" : "text-emerald-950"
          }`}
        >
          Medications & Prescriptions
        </h1>
        <p
          className={`mt-1 text-[12px] ${
            darkMode ? "text-slate-500" : "text-slate-500"
          }`}
        >
          Manage clinical prescriptions, dosing schedules, and OpenFDA safety warnings
        </p>
      </div>

      <div className="flex items-center gap-4">
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

        <div className="flex items-center gap-3">
          <div
            className={`h-10 w-10 overflow-hidden rounded-full ${
              darkMode ? "bg-slate-700" : "bg-slate-200"
            }`}
          >
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
              alt={patientName}
              className="h-full w-full object-cover"
            />
          </div>

          <span
            className={`text-[14px] font-semibold ${
              darkMode ? "text-slate-200" : "text-slate-800"
            }`}
          >
            {patientName}
          </span>

          <ChevronDown
            size={16}
            className={darkMode ? "text-slate-400" : "text-slate-600"}
          />
        </div>
      </div>
    </header>
  );
}

function StatCard({ darkMode, label, value, suffix, icon, warning = false }) {
  return (
    <div
      className={`rounded-[14px] border p-4 ${
        darkMode ? "border-slate-800 bg-[#15211f]" : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between">
        <div
          className={`flex h-8 w-8 items-center justify-center rounded-lg ${
            warning
              ? darkMode
                ? "bg-amber-500/10"
                : "bg-amber-50"
              : darkMode
              ? "bg-emerald-500/10"
              : "bg-emerald-50"
          }`}
        >
          {React.cloneElement(icon, {
            size: 15,
            className: warning ? "text-amber-500" : "text-emerald-500",
          })}
        </div>
      </div>

      <p
        className={`mt-3 text-[10px] font-semibold tracking-wider uppercase ${
          darkMode ? "text-slate-400" : "text-slate-500"
        }`}
      >
        {label}
      </p>

      <div className="mt-1 flex items-baseline gap-1">
        <span
          className={`text-[23px] font-semibold ${
            darkMode ? "text-white" : "text-emerald-950"
          }`}
        >
          {value}
        </span>

        {suffix && (
          <span
            className={`text-[10px] ${
              darkMode ? "text-slate-500" : "text-slate-500"
            }`}
          >
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}

function CurrentMedicationCard({
  medication,
  darkMode,
  onOpenFda,
}) {
  const [active, setActive] = useState(medication.is_active !== false);

  return (
    <div
      className={`rounded-xl border p-3.5 transition hover:border-emerald-500/30 ${
        darkMode ? "border-slate-800 bg-[#101918]" : "border-slate-100 bg-slate-50/70"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <div
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${
              darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
            }`}
          >
            <Pill size={16} className="text-emerald-500" />
          </div>

          <div className="min-w-0">
            <p
              className={`truncate text-[11px] font-semibold ${
                darkMode ? "text-slate-100" : "text-slate-800"
              }`}
            >
              {medication.name}
            </p>

            <p
              className={`mt-0.5 text-[9px] ${
                darkMode ? "text-slate-400" : "text-slate-500"
              }`}
            >
              {medication.dosage || medication.dose || "Standard dose"} ·{" "}
              {medication.frequency || "Daily"}
            </p>
          </div>
        </div>

        <span
          className={`rounded-full px-2.5 py-0.5 text-[8px] font-semibold ${
            active
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : "bg-slate-800 text-slate-400 border border-slate-700"
          }`}
        >
          {active ? "Active" : "Completed"}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 border-t border-slate-800/40 pt-2.5">
        <div>
          <p className="text-[8px] font-medium uppercase tracking-wider text-slate-500">
            Frequency / Schedule
          </p>
          <p
            className={`mt-0.5 text-[10px] ${
              darkMode ? "text-slate-300" : "text-slate-700"
            }`}
          >
            {medication.frequency || "As directed"}
          </p>
        </div>

        <div>
          <p className="text-[8px] font-medium uppercase tracking-wider text-slate-500">
            Prescriber
          </p>
          <p
            className={`mt-0.5 truncate text-[10px] ${
              darkMode ? "text-slate-300" : "text-slate-700"
            }`}
          >
            {medication.prescribed_by_name ||
              medication.prescribedBy ||
              "Primary Care Physician"}
          </p>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between border-t border-slate-800/40 pt-2">
        <span
          className={`text-[9px] ${
            darkMode ? "text-slate-500" : "text-slate-400"
          }`}
        >
          {medication.notes ? `Note: ${medication.notes.slice(0, 30)}...` : "Clinical Prescription"}
        </span>

        <button
          type="button"
          onClick={() => onOpenFda(medication.name)}
          className="flex items-center gap-1 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 text-[9px] font-semibold text-emerald-400 transition hover:bg-emerald-500/20"
        >
          <ShieldAlert size={11} />
          FDA Safety
        </button>
      </div>
    </div>
  );
}

function AddMedicationModal({ darkMode, doctors, onClose, onAdd }) {
  const [name, setName] = useState("");
  const [dosage, setDosage] = useState("");
  const [frequency, setFrequency] = useState("Once daily");
  const [doctorId, setDoctorId] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please specify the medicine name.");
      return;
    }
    if (!dosage.trim()) {
      setError("Please specify the dosage (e.g. 500mg).");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      await onAdd({
        name: name.trim(),
        dosage: dosage.trim(),
        frequency,
        notes: notes.trim(),
        is_active: true,
        prescribed_by: doctorId ? parseInt(doctorId, 10) : null,
      });
      onClose();
    } catch (err) {
      console.error("Failed to add medication:", err);
      setError(
        err.response?.data?.detail ||
          err.response?.data?.name?.[0] ||
          "Failed to save medication to database."
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        className={`w-full max-w-md rounded-2xl border shadow-2xl ${
          darkMode ? "border-slate-700 bg-[#15211f]" : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-start justify-between border-b border-slate-800 p-5">
          <div>
            <h3
              className={`text-[16px] font-bold ${
                darkMode ? "text-white" : "text-emerald-950"
              }`}
            >
              Add Medicine
            </h3>
            <p className="mt-1 text-[11px] text-slate-400">
              Record a new medication in your health profile
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-3.5">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 p-2.5 text-[11px] text-red-400">
              <AlertCircle size={15} />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-[11px] font-medium text-slate-300">
              Medicine Name *
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Metformin, Lisinopril, Atorvastatin"
              className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[11px] outline-none ${
                darkMode
                  ? "border-slate-700 bg-[#101918] text-slate-200 placeholder:text-slate-600"
                  : "border-slate-200 bg-white text-slate-700 placeholder:text-slate-400"
              }`}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-300">
                Dosage *
              </label>
              <input
                value={dosage}
                onChange={(e) => setDosage(e.target.value)}
                placeholder="e.g. 500 mg"
                className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[11px] outline-none ${
                  darkMode
                    ? "border-slate-700 bg-[#101918] text-slate-200 placeholder:text-slate-600"
                    : "border-slate-200 bg-white text-slate-700 placeholder:text-slate-400"
                }`}
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-300">
                Frequency
              </label>
              <select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[11px] outline-none ${
                  darkMode
                    ? "border-slate-700 bg-[#101918] text-slate-200"
                    : "border-slate-200 bg-white text-slate-700"
                }`}
              >
                <option>Once daily</option>
                <option>Twice daily</option>
                <option>Three times daily</option>
                <option>As needed (PRN)</option>
                <option>Weekly</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-300">
              Prescribed By (Doctor)
            </label>
            <select
              value={doctorId}
              onChange={(e) => setDoctorId(e.target.value)}
              className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[11px] outline-none ${
                darkMode
                  ? "border-slate-700 bg-[#101918] text-slate-200"
                  : "border-slate-200 bg-white text-slate-700"
              }`}
            >
              <option value="">Select doctor (or self-reported)</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.specialization})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-300">
              Clinical Notes / Instructions
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Take with food in the morning."
              className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[11px] outline-none resize-none ${
                darkMode
                  ? "border-slate-700 bg-[#101918] text-slate-200 placeholder:text-slate-600"
                  : "border-slate-200 bg-white text-slate-700 placeholder:text-slate-400"
              }`}
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-700 px-4 py-2 text-[11px] font-semibold text-slate-400 hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !name.trim()}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-500 px-5 py-2 text-[11px] font-semibold text-white hover:bg-emerald-600 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 size={13} className="animate-spin" />
                  Saving...
                </>
              ) : (
                "Add Medicine"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// --- OpenFdaModal ---
// What it does: Modal dialog executing real-time OpenFDA queries to show official drug label warnings and adverse events.
// Why it's structured this way: Encapsulates network loading and error states to display structured FDA safety reports without navigating away from the page.
// Parameters & Returns: { drugName, darkMode, onClose } -> Modal dialog JSX element.
// ------------------------------------------------------------------------------
function OpenFdaModal({ drugName, darkMode, onClose }) {
  const [loading, setLoading] = useState(true);
  const [safetyData, setSafetyData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchSafety() {
      try {
        setLoading(true);
        setError("");
        const data = await patientService.getDrugReactions(drugName, 8);
        setSafetyData(data);
      } catch (err) {
        console.error("OpenFDA fetch error:", err);
        setError(
          err.response?.data?.detail ||
            "Unable to query OpenFDA safety database for this substance."
        );
      } finally {
        setLoading(false);
      }
    }
    if (drugName) {
      fetchSafety();
    }
  }, [drugName]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div
        className={`w-full max-w-xl rounded-2xl border shadow-2xl max-h-[85vh] flex flex-col ${
          darkMode ? "border-slate-700 bg-[#111c1b]" : "border-slate-200 bg-white"
        }`}
      >
        <div className="flex items-start justify-between border-b border-slate-800 p-5 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
              <ShieldAlert size={20} />
            </div>
            <div>
              <h3
                className={`text-[17px] font-bold ${
                  darkMode ? "text-white" : "text-slate-900"
                }`}
              >
                OpenFDA Pharmacological Safety
              </h3>
              <p className="text-[11px] text-slate-400">
                Official FDA drug label warnings and reported adverse reactions for{" "}
                <span className="font-semibold text-emerald-400 uppercase">
                  {drugName}
                </span>
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <Loader2 size={24} className="animate-spin text-emerald-400 mb-2" />
              <p className="text-[12px]">
                Connecting to OpenFDA drug surveillance database...
              </p>
            </div>
          ) : error ? (
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-[12px] text-red-400">
              <div className="flex items-center gap-2 font-semibold mb-1">
                <AlertCircle size={16} />
                <span>Lookup Unsuccessful</span>
              </div>
              <p>{error}</p>
            </div>
          ) : safetyData ? (
            <>
              {/* Boxed Warnings Section */}
              {safetyData.has_boxed_warning &&
              safetyData.boxed_warnings &&
              safetyData.boxed_warnings.length > 0 ? (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
                  <div className="flex items-center gap-2 text-red-400 font-bold text-[12px] mb-2">
                    <AlertTriangle size={16} />
                    <span>FDA BOXED WARNING (BLACK BOX)</span>
                  </div>
                  <div className="space-y-2 text-[11px] text-red-200/90 leading-relaxed">
                    {safetyData.boxed_warnings.slice(0, 2).map((w, idx) => (
                      <p key={idx} className="bg-red-950/40 p-2.5 rounded-lg border border-red-500/20">
                        {w}
                      </p>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-[11px] text-emerald-400">
                  <CheckCircle2 size={16} />
                  <span>No FDA Black Box Warnings found for this drug formulation.</span>
                </div>
              )}

              {/* Adverse Reactions List */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-[12px] font-bold text-slate-200 uppercase tracking-wide">
                    Reported Adverse Reactions
                  </h4>
                  {safetyData.total_reactions > 0 && (
                    <span className="text-[10px] text-slate-400">
                      {safetyData.total_reactions.toLocaleString()} surveillance reports
                    </span>
                  )}
                </div>

                {safetyData.adverse_reactions && safetyData.adverse_reactions.length > 0 ? (
                  <div className="grid grid-cols-2 gap-2">
                    {safetyData.adverse_reactions.map((r, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded-lg border border-slate-800 bg-[#0c1817] px-3 py-2 text-[11px]"
                      >
                        <span className="font-medium text-slate-300 uppercase">
                          {r.reaction}
                        </span>
                        <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[9px] text-emerald-400 font-mono">
                          {r.reported_cases} cases
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-[11px] text-slate-500 italic">
                    No high-frequency adverse reactions cataloged for this term.
                  </p>
                )}
              </div>

              {/* Precautions */}
              {safetyData.precautions && safetyData.precautions.length > 0 && (
                <div className="rounded-xl border border-slate-800 bg-[#0c1817] p-3.5">
                  <h4 className="text-[11px] font-semibold text-slate-300 uppercase tracking-wide mb-1.5">
                    Clinical Precautions
                  </h4>
                  <div className="space-y-1.5 text-[11px] text-slate-400">
                    {safetyData.precautions.slice(0, 2).map((p, idx) => (
                      <p key={idx} className="line-clamp-3">
                        • {p}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              <div className="flex items-start gap-2 rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-[10px] text-slate-400">
                <Info size={14} className="shrink-0 text-slate-500 mt-0.5" />
                <span>
                  Source: U.S. Food and Drug Administration (FDA) adverse event reporting system (FAERS). Consult your licensed physician before altering your medication regimen.
                </span>
              </div>
            </>
          ) : null}
        </div>

        <div className="border-t border-slate-800 p-4 flex justify-end shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg bg-emerald-500 px-5 py-2 text-[11px] font-semibold text-white hover:bg-emerald-600"
          >
            Close Safety Report
          </button>
        </div>
      </div>
    </div>
  );
}

// --- Medications ---
// What it does: Main medication overview component fetching patient prescriptions, filtering active drugs, and managing modals.
// Why it's structured this way: Combines schedule cards with interactive safety lookups to promote medication adherence.
// Parameters & Returns: Props (none) -> Rendered medications portal view JSX.
// ------------------------------------------------------------------------------
export default function Medications() {
  const [darkMode, setDarkMode] = useDarkMode();
  const [medications, setMedications] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // OpenFDA Modal
  const [fdaDrug, setFdaDrug] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [medsData, docsData] = await Promise.all([
        patientService.getMedications(),
        patientService.getDoctors().catch(() => []),
      ]);
      setMedications(Array.isArray(medsData) ? medsData : []);
      setDoctors(Array.isArray(docsData) ? docsData : []);
    } catch (err) {
      console.error("Failed to load medication data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddMedication = async (medData) => {
    await patientService.addMedication(medData);
    await loadData();
  };

  const filteredMeds = medications.filter((m) =>
    (m.name || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeMeds = filteredMeds.filter((m) => m.is_active !== false);
  const pastMeds = filteredMeds.filter((m) => m.is_active === false);

  const morningDoses = activeMeds.filter((m) =>
    (m.frequency || "").toLowerCase().includes("daily") ||
    (m.notes || "").toLowerCase().includes("morning")
  ).length;

  const eveningDoses = activeMeds.filter((m) =>
    (m.frequency || "").toLowerCase().includes("twice") ||
    (m.notes || "").toLowerCase().includes("evening") ||
    (m.notes || "").toLowerCase().includes("night")
  ).length;

  return (
    <div
      className={`h-screen w-full overflow-hidden ${
        darkMode ? "bg-[#0b1413] text-white" : "bg-[#f8faf9] text-slate-900"
      }`}
    >
      <Sidebar darkMode={darkMode} />

      <div className="ml-[255px] h-full p-2">
        <div
          className={`flex h-full w-full overflow-hidden rounded-[18px] border ${
            darkMode ? "border-slate-800 bg-[#111c1b]" : "border-slate-200 bg-white"
          }`}
        >
          <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
            <Header darkMode={darkMode} setDarkMode={setDarkMode} />

            <div className="min-h-0 flex-1 overflow-y-auto px-8 py-5">
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-9 w-[260px] items-center gap-2.5 rounded-xl border px-3 ${
                      darkMode
                        ? "border-slate-700 bg-slate-900/40"
                        : "border-slate-200 bg-white"
                    }`}
                  >
                    <Search size={15} className="text-slate-500" />
                    <input
                      placeholder="Search medications..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className={`w-full bg-transparent text-[11px] outline-none ${
                        darkMode
                          ? "text-white placeholder:text-slate-500"
                          : "text-slate-700 placeholder:text-slate-400"
                      }`}
                    />
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setShowAdd(true)}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500 px-4 py-2 text-[11px] font-semibold text-white hover:bg-emerald-600 transition"
                >
                  <Plus size={14} />
                  Add Medicine
                </button>
              </div>

              {/* STAT CARDS */}
              <div className="mt-4 grid grid-cols-4 gap-3">
                <StatCard
                  darkMode={darkMode}
                  label="Active Medications"
                  value={activeMeds.length}
                  icon={<Pill />}
                />
                <StatCard
                  darkMode={darkMode}
                  label="Morning Regimens"
                  value={morningDoses}
                  suffix="regimens"
                  icon={<Clock3 />}
                />
                <StatCard
                  darkMode={darkMode}
                  label="Evening Regimens"
                  value={eveningDoses}
                  suffix="regimens"
                  icon={<Clock3 />}
                />
                <StatCard
                  darkMode={darkMode}
                  label="Registered Prescribers"
                  value={doctors.length}
                  suffix="doctors"
                  icon={<CalendarDays />}
                />
              </div>

              {/* MEDICATIONS GRID */}
              <div className="mt-4 grid grid-cols-[1.1fr_0.9fr] gap-4">
                {/* ACTIVE PRESCRIPTIONS */}
                <section
                  className={`rounded-[14px] border p-4 ${
                    darkMode ? "border-slate-800 bg-[#15211f]" : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3
                        className={`text-[14px] font-bold ${
                          darkMode ? "text-white" : "text-emerald-950"
                        }`}
                      >
                        Active Prescriptions
                      </h3>
                      <p className="mt-0.5 text-[10px] text-slate-400">
                        Current medications on file in your clinical chart
                      </p>
                    </div>

                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[9px] font-semibold ${
                        darkMode
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-emerald-50 text-emerald-700"
                      }`}
                    >
                      {activeMeds.length} Active
                    </span>
                  </div>

                  {loading ? (
                    <div className="flex items-center justify-center py-10 text-[11px] text-slate-400">
                      <Loader2 size={16} className="animate-spin mr-2 text-emerald-400" />
                      Loading active medications...
                    </div>
                  ) : activeMeds.length === 0 ? (
                    <div
                      className={`rounded-xl border p-8 text-center text-[11px] ${
                        darkMode
                          ? "border-slate-800 bg-[#101918] text-slate-500"
                          : "border-slate-100 bg-slate-50 text-slate-500"
                      }`}
                    >
                      <Pill size={28} className="mx-auto mb-2 text-slate-600" />
                      <p className="font-semibold text-slate-400">No active medications recorded.</p>
                      <p className="mt-1 text-[10px] text-slate-500">
                        Click "Add Medicine" to record your prescriptions.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {activeMeds.map((medication) => (
                        <CurrentMedicationCard
                          key={medication.id}
                          medication={medication}
                          darkMode={darkMode}
                          onOpenFda={(drug) => setFdaDrug(drug)}
                        />
                      ))}
                    </div>
                  )}
                </section>

                {/* TODAY SCHEDULE / QUICK VIEW */}
                <section
                  className={`rounded-[14px] border p-4 flex flex-col ${
                    darkMode ? "border-slate-800 bg-[#15211f]" : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3
                        className={`text-[14px] font-bold ${
                          darkMode ? "text-white" : "text-emerald-950"
                        }`}
                      >
                        Pharmacological Safety Quick Lookup
                      </h3>
                      <p className="mt-0.5 text-[10px] text-slate-400">
                        Check FDA boxed warnings and adverse event reports
                      </p>
                    </div>
                  </div>

                  <div className="space-y-2.5 flex-1">
                    <p className="text-[11px] text-slate-300">
                      Select any of your medications below to trigger real-time FDA safety surveillance:
                    </p>

                    <div className="flex flex-wrap gap-2 pt-1">
                      {activeMeds.length > 0 ? (
                        activeMeds.map((m) => (
                          <button
                            key={m.id}
                            type="button"
                            onClick={() => setFdaDrug(m.name)}
                            className="flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-[11px] font-semibold text-emerald-400 hover:bg-emerald-500/20 transition"
                          >
                            <ShieldAlert size={13} />
                            {m.name}
                          </button>
                        ))
                      ) : (
                        <p className="text-[10px] text-slate-500 italic">
                          No medications available for safety lookup.
                        </p>
                      )}
                    </div>

                    <div className="mt-4 rounded-xl border border-slate-800 bg-[#101918] p-3 text-[10px] text-slate-400 space-y-1.5">
                      <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                        <Info size={13} />
                        <span>Surveillance Engine Features</span>
                      </div>
                      <p>• FDA Black Box Warnings & Contradictions</p>
                      <p>• Post-marketing adverse event frequencies</p>
                      <p>• Clinical precautions & dosage safeguards</p>
                    </div>
                  </div>
                </section>
              </div>

              {/* MEDICATION HISTORY TABLE */}
              <section
                className={`mt-4 overflow-hidden rounded-[14px] border ${
                  darkMode ? "border-slate-800 bg-[#15211f]" : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
                  <div>
                    <h3
                      className={`text-[13px] font-bold ${
                        darkMode ? "text-white" : "text-emerald-950"
                      }`}
                    >
                      All Prescriptions & History
                    </h3>
                    <p className="mt-0.5 text-[9px] text-slate-400">
                      Complete log of active and discontinued medications
                    </p>
                  </div>
                </div>

                <div className="min-w-0">
                  <div
                    className={`grid grid-cols-[1.4fr_1fr_1.2fr_1.2fr_.8fr] px-4 py-2.5 text-[9px] font-semibold uppercase tracking-[0.08em] ${
                      darkMode ? "text-slate-400" : "text-slate-500"
                    }`}
                  >
                    <span>Medication Name</span>
                    <span>Dosage</span>
                    <span>Frequency</span>
                    <span>Prescribed By</span>
                    <span className="text-right">Safety Action</span>
                  </div>

                  {filteredMeds.length === 0 ? (
                    <div className="py-8 text-center text-[11px] text-slate-500">
                      No medication records in chart.
                    </div>
                  ) : (
                    filteredMeds.map((item) => (
                      <div
                        key={item.id}
                        className={`grid grid-cols-[1.4fr_1fr_1.2fr_1.2fr_.8fr] items-center px-4 py-3 text-[11px] border-t ${
                          darkMode ? "border-slate-800" : "border-slate-100"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <Pill size={13} className="text-emerald-400 shrink-0" />
                          <span className="font-semibold text-white">
                            {item.name}
                          </span>
                        </div>

                        <span className="text-slate-300">
                          {item.dosage || "Standard"}
                        </span>

                        <span className="text-slate-400">
                          {item.frequency || "Daily"}
                        </span>

                        <span className="text-slate-400">
                          {item.prescribed_by_name || "Primary Care"}
                        </span>

                        <div className="text-right">
                          <button
                            type="button"
                            onClick={() => setFdaDrug(item.name)}
                            className="inline-flex items-center gap-1 rounded border border-slate-700 px-2 py-0.5 text-[10px] text-slate-300 hover:border-emerald-500 hover:text-emerald-400 transition"
                          >
                            <ShieldAlert size={11} />
                            Inspect
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </section>
            </div>
          </main>
        </div>
      </div>

      {showAdd && (
        <AddMedicationModal
          darkMode={darkMode}
          doctors={doctors}
          onClose={() => setShowAdd(false)}
          onAdd={handleAddMedication}
        />
      )}

      {fdaDrug && (
        <OpenFdaModal
          drugName={fdaDrug}
          darkMode={darkMode}
          onClose={() => setFdaDrug(null)}
        />
      )}
    </div>
  );
}
