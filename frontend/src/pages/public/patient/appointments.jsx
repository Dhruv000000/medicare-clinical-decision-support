// ==============================================================================
// FILE: frontend/src/pages/public/patient/appointments.jsx
// PURPOSE: Patient appointment scheduling portal and consultation calendar.
// VIVA EXPLANATION: Implements the appointment management portal for patients. Allows booking consultations with verified physicians from /doctor/list/, browsing upcoming vs past visits, viewing appointment status updates (SCHEDULED, CONFIRMED, COMPLETED), and reviewing booking reasons.
// ==============================================================================

import React, { createContext, useContext, useEffect, useState } from "react";
import Sidebar from "./sidebar";
import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Bell,
  Brain,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  CircleDot,
  ClipboardList,
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
  XCircle,
} from "lucide-react";
import patientService from "../../../services/patientService";
import { useAuth } from "../../../_core/hooks/useAuth";

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem("medicare-theme");

    if (savedTheme === "dark" || savedTheme === "light") {
      return savedTheme;
    }

    return "light";
  });

  useEffect(() => {
    const root = document.documentElement;

    root.classList.toggle("dark", theme === "dark");
    root.setAttribute("data-theme", theme);
    localStorage.setItem("medicare-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((currentTheme) =>
      currentTheme === "dark" ? "light" : "dark"
    );
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        toggleTheme,
        isDark: theme === "dark",
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error("useTheme must be used inside ThemeProvider");
  }

  return context;
}

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

function isActivePath(currentPath, route) {
  return currentPath.replace(/\/$/, "") === route.replace(/\/$/, "");
}

