// ==============================================================================
// FILE: frontend/src/pages/public/doctor/appointmentss.jsx
// PURPOSE: Doctor consultation schedule console managing patient appointments, status transitions, and encounter calendars.
// VIVA EXPLANATION: This screen allows practitioners to view real-time booked consultations, filter by status (scheduled, confirmed, completed, cancelled), and execute state transitions directly updating the underlying appointments microservice.
// ==============================================================================

import React, { useEffect, useMemo, useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  CalendarDays,
  Clock3,
  UserRound,
  Video,
  MapPin,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Calendar,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";
import { useAuth } from "../../../_core/hooks/useAuth";
import doctorService from "../../../services/doctorService";

// --- StatusBadge ---
// What it does: Renders normalized status labels and iconography for appointment scheduling states.
// Why it's structured this way: Normalizes case sensitivity and provides distinct badge coloring for triage clarity.
// Parameters & Returns: Props: status (string). Returns styled JSX badge.
// ------------------------------------------------------------------------------
function StatusBadge({ status }) {
  const norm = (status || "scheduled").toLowerCase();

  const config = {
    confirmed: {
      icon: CheckCircle2,
      label: "Confirmed",
      style: "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20",
    },
    completed: {
      icon: CheckCircle2,
      label: "Completed",
      style: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
    },
    scheduled: {
      icon: Clock3,
      label: "Scheduled",
      style: "bg-amber-500/10 text-amber-500 border border-amber-500/20",
    },
    pending: {
      icon: Clock3,
      label: "Pending",
      style: "bg-amber-500/10 text-amber-500 border border-amber-500/20",
    },
    cancelled: {
      icon: XCircle,
      label: "Cancelled",
      style: "bg-red-500/10 text-red-500 border border-red-500/20",
    },
  };

  const item = config[norm] || config.scheduled;
  const Icon = item.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${item.style}`}
    >
      <Icon size={12} />
      {item.label}
    </span>
  );
}

// --- DoctorAppointments ---
// What it does: Primary schedule management component displaying appointment queues with dynamic status transitions.
// Why it's structured this way: Consumes doctorService to query and mutate clinical consultation slots with optimistic status updates.
// Parameters & Returns: None. Returns consultation schedule management JSX view.
// ------------------------------------------------------------------------------
export default function DoctorAppointments() {
  const { isDark, toggleTheme } = useTheme();
  const { user } = useAuth();

  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const loadAppointments = async () => {
    try {
      setLoading(true);
      const data = await doctorService.getAppointments();
      setAppointments(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load doctor appointments:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, []);

  const handleStatusUpdate = async (id, newStatus) => {
    try {
      setActionLoadingId(id);
      await doctorService.updateAppointmentStatus(id, newStatus);
      await loadAppointments();
    } catch (err) {
      console.error("Failed to update appointment status:", err);
    } finally {
      setActionLoadingId(null);
    }
  };

  const filteredAppointments = useMemo(() => {
    const query = search.trim().toLowerCase();

    return appointments.filter((appointment) => {
      const patientName = appointment.patient_name || appointment.patient?.email || "Patient";
      const reason = appointment.reason || "";
      const idStr = String(appointment.id);
      const status = (appointment.status || "scheduled").toLowerCase();

      const matchesSearch =
        !query ||
        patientName.toLowerCase().includes(query) ||
        reason.toLowerCase().includes(query) ||
        idStr.includes(query);

      const matchesFilter =
        filter === "All" ||
        status === filter.toLowerCase();

      return matchesSearch && matchesFilter;
    });
  }, [appointments, search, filter]);

  const doctorName = user?.last_name
    ? `Dr. ${user.last_name}`
    : user?.first_name
    ? `Dr. ${user.first_name}`
    : "Dr. Doctor";

  // Compute metrics
  const totalCount = appointments.length;
  const confirmedCount = appointments.filter(
    (a) => (a.status || "").toLowerCase() === "confirmed"
  ).length;
  const scheduledCount = appointments.filter(
    (a) => (a.status || "").toLowerCase() === "scheduled"
  ).length;
  const completedCount = appointments.filter(
    (a) => (a.status || "").toLowerCase() === "completed"
  ).length;

  return (
    <div
      className="h-dvh min-h-0 overflow-hidden medicare-doctor-shell bg-[var(--bg)] text-[var(--text)]"
      style={{ colorScheme: isDark ? "dark" : "light" }}
    >
      <div className="flex h-full min-h-0">
        <Sidebar />

        <main className="ml-[217px] min-h-0 min-w-0 w-[calc(100%-217px)] flex-none overflow-hidden">
          {/* HEADER */}
          <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-[var(--border)] px-5 sm:px-7 lg:px-8">
            <h1 className="text-[26px] font-bold tracking-tight">Appointments Schedule</h1>

            <div className="flex items-center gap-3">
              <div className="hidden h-10 w-[280px] items-center gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 md:flex">
                <Search size={18} className="text-[var(--muted)]" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search visits..."
                  className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
                />
              </div>

              <button
                type="button"
                onClick={toggleTheme}
                aria-label="Toggle theme"
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] text-[var(--accent)]"
              >
                <span className="text-xl">{isDark ? "☼" : "☾"}</span>
              </button>

              <button type="button" aria-label="Notifications" className="relative p-2 text-[var(--text-secondary)]">
                <Bell size={20} />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--accent)]" />
              </button>

              <div className="hidden items-center gap-2 sm:flex">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                  <UserRound size={19} className="text-[var(--accent)]" />
                </div>
                <span className="text-xs font-semibold">{doctorName}</span>
              </div>
            </div>
          </header>

          {/* CONTENT */}
          <section className="grid h-[calc(100vh-72px)] min-h-0 grid-rows-[auto_auto_minmax(0,1fr)] gap-4 overflow-hidden px-5 py-5 sm:px-7 lg:px-8">
            <div className="flex items-end justify-between gap-4">
              <div>
                <h2 className="text-[22px] font-bold">Clinical Appointments</h2>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  Review booked consultations and advance patient appointment workflows
                </p>
              </div>
            </div>

            {/* SUMMARY CARDS */}
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Total Booked</span>
                  <Calendar size={17} className="text-[var(--accent)]" />
                </div>
                <p className="mt-2 text-2xl font-bold">{totalCount}</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Confirmed</span>
                  <CheckCircle2 size={17} className="text-emerald-400" />
                </div>
                <p className="mt-2 text-2xl font-bold">{confirmedCount}</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Pending Action</span>
                  <Clock3 size={17} className="text-amber-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">{scheduledCount}</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Completed</span>
                  <CheckCircle2 size={17} className="text-blue-400" />
                </div>
                <p className="mt-2 text-2xl font-bold">{completedCount}</p>
              </div>
            </div>

            {/* APPOINTMENT TABLE */}
            <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)]">
              {/* TOOLBAR */}
              <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
                <div className="flex items-center gap-2">
                  <CalendarDays size={16} className="text-[var(--muted)]" />
                  <span className="text-sm font-medium">All Consultations</span>
                  <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--accent)]">
                    {filteredAppointments.length}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {["All", "Scheduled", "Confirmed", "Completed", "Cancelled"].map((item) => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => setFilter(item)}
                      className={`rounded-lg px-3 py-1 text-xs font-medium transition ${
                        filter === item
                          ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                          : "text-[var(--muted)] hover:bg-[var(--card-soft)]"
                      }`}
                    >
                      {item}
                    </button>
                  ))}
                </div>
              </div>

              {/* TABLE */}
              <div className="min-h-0 flex-1 overflow-y-auto">
                <table className="w-full table-fixed border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border)] bg-[var(--card-soft)]">
                      <th className="w-[16%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Scheduled Time
                      </th>
                      <th className="w-[26%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Patient Name
                      </th>
                      <th className="w-[22%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Clinical Reason
                      </th>
                      <th className="w-[14%] px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Current Status
                      </th>
                      <th className="w-[22%] px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-[var(--muted)]">
                        Status Actions
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan="5" className="py-12 text-center text-sm text-[var(--muted)]">
                          <Loader2 size={20} className="mx-auto mb-2 animate-spin text-[var(--accent)]" />
                          Loading scheduled appointments...
                        </td>
                      </tr>
                    ) : filteredAppointments.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="py-12 text-center text-sm text-[var(--muted)]">
                          <CalendarDays size={32} className="mx-auto mb-2 text-[var(--muted)] opacity-60" />
                          <p className="font-semibold">No appointments found.</p>
                          <p className="mt-1 text-xs text-[var(--muted)]">
                            Patient booking requests will appear here when scheduled.
                          </p>
                        </td>
                      </tr>
                    ) : (
                      filteredAppointments.map((apt) => {
                        const dateObj = apt.starts_at ? new Date(apt.starts_at) : null;
                        const dateStr = dateObj
                          ? dateObj.toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                            })
                          : "Today";
                        const timeStr = dateObj
                          ? dateObj.toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "TBD";

                        const patientName = apt.patient_name || apt.patient?.email || `Patient #${apt.patient_id}`;
                        const statusNorm = (apt.status || "scheduled").toLowerCase();
                        const isActionLoading = actionLoadingId === apt.id;

                        return (
                          <tr
                            key={apt.id}
                            className="border-b border-[var(--border)] transition hover:bg-[var(--card-soft)] last:border-b-0"
                          >
                            <td className="px-4 py-3">
                              <p className="text-sm font-semibold">{timeStr}</p>
                              <p className="mt-0.5 flex items-center gap-1 text-[11px] text-[var(--muted)]">
                                <Clock3 size={11} />
                                {dateStr}
                              </p>
                            </td>

                            <td className="px-4 py-3">
                              <div className="flex min-w-0 items-center gap-2.5">
                                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                                  <UserRound size={15} className="text-[var(--accent)]" />
                                </div>
                                <div className="min-w-0">
                                  <p className="truncate text-sm font-semibold">{patientName}</p>
                                  <p className="truncate text-[10px] text-[var(--muted)]">
                                    APT-{apt.id}
                                  </p>
                                </div>
                              </div>
                            </td>

                            <td className="px-4 py-3">
                              <p className="truncate text-xs font-medium">
                                {apt.reason || "General Consultation"}
                              </p>
                            </td>

                            <td className="px-4 py-3">
                              <StatusBadge status={apt.status} />
                            </td>

                            <td className="px-4 py-3 text-right">
                              {isActionLoading ? (
                                <Loader2 size={14} className="ml-auto animate-spin text-[var(--accent)]" />
                              ) : (
                                <div className="flex items-center justify-end gap-1.5">
                                  {statusNorm === "scheduled" && (
                                    <button
                                      type="button"
                                      onClick={() => handleStatusUpdate(apt.id, "confirmed")}
                                      className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/20 transition"
                                    >
                                      Confirm
                                    </button>
                                  )}

                                  {statusNorm === "confirmed" && (
                                    <button
                                      type="button"
                                      onClick={() => handleStatusUpdate(apt.id, "completed")}
                                      className="rounded-lg border border-blue-500/30 bg-blue-500/10 px-2 py-1 text-xs font-semibold text-blue-400 hover:bg-blue-500/20 transition"
                                    >
                                      Complete
                                    </button>
                                  )}

                                  {statusNorm !== "cancelled" && statusNorm !== "completed" && (
                                    <button
                                      type="button"
                                      onClick={() => handleStatusUpdate(apt.id, "cancelled")}
                                      className="rounded-lg border border-red-500/30 bg-red-500/10 px-2 py-1 text-xs font-semibold text-red-400 hover:bg-red-500/20 transition"
                                    >
                                      Cancel
                                    </button>
                                  )}
                                </div>
                              )}
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
    </div>
  );
}