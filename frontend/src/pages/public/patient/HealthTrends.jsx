// ==============================================================================
// FILE: frontend/src/pages/public/patient/HealthTrends.jsx
// PURPOSE: Longitudinal health analytics and vital signs trend tracking.
// VIVA EXPLANATION: Visualizes patient biomarker timelines over consecutive clinical visits. Renders blood glucose and blood pressure trend graphs using Recharts, computes normal vs abnormal status badges, and highlights AI clinical observations.
// ==============================================================================

import React from "react";
import { Link } from "react-router-dom";
import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";
import {
  Activity,
  Bell,
  ChevronDown,
  ClipboardList,
  Moon,
  Search,
  Sparkles,
  Sun,
  Thermometer,
} from "lucide-react";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAuth } from "../../../_core/hooks/useAuth";
import patientService from "../../../services/patientService";

/* ---------------------------------------------------------
   HEADER
--------------------------------------------------------- */

function Header({ darkMode, toggleTheme }) {
  const { user } = useAuth();
  const displayName =
    user?.full_name ||
    (user?.first_name ? `${user.first_name} ${user.last_name || ""}`.trim() : null) ||
    user?.email ||
    "Patient";

  return (
    <header
      className={`flex h-[72px] shrink-0 items-center justify-between border-b px-8 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#111c1b]"
          : "border-slate-200 bg-white"
      }`}
    >
      <div>
        <h1
          className={`text-[27px] font-bold tracking-[-0.8px] ${
            darkMode
              ? "text-white"
              : "text-slate-900"
          }`}
        >
          Health Trends
        </h1>

        <p
          className={`mt-0.5 text-[12px] ${
            darkMode
              ? "text-slate-500"
              : "text-slate-500"
          }`}
        >
          Track your health metrics over time
        </p>
      </div>

      <div className="flex items-center gap-4">
        {/* SEARCH */}

        <div
          className={`flex h-10 w-[280px] items-center gap-3 rounded-xl border px-4 ${
            darkMode
              ? "border-slate-700 bg-slate-900/40"
              : "border-slate-200 bg-slate-50"
          }`}
        >
          <Search
            size={17}
            className={
              darkMode
                ? "text-slate-500"
                : "text-slate-400"
            }
          />

          <input
            className={`w-full bg-transparent text-sm outline-none ${
              darkMode
                ? "text-white placeholder:text-slate-500"
                : "text-slate-900 placeholder:text-slate-400"
            }`}
            placeholder="Search anything..."
          />
        </div>

        {/* THEME BUTTON */}

        <button
          type="button"
          onClick={toggleTheme}
          className={`flex h-10 w-10 items-center justify-center rounded-xl border transition-colors ${
            darkMode
              ? "border-slate-700 bg-slate-900 text-yellow-300"
              : "border-slate-200 bg-slate-50 text-slate-700"
          }`}
        >
          {darkMode ? (
            <Sun size={19} />
          ) : (
            <Moon size={19} />
          )}
        </button>

        {/* NOTIFICATIONS */}

        <button
          type="button"
          className={`relative ${
            darkMode
              ? "text-slate-300"
              : "text-slate-600"
          }`}
        >
          <Bell size={21} />

          <span
            className={`absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full border-2 ${
              darkMode
                ? "border-[#111c1b]"
                : "border-white"
            } bg-emerald-500`}
          />
        </button>

        {/* PROFILE */}

        <Link
          to="/patient/settings"
          className="flex items-center gap-3"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 text-white font-semibold text-xs">
            {displayName.slice(0, 2).toUpperCase()}
          </div>

          <span
            className={`text-[14px] font-semibold ${
              darkMode
                ? "text-white"
                : "text-slate-900"
            }`}
          >
            {displayName}
          </span>

          <ChevronDown
            size={16}
            className={
              darkMode
                ? "text-slate-400"
                : "text-slate-500"
            }
          />
        </Link>
      </div>
    </header>
  );
}