function Header() {
  const { isDark: darkMode, toggleTheme } = useTheme();
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
          Appointments
        </h1>

        <p
          className={`mt-1 text-[12px] ${
            darkMode ? "text-slate-500" : "text-slate-500"
          }`}
        >
          Manage your doctor appointments
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
          onClick={toggleTheme}
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

function StatCard({ darkMode, icon, label, value, suffix }) {
  return (
    <div
      className={`rounded-[14px] border p-4 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-start justify-between">
        <div
          className={`flex h-8 w-8 items-center justify-center rounded-lg ${
            darkMode ? "bg-emerald-500/10" : "bg-emerald-50"
          }`}
        >
          {icon}
        </div>

        <CalendarDays
          size={14}
          className={darkMode ? "text-slate-600" : "text-slate-400"}
        />
      </div>

      <p
        className={`mt-3 text-[10px] ${
          darkMode ? "text-slate-500" : "text-slate-500"
        }`}
      >
        {label}
      </p>

      <div className="mt-1 flex items-baseline gap-1">
        <span
          className={`text-[22px] font-semibold ${
            darkMode ? "text-white" : "text-emerald-950"
          }`}
        >
          {value}
        </span>

        {suffix && (
          <span
            className={`text-[10px] ${
              darkMode ? "text-slate-400" : "text-slate-500"
            }`}
          >
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}

function AppointmentPerson({ appointment, darkMode }) {
  const doctorName = appointment.doctor || appointment.doctor_name || "Dr. Specialist";
  const specialty = appointment.specialty || "Clinical Consultation";
  const initial = doctorName.replace(/^Dr\.?\s*/i, "").charAt(0) || "D";

  return (
    <div className="flex min-w-0 items-center gap-3">
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold uppercase ${
          darkMode
            ? "bg-emerald-900/60 text-emerald-300 border border-emerald-700/50"
            : "bg-emerald-100 text-emerald-800"
        }`}
      >
        {initial}
      </div>

      <div className="min-w-0">
        <p
          className={`truncate text-[11px] font-semibold ${
            darkMode ? "text-white" : "text-slate-800"
          }`}
        >
          {doctorName}
        </p>

        <p
          className={`mt-0.5 text-[9px] ${
            darkMode ? "text-slate-500" : "text-slate-500"
          }`}
        >
          {specialty}
        </p>
      </div>
    </div>
  );
}

// --- AppointmentsContent ---
// What it does: Primary appointments component managing booking state, appointment lists, doctor selections, and modals.
// Why it's structured this way: Separates upcoming from past visits based on current timestamp comparison.
// Parameters & Returns: Props (none) -> Rendered appointments content JSX.
// ------------------------------------------------------------------------------
function AppointmentsContent() {
  const { isDark: darkMode } = useTheme();
  const [showModal, setShowModal] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);

  const [appointmentsList, setAppointmentsList] = useState([]);
  const [doctorsList, setDoctorsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState("");

  // Booking form state
  const [selectedDoctorId, setSelectedDoctorId] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
  const [bookingReason, setBookingReason] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const [apts, docs] = await Promise.all([
        patientService.getAppointments(),
        patientService.getDoctors(),
      ]);
      const aptsArr = Array.isArray(apts) ? apts : [];
      const docsArr = Array.isArray(docs) ? docs : [];
      setAppointmentsList(aptsArr);
      setDoctorsList(docsArr);
      if (docsArr.length > 0) {
        setSelectedDoctorId(String(docsArr[0].id));
      }
    } catch (err) {
      console.warn("Failed to load appointments:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const openDetails = (appointment) => {
    setSelectedAppointment(appointment);
    setShowModal(true);
  };

  // Split into upcoming and past
  const now = new Date();
  const upcomingAppointments = appointmentsList
    .filter((a) => {
      const d = new Date(a.starts_at);
      return d >= now && a.status !== "CANCELLED";
    })
    .map((a) => {
      const d = new Date(a.starts_at);
      return {
        id: a.id,
        doctor: a.doctor_name || "Dr. Medical Specialist",
        specialty: a.doctor_specialization || "Clinical Consultation",
        date: d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
        time: d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
        hospital: a.reason || "MediCare Center",
        status: a.status,
      };
    });

  const appointmentHistory = appointmentsList
    .filter((a) => {
      const d = new Date(a.starts_at);
      return d < now || a.status === "COMPLETED" || a.status === "CANCELLED";
    })
    .map((a) => {
      const d = new Date(a.starts_at);
      return {
        id: a.id,
        doctor: a.doctor_name || "Dr. Medical Specialist",
        specialty: a.doctor_specialization || "Clinical Consultation",
        date: d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
        time: d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
        hospital: a.reason || "MediCare Center",
        status: a.status,
      };
    });

  const handleBookAppointment = async (e) => {
    e.preventDefault();
    if (!selectedDoctorId || !selectedDate || !selectedTime) {
      setBookingError("Please select a doctor, date, and appointment time.");
      return;
    }

    try {
      setIsSubmitting(true);
      setBookingError("");
      const startsAtISO = new Date(`${selectedDate}T${selectedTime}:00`).toISOString();
      await patientService.bookAppointment({
        doctor_id: Number(selectedDoctorId),
        starts_at: startsAtISO,
        reason: bookingReason || "General Consultation",
      });
      await loadData();
      setShowModal(false);
      setSelectedDate("");
      setSelectedTime("");
      setBookingReason("");
    } catch (err) {
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        "Could not book appointment. Please try again.";
      setBookingError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className={`min-h-screen w-full overflow-hidden ${
        darkMode
          ? "bg-[#0b1413] text-white"
          : "bg-[#f8faf9] text-slate-900"
      }`}
    >
      <div
        className={`min-h-screen w-full overflow-hidden ${
          darkMode
            ? "border-slate-800 bg-[#111c1b]"
            : "border-slate-200 bg-white"
        }`}
      >
        <Sidebar darkMode={darkMode} />

        <main className="ml-[255px] flex min-w-0 min-h-screen flex-1 flex-col overflow-hidden">
          <Header />

          <div className="min-h-0 flex-1 overflow-hidden px-8 py-4">
            <div className="flex h-full min-h-0 flex-col">
              <div className="flex shrink-0 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedAppointment(null);
                    setShowModal(true);
                  }}
                  className="rounded-lg bg-emerald-500 px-4 py-2 text-[10px] font-semibold text-white transition hover:bg-emerald-600"
                >
                  + Book Appointment
                </button>
              </div>

              <div className="mt-3 grid shrink-0 grid-cols-3 gap-3">
                <StatCard
                  darkMode={darkMode}
                  icon={
                    <CalendarDays
                      size={16}
                      className="text-emerald-500"
                    />
                  }
                  label="Upcoming"
                  value={loading ? "…" : upcomingAppointments.length}
                  suffix="Appointments"
                />

                <StatCard
                  darkMode={darkMode}
                  icon={
                    <CheckCircle2
                      size={16}
                      className="text-emerald-500"
                    />
                  }
                  label="Completed"
                  value={loading ? "…" : appointmentsList.filter((a) => a.status === "COMPLETED").length}
                  suffix="Visits"
                />

                <StatCard
                  darkMode={darkMode}
                  icon={
                    <XCircle
                      size={16}
                      className="text-red-400"
                    />
                  }
                  label="Cancelled"
                  value={loading ? "…" : appointmentsList.filter((a) => a.status === "CANCELLED").length}
                  suffix="Visits"
                />
              </div>

              <section
                className={`mt-3 shrink-0 rounded-[14px] border p-4 ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3
                      className={`text-[13px] font-bold ${
                        darkMode ? "text-white" : "text-emerald-950"
                      }`}
                    >
                      Upcoming Appointments
                    </h3>

                    <p
                      className={`mt-1 text-[9px] ${
                        darkMode ? "text-slate-500" : "text-slate-500"
                      }`}
                    >
                      Your scheduled appointments
                    </p>
                  </div>

                  <span
                    className={`rounded-full px-2 py-1 text-[8px] font-medium ${
                      darkMode
                        ? "bg-emerald-500/10 text-emerald-400"
                        : "bg-emerald-50 text-emerald-700"
                    }`}
                  >
                    {upcomingAppointments.length} Scheduled
                  </span>
                </div>

                <div className="mt-3 space-y-2">
                  {upcomingAppointments.length === 0 ? (
                    <div className="py-6 text-center text-[10px] text-slate-500">
                      No upcoming appointments scheduled. Use &quot;+ Book Appointment&quot; above.
                    </div>
                  ) : (
                    upcomingAppointments.map((appointment) => (
                      <div
                        key={appointment.id}
                        className={`grid grid-cols-[1.5fr_0.8fr_0.75fr_1.15fr_auto] items-center gap-4 rounded-xl border px-3 py-2.5 ${
                          darkMode
                            ? "border-slate-800 bg-[#101918]"
                            : "border-slate-100 bg-slate-50/70"
                        }`}
                      >
                        <AppointmentPerson
                          appointment={appointment}
                          darkMode={darkMode}
                        />

                        <div className="min-w-0">
                          <p className="text-[8px] text-slate-500">DATE</p>

                          <p
                            className={`mt-0.5 text-[10px] font-medium ${
                              darkMode ? "text-slate-200" : "text-slate-700"
                            }`}
                          >
                            {appointment.date}
                          </p>
                        </div>

                        <div>
                          <p className="text-[8px] text-slate-500">TIME</p>

                          <p
                            className={`mt-0.5 text-[10px] font-medium ${
                              darkMode ? "text-slate-200" : "text-slate-700"
                            }`}
                          >
                            {appointment.time}
                          </p>
                        </div>

                        <div className="min-w-0">
                          <p className="text-[8px] text-slate-500">
                            REASON
                          </p>

                          <p
                            className={`mt-0.5 truncate text-[10px] font-medium ${
                              darkMode ? "text-slate-200" : "text-slate-700"
                            }`}
                          >
                            {appointment.hospital}
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={() => openDetails(appointment)}
                          className="whitespace-nowrap rounded-lg border border-emerald-500/50 px-3 py-1.5 text-[9px] font-semibold text-emerald-500 transition hover:bg-emerald-500 hover:text-white"
                        >
                          View Details
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </section>

              <section
                className={`mt-3 min-h-0 flex-1 overflow-hidden rounded-[14px] border ${
                  darkMode
                    ? "border-slate-800 bg-[#15211f]"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-center justify-between px-4 py-3">
                  <div>
                    <h3
                      className={`text-[13px] font-bold ${
                        darkMode ? "text-white" : "text-emerald-950"
                      }`}
                    >
                      Appointment History
                    </h3>

                    <p
                      className={`mt-1 text-[9px] ${
                        darkMode ? "text-slate-500" : "text-slate-500"
                      }`}
                    >
                      Your previous appointments
                    </p>
                  </div>

                  <button
                    type="button"
                    className="text-[9px] font-medium text-emerald-500"
                  >
                    View All
                  </button>
                </div>

                <div
                  className={`border-t ${
                    darkMode ? "border-slate-800" : "border-slate-100"
                  }`}
                >
                  <div
                    className={`grid grid-cols-[1.4fr_1.1fr_0.9fr_0.8fr_0.6fr] px-4 py-2 text-[8px] font-semibold uppercase tracking-[0.08em] ${
                      darkMode ? "text-slate-600" : "text-slate-400"
                    }`}
                  >
                    <span>Doctor</span>
                    <span>Specialty</span>
                    <span>Date</span>
                    <span>Status</span>
                    <span className="text-right">Action</span>
                  </div>

                  {appointmentHistory.map((item, index) => (
                    <div
                      key={`${item.doctor}-${item.date}`}
                      className={`grid grid-cols-[1.4fr_1.1fr_0.9fr_0.8fr_0.6fr] items-center px-4 py-2.5 text-[9px] ${
                        index !== appointmentHistory.length - 1
                          ? `border-b ${
                              darkMode
                                ? "border-slate-800"
                                : "border-slate-100"
                            }`
                          : ""
                      }`}
                    >
                      <span
                        className={`font-medium ${
                          darkMode ? "text-slate-200" : "text-slate-700"
                        }`}
                      >
                        {item.doctor}
                      </span>

                      <span
                        className={
                          darkMode ? "text-slate-500" : "text-slate-500"
                        }
                      >
                        {item.specialty}
                      </span>

                      <span
                        className={
                          darkMode ? "text-slate-400" : "text-slate-500"
                        }
                      >
                        {item.date}
                      </span>

                      <span>
                        <span
                          className={`inline-flex rounded-full px-2 py-1 text-[8px] font-medium ${
                            item.status === "Completed"
                              ? darkMode
                                ? "bg-emerald-500/10 text-emerald-400"
                                : "bg-emerald-50 text-emerald-700"
                              : darkMode
                                ? "bg-red-500/10 text-red-400"
                                : "bg-red-50 text-red-600"
                          }`}
                        >
                          {item.status}
                        </span>
                      </span>

                      <button
                        type="button"
                        onClick={() =>
                          openDetails({
                            doctor: item.doctor,
                            specialty: item.specialty,
                            date: item.date,
                            time: "Previous visit",
                            hospital: "MediCare Clinic",
                          })
                        }
                        className="text-right font-medium text-emerald-500 hover:text-emerald-600"
                      >
                        View
                      </button>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </div>
        </main>

        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div
              className={`w-full max-w-md rounded-2xl border p-5 shadow-2xl ${
                darkMode
                  ? "border-slate-700 bg-[#15211f]"
                  : "border-slate-200 bg-white"
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3
                    className={`text-[16px] font-bold ${
                      darkMode ? "text-white" : "text-emerald-950"
                    }`}
                  >
                    {selectedAppointment
                      ? "Appointment Details"
                      : "Book Appointment"}
                  </h3>

                  <p
                    className={`mt-1 text-[10px] ${
                      darkMode ? "text-slate-500" : "text-slate-500"
                    }`}
                  >
                    {selectedAppointment
                      ? "Review the appointment information."
                      : "Choose a doctor and preferred visit time."}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className={`rounded-lg p-1.5 ${
                    darkMode
                      ? "text-slate-400 hover:bg-slate-800"
                      : "text-slate-500 hover:bg-slate-100"
                  }`}
                >
                  <XCircle size={18} />
                </button>
              </div>

              {selectedAppointment ? (
                <div className="mt-5">
                  <AppointmentPerson
                    appointment={selectedAppointment}
                    darkMode={darkMode}
                  />

                  <div className="mt-5 grid grid-cols-2 gap-3">
                    <div
                      className={`rounded-xl border p-3 ${
                        darkMode
                          ? "border-slate-800 bg-[#101918]"
                          : "border-slate-100 bg-slate-50"
                      }`}
                    >
                      <p className="text-[8px] text-slate-500">DATE</p>

                      <p
                        className={`mt-1 text-[11px] font-medium ${
                          darkMode
                            ? "text-slate-200"
                            : "text-slate-700"
                        }`}
                      >
                        {selectedAppointment.date}
                      </p>
                    </div>

                    <div
                      className={`rounded-xl border p-3 ${
                        darkMode
                          ? "border-slate-800 bg-[#101918]"
                          : "border-slate-100 bg-slate-50"
                      }`}
                    >
                      <p className="text-[8px] text-slate-500">TIME</p>

                      <p
                        className={`mt-1 text-[11px] font-medium ${
                          darkMode
                            ? "text-slate-200"
                            : "text-slate-700"
                        }`}
                      >
                        {selectedAppointment.time}
                      </p>
                    </div>
                  </div>

                  <div
                    className={`mt-3 rounded-xl border p-3 ${
                      darkMode
                        ? "border-slate-800 bg-[#101918]"
                        : "border-slate-100 bg-slate-50"
                    }`}
                  >
                    <p className="text-[8px] text-slate-500">LOCATION</p>

                    <p
                      className={`mt-1 text-[11px] font-medium ${
                        darkMode
                          ? "text-slate-200"
                          : "text-slate-700"
                      }`}
                    >
                      {selectedAppointment.hospital}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="mt-5 w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-[10px] font-semibold text-white hover:bg-emerald-600"
                  >
                    Close
                  </button>
                </div>
              ) : (
                <form onSubmit={handleBookAppointment} className="mt-5 space-y-3">
                  {bookingError && (
                    <div className="rounded-lg bg-red-500/10 p-2.5 text-[10px] text-red-400 border border-red-500/20">
                      {bookingError}
                    </div>
                  )}

                  <label
                    className={`block text-[10px] font-medium ${
                      darkMode ? "text-slate-300" : "text-slate-700"
                    }`}
                  >
                    Choose Doctor
                    <select
                      value={selectedDoctorId}
                      onChange={(e) => setSelectedDoctorId(e.target.value)}
                      className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[10px] outline-none ${
                        darkMode
                          ? "border-slate-700 bg-[#101918] text-slate-200"
                          : "border-slate-200 bg-white text-slate-700"
                      }`}
                    >
                      {doctorsList.length === 0 ? (
                        <option value="">No doctors currently available</option>
                      ) : (
                        doctorsList.map((doc) => (
                          <option key={doc.id} value={doc.id}>
                            {doc.name} ({doc.specialization})
                          </option>
                        ))
                      )}
                    </select>
                  </label>

                  <label
                    className={`block text-[10px] font-medium ${
                      darkMode ? "text-slate-300" : "text-slate-700"
                    }`}
                  >
                    Date
                    <input
                      type="date"
                      required
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[10px] outline-none ${
                        darkMode
                          ? "border-slate-700 bg-[#101918] text-slate-200"
                          : "border-slate-200 bg-white text-slate-700"
                      }`}
                    />
                  </label>

                  <label
                    className={`block text-[10px] font-medium ${
                      darkMode ? "text-slate-300" : "text-slate-700"
                    }`}
                  >
                    Time
                    <input
                      type="time"
                      required
                      value={selectedTime}
                      onChange={(e) => setSelectedTime(e.target.value)}
                      className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[10px] outline-none ${
                        darkMode
                          ? "border-slate-700 bg-[#101918] text-slate-200"
                          : "border-slate-200 bg-white text-slate-700"
                      }`}
                    />
                  </label>

                  <label
                    className={`block text-[10px] font-medium ${
                      darkMode ? "text-slate-300" : "text-slate-700"
                    }`}
                  >
                    Reason / Notes
                    <input
                      type="text"
                      placeholder="e.g. Follow-up consultation"
                      value={bookingReason}
                      onChange={(e) => setBookingReason(e.target.value)}
                      className={`mt-1.5 w-full rounded-lg border px-3 py-2 text-[10px] outline-none ${
                        darkMode
                          ? "border-slate-700 bg-[#101918] text-slate-200"
                          : "border-slate-200 bg-white text-slate-700"
                      }`}
                    />
                  </label>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="mt-2 w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-[10px] font-semibold text-white hover:bg-emerald-600 disabled:opacity-50"
                  >
                    {isSubmitting ? "Booking Appointment..." : "Confirm Appointment"}
                  </button>
                </form>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// --- Appointments ---
// What it does: Top-level wrapper component ensuring theme context availability for the appointments view.
// Why it's structured this way: Encapsulates ThemeProvider boundary for independent route rendering.
// Parameters & Returns: Props (none) -> Theme-wrapped Appointments JSX.
// ------------------------------------------------------------------------------
function Appointments() {
  return (
    <ThemeProvider>
      <AppointmentsContent />
    </ThemeProvider>
  );
}

export default Appointments;