/* ---------------------------------------------------------
   METRIC CARD
--------------------------------------------------------- */

function MetricCard({
  icon,
  label,
  value,
  unit,
  badge,
  darkMode,
}) {
  return (
    <div
      className={`rounded-[14px] border p-5 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white shadow-sm"
      }`}
    >
      <div className="flex items-start justify-between">
        <div
          className={`flex h-9 w-9 items-center justify-center rounded-full ${
            darkMode
              ? "bg-emerald-500/10"
              : "bg-emerald-50"
          }`}
        >
          {icon}
        </div>

        <span
          className={`rounded-full px-2 py-1 text-[10px] font-medium ${
            darkMode
              ? "bg-emerald-500/10 text-emerald-500"
              : "bg-emerald-50 text-emerald-600"
          }`}
        >
          {badge}
        </span>
      </div>

      <p
        className={`mt-3 text-[11px] ${
          darkMode
            ? "text-slate-300"
            : "text-slate-600"
        }`}
      >
        {label}
      </p>

      <div className="mt-1 flex items-baseline gap-1.5">
        <span
          className={`text-[25px] font-semibold ${
            darkMode
              ? "text-white"
              : "text-slate-900"
          }`}
        >
          {value}
        </span>

        <span
          className={`text-[9px] ${
            darkMode
              ? "text-slate-500"
              : "text-slate-400"
          }`}
        >
          {unit}
        </span>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------
   BLOOD GLUCOSE CHART
--------------------------------------------------------- */

function BloodGlucoseCard({ darkMode, data = [] }) {
  const chartGrid = darkMode
    ? "#263936"
    : "#e2e8f0";

  const chartText = darkMode
    ? "#64748b"
    : "#94a3b8";

  const tooltipBg = darkMode
    ? "#101918"
    : "#ffffff";

  const tooltipBorder = darkMode
    ? "#334155"
    : "#e2e8f0";

  const tooltipText = darkMode
    ? "#e2e8f0"
    : "#334155";

  return (
    <section
      className={`min-h-0 flex-1 rounded-[14px] border p-4 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white shadow-sm"
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3
            className={`text-[14px] font-bold ${
              darkMode
                ? "text-white"
                : "text-slate-900"
            }`}
          >
            Blood Glucose
          </h3>

          <p
            className={`mt-1 text-[9px] ${
              darkMode
                ? "text-slate-500"
                : "text-slate-400"
            }`}
          >
            Recorded readings over time
          </p>
        </div>

        <span className="flex items-center gap-1 text-[9px] text-emerald-500">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          Glucose
        </span>
      </div>

      <div className="mt-3 h-[230px]">
        {data.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center p-4">
            <Activity size={28} className="text-slate-400 mb-2 opacity-40" />
            <p className={`text-xs font-medium ${darkMode ? "text-slate-300" : "text-slate-600"}`}>
              No blood glucose trend data recorded yet
            </p>
            <p className={`text-[10px] mt-1 ${darkMode ? "text-slate-500" : "text-slate-400"}`}>
              Upload lab test reports to populate historical glucose charts.
            </p>
          </div>
        ) : (
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <LineChart
              data={data}
              margin={{
                top: 4,
                right: 4,
                left: -24,
                bottom: 0,
              }}
            >
              <CartesianGrid
                stroke={chartGrid}
                strokeDasharray="2 4"
              />

              <XAxis
                dataKey="day"
                axisLine={false}
                tickLine={false}
                tick={{
                  fontSize: 8,
                  fill: chartText,
                }}
              />

              <YAxis
                domain={["auto", "auto"]}
                axisLine={false}
                tickLine={false}
                tick={{
                  fontSize: 8,
                  fill: chartText,
                }}
              />

              <Tooltip
                content={({ active, payload, label }) => {
                  if (
                    !active ||
                    !payload?.length
                  ) {
                    return null;
                  }

                  return (
                    <div
                      className="rounded-xl border px-3 py-2"
                      style={{
                        backgroundColor:
                          tooltipBg,
                        borderColor:
                          tooltipBorder,
                        color: tooltipText,
                      }}
                    >
                      <p className="text-[9px] font-semibold">
                        {label}
                      </p>

                      <p className="mt-1 text-[9px]">
                        Blood glucose:{" "}
                        <strong>
                          {payload[0]?.value} mg/dL
                        </strong>
                      </p>
                    </div>
                  );
                }}
              />

              <Line
                type="monotone"
                dataKey="value"
                stroke="#31b481"
                strokeWidth={2}
                dot={false}
                activeDot={{
                  r: 5,
                  fill: darkMode
                    ? "#15211f"
                    : "#ffffff",
                  stroke: "#31b481",
                  strokeWidth: 2,
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}

/* ---------------------------------------------------------
   RECENT MEASUREMENTS
--------------------------------------------------------- */

function RecentMeasurements({ darkMode, rows = [] }) {
  return (
    <section
      className={`shrink-0 rounded-[14px] border p-4 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white shadow-sm"
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <h3
            className={`text-[13px] font-bold ${
              darkMode
                ? "text-white"
                : "text-slate-900"
            }`}
          >
            Recent Measurements
          </h3>

          <p
            className={`mt-1 text-[9px] ${
              darkMode
                ? "text-slate-500"
                : "text-slate-400"
            }`}
          >
            Latest recorded health values
          </p>
        </div>

        <span
          className={`rounded-full px-2 py-1 text-[8px] font-medium ${
            darkMode
              ? "bg-emerald-500/10 text-emerald-500"
              : "bg-emerald-50 text-emerald-600"
          }`}
        >
          {rows.length} {rows.length === 1 ? "record" : "records"}
        </span>
      </div>

      <div
        className={`mt-2 divide-y ${
          darkMode
            ? "divide-slate-800"
            : "divide-slate-200"
        }`}
      >
        {rows.length === 0 ? (
          <div className="py-4 text-center">
            <p className={`text-[10px] ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
              No health measurements or diagnostic tests recorded yet.
            </p>
          </div>
        ) : (
          rows.slice(0, 4).map((row, idx) => (
            <div
              key={`${row.label}-${idx}`}
              className="flex items-center justify-between py-2"
            >
              <div>
                <p
                  className={`text-[10px] font-medium ${
                    darkMode
                      ? "text-slate-200"
                      : "text-slate-700"
                  }`}
                >
                  {row.label}
                </p>

                <p
                  className={`text-[8px] ${
                    darkMode
                      ? "text-slate-500"
                      : "text-slate-400"
                  }`}
                >
                  {row.date}
                </p>
              </div>

              <span
                className={`text-[10px] font-semibold ${
                  darkMode
                    ? "text-white"
                    : "text-slate-900"
                }`}
              >
                {row.value}
              </span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

/* ---------------------------------------------------------
   AI INSIGHT
--------------------------------------------------------- */

function AIInsight({ darkMode, latestReport }) {
  const hasAnalysis = Boolean(latestReport?.analysis_summary || latestReport?.extracted_text);

  return (
    <section
      className={`flex h-full min-h-0 flex-col rounded-[14px] border p-5 transition-colors duration-200 ${
        darkMode
          ? "border-slate-800 bg-[#15211f]"
          : "border-slate-200 bg-white shadow-sm"
      }`}
    >
      {/* HEADER */}

      <div className="flex shrink-0 items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-full ${
              darkMode
                ? "bg-emerald-500/10"
                : "bg-emerald-50"
            }`}
          >
            <Sparkles
              size={17}
              className="text-emerald-500"
            />
          </div>

          <div>
            <h3
              className={`text-[15px] font-bold ${
                darkMode
                  ? "text-white"
                  : "text-slate-900"
              }`}
            >
              AI Trend Insight
            </h3>

            <p
              className={`mt-0.5 text-[9px] ${
                darkMode
                  ? "text-slate-500"
                  : "text-slate-400"
              }`}
            >
              Clinical diagnostic synthesis
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={`rounded-full px-2 py-1 text-[8px] font-medium ${
              darkMode
                ? "bg-emerald-500/10 text-emerald-500"
                : "bg-emerald-50 text-emerald-600"
            }`}
          >
            AI Engine
          </span>
        </div>
      </div>

      {/* MAIN INSIGHT */}

      <div className="mt-5 flex flex-1 flex-col">
        <div
          className={`flex-1 rounded-xl border p-4 ${
            darkMode
              ? "border-slate-800 bg-[#101918]"
              : "border-slate-200 bg-slate-50"
          }`}
        >
          {hasAnalysis ? (
            <p
              className={`text-[11px] leading-6 ${
                darkMode
                  ? "text-slate-300"
                  : "text-slate-600"
              }`}
            >
              {latestReport.analysis_summary || latestReport.extracted_text.slice(0, 300)}
            </p>
          ) : (
            <p
              className={`text-[11px] leading-6 ${
                darkMode
                  ? "text-slate-300"
                  : "text-slate-600"
              }`}
            >
              No AI clinical insights generated yet. Upload a diagnostic laboratory report or clinical document to run OCR and clinical metric analysis.
            </p>
          )}
        </div>

        {/* STATS */}

        <div className="mt-4 grid shrink-0 grid-cols-2 gap-3">
          <div
            className={`rounded-xl border p-4 ${
              darkMode
                ? "border-slate-800 bg-[#101918]"
                : "border-slate-200 bg-slate-50"
            }`}
          >
            <p
              className={`text-[9px] ${
                darkMode
                  ? "text-slate-500"
                  : "text-slate-400"
              }`}
            >
              Latest report
            </p>

            <p
              className={`mt-2 text-[13px] font-semibold truncate ${
                darkMode
                  ? "text-white"
                  : "text-slate-900"
              }`}
            >
              {latestReport?.title || "None recorded"}
            </p>
          </div>

          <div
            className={`rounded-xl border p-4 ${
              darkMode
                ? "border-slate-800 bg-[#101918]"
                : "border-slate-200 bg-slate-50"
            }`}
          >
            <p
              className={`text-[9px] ${
                darkMode
                  ? "text-slate-500"
                  : "text-slate-400"
              }`}
            >
              Diagnostic status
            </p>

            <p
              className={`mt-2 text-[13px] font-semibold ${
                darkMode
                  ? "text-white"
                  : "text-slate-900"
              }`}
            >
              {hasAnalysis ? "Analyzed" : "Pending data"}
            </p>
          </div>
        </div>

        <Link
          to="/patient/reports-lab-tests"
          className="mt-4 shrink-0 rounded-lg bg-emerald-500 px-3 py-3 text-center text-[10px] font-semibold text-white transition-colors hover:bg-emerald-600"
        >
          View laboratory reports
        </Link>
      </div>
    </section>
  );
}

// --- HealthTrends ---
// What it does: Primary longitudinal trend viewer plotting chronological biomarker measurements and clinical records.
// Why it's structured this way: Uses Promise.allSettled to gracefully render available charts even if one data source fails.
// Parameters & Returns: Props (none) -> Rendered health trends dashboard JSX.
// ------------------------------------------------------------------------------
export default function HealthTrends() {
  const { isDark: darkMode, toggleTheme } = useTheme();
  const [dashboardData, setDashboardData] = React.useState(null);
  const [labReports, setLabReports] = React.useState([]);
  const [medicalRecords, setMedicalRecords] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let isMounted = true;
    Promise.allSettled([
      patientService.getDashboardSummary(),
      patientService.getLabReports(),
      patientService.getMedicalRecords(),
    ]).then(([dashRes, labRes, recRes]) => {
      if (!isMounted) return;
      if (dashRes.status === "fulfilled") setDashboardData(dashRes.value);
      if (labRes.status === "fulfilled") {
        const raw = labRes.value?.results || labRes.value || [];
        setLabReports(Array.isArray(raw) ? raw : []);
      }
      if (recRes.status === "fulfilled") {
        const raw = recRes.value?.results || recRes.value || [];
        setMedicalRecords(Array.isArray(raw) ? raw : []);
      }
      setLoading(false);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const measurementRows = React.useMemo(() => {
    const list = [];
    medicalRecords.forEach((r) => {
      list.push({
        label: r.title || r.record_type || "Medical Record",
        date: r.recorded_at
          ? new Date(r.recorded_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })
          : "Recorded",
        value: r.record_type || "Clinical Record",
      });
    });
    labReports.forEach((l) => {
      list.push({
        label: l.title || "Lab Diagnostic Report",
        date: l.uploaded_at
          ? new Date(l.uploaded_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })
          : "Uploaded",
        value: l.file_type || "Laboratory File",
      });
    });
    return list;
  }, [medicalRecords, labReports]);

  return (
    <div
      className={`h-screen w-full overflow-hidden p-2 transition-colors duration-200 ${
        darkMode
          ? "bg-[#0b1413]"
          : "bg-slate-100"
      }`}
    >
      <div
        className={`relative flex h-full w-full overflow-hidden rounded-[18px] border transition-colors duration-200 ${
          darkMode
            ? "border-slate-800 bg-[#111c1b]"
            : "border-slate-200 bg-white"
        }`}
      >
        {/* UNIVERSAL SIDEBAR */}
        <Sidebar darkMode={darkMode} />

        {/* MAIN CONTENT */}
        <main className="ml-[255px] flex min-w-0 flex-1 flex-col overflow-hidden">
          <Header
            darkMode={darkMode}
            toggleTheme={toggleTheme}
          />

          <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-6 pb-3 pt-3">
            {/* METRIC CARDS */}

            <div className="grid shrink-0 grid-cols-3 gap-3">
              {/* DIAGNOSTIC REPORTS */}

              <MetricCard
                darkMode={darkMode}
                icon={
                  <Activity
                    size={17}
                    className="text-emerald-500"
                  />
                }
                label="Lab Diagnostic Reports"
                value={dashboardData?.lab_reports_count ?? labReports.length}
                unit="reports"
                badge={labReports.length > 0 ? "Synchronized" : "Empty"}
              />

              {/* ACTIVE MEDICATIONS */}

              <MetricCard
                darkMode={darkMode}
                icon={
                  <Thermometer
                    size={17}
                    className="text-emerald-500"
                  />
                }
                label="Active Medications"
                value={dashboardData?.active_medications_count ?? 0}
                unit="prescriptions"
                badge={dashboardData?.active_medications_count > 0 ? "Active" : "None"}
              />

              {/* RECORDED MEASUREMENTS */}

              <MetricCard
                darkMode={darkMode}
                icon={
                  <ClipboardList
                    size={17}
                    className="text-emerald-500"
                  />
                }
                label="Total Medical Records"
                value={dashboardData?.medical_records_count ?? medicalRecords.length}
                unit="records"
                badge="Updated"
              />
            </div>

            {/* MAIN GRID */}

            <div className="mt-3 grid min-h-0 flex-1 grid-cols-[1.72fr_0.78fr] gap-3">
              {/* LEFT COLUMN */}

              <div className="flex min-h-0 min-w-0 flex-col gap-3">
                <BloodGlucoseCard
                  darkMode={darkMode}
                  data={[]}
                />

                <div className="min-h-[260px] flex-1">
                  <RecentMeasurements
                    darkMode={darkMode}
                    rows={measurementRows}
                  />
                </div>
              </div>

              {/* RIGHT COLUMN */}

              <div className="min-h-0">
                <AIInsight
                  darkMode={darkMode}
                  latestReport={labReports[0]}
                />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}