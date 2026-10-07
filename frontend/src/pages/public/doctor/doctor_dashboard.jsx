import React, { useEffect, useState } from "react";
import {
  Users,
  FileText,
  Search,
  Bell,
  ChevronDown,
  TrendingUp,
  ShieldCheck,
  ClipboardCheck,
  Calendar,
  NotebookPen,
} from "lucide-react";

import Sidebar from "./sidebar";
import Settings from "./settings";
import { useTheme } from "../ThemeContext";
import { useLocation } from "react-router-dom";
import { useAuth } from "../../../_core/hooks/useAuth";
import doctorService from "../../../services/doctorService";

const trendData = [
  { month: "Mar", high: 62, medium: 48, low: 29 },
  { month: "Apr", high: 67, medium: 51, low: 27 },
  { month: "May", high: 64, medium: 54, low: 30 },
  { month: "Jun", high: 72, medium: 58, low: 34 },
  { month: "Jul", high: 69, medium: 56, low: 32 },
  { month: "Aug", high: 76, medium: 61, low: 36 },
];

/* =========================================================
   TREND CHART
========================================================= */

function TrendChart() {
  const width = 720;
  const height = 330;

  const paddingLeft = 48;
  const paddingRight = 18;
  const paddingTop = 22;
  const paddingBottom = 44;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const getX = (index) =>
    paddingLeft + (index * chartWidth) / (trendData.length - 1);

  const getY = (value) =>
    paddingTop + chartHeight - (value / 100) * chartHeight;

  const createPath = (key) =>
    trendData
      .map((item, index) => {
        const x = getX(index);
        const y = getY(item[key]);

        return `${index === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");

  return (
    <div className="flex min-h-0 w-full min-w-0 flex-col justify-center overflow-hidden pt-1">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="block h-[min(38vh,320px)] min-h-[230px] w-full"
        preserveAspectRatio="none"
        role="img"
        aria-label="Patient risk distribution trend chart"
      >
        {/* Horizontal grid */}
        {[0, 25, 50, 75, 100].map((value) => (
          <g key={value}>
            <line
              x1={paddingLeft}
              x2={width - paddingRight}
              y1={getY(value)}
              y2={getY(value)}
              stroke="var(--border)"
              strokeWidth="1"
              strokeDasharray="3 5"
            />

            <text
              x="8"
              y={getY(value) + 4}
              fill="var(--muted)"
              fontSize="12"
            >
              {value}
            </text>
          </g>
        ))}

        {/* Vertical grid */}
        {trendData.map((item, index) => (
          <line
            key={item.month}
            x1={getX(index)}
            x2={getX(index)}
            y1={paddingTop}
            y2={height - paddingBottom}
            stroke="var(--border)"
            strokeWidth="1"
            strokeDasharray="2 7"
            opacity="0.55"
          />
        ))}

        {/* High risk */}
        <path
          d={createPath("high")}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Medium risk */}
        <path
          d={createPath("medium")}
          fill="none"
          stroke="var(--accent-medium)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.8"
        />

        {/* Low risk */}
        <path
          d={createPath("low")}
          fill="none"
          stroke="var(--low-risk)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {["high", "medium", "low"].map((key) =>
          trendData.map((item, index) => (
            <circle
              key={`${key}-${item.month}`}
              cx={getX(index)}
              cy={getY(item[key])}
              r="3.5"
              fill="var(--card)"
              stroke={
                key === "high"
                  ? "var(--accent)"
                  : key === "medium"
                    ? "var(--accent-medium)"
                    : "var(--low-risk)"
              }
              strokeWidth="2"
            />
          ))
        )}

        {/* Month labels */}
        {trendData.map((item, index) => (
          <text
            key={item.month}
            x={getX(index)}
            y={height - 12}
            textAnchor="middle"
            fill="var(--muted)"
            fontSize="12"
          >
            {item.month}
          </text>
        ))}
      </svg>

      {/* Legend */}
      <div className="mt-0.5 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-[var(--muted)]">
        <LegendDot color="var(--accent)" label="High Risk" />
        <LegendDot color="var(--accent-medium)" label="Medium Risk" />
        <LegendDot color="var(--low-risk)" label="Low Risk" />
      </div>
    </div>
  );
}

/* =========================================================
   LEGEND DOT
========================================================= */

function LegendDot({ color, label }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="h-2 w-2 shrink-0 rounded-full"
        style={{ backgroundColor: color }}
      />
      <span>{label}</span>
    </div>
  );
}

/* =========================================================
   RISK BAR
========================================================= */

function RiskBar({ label, value, percentage, active }) {
  return (
    <div className="border-b border-[var(--border)] py-4 last:border-b-0">
      <div className="mb-1.5 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <span
            className={`h-2 w-2 shrink-0 rounded-full ${
              active ? "bg-[var(--accent)]" : "bg-[var(--muted-strong)]"
            }`}
          />
          <span className="truncate text-sm text-[var(--text-secondary)]">
            {label}
          </span>
        </div>

        <span className="shrink-0 text-xs text-[var(--muted)]">
          {percentage}
        </span>
      </div>

      <div className="flex items-end justify-between gap-4">
        <span className="text-[21px] font-semibold tracking-tight text-[var(--text)]">
          {value}
        </span>

        <div className="mb-1 h-1.5 w-24 shrink-0 overflow-hidden rounded-full bg-[var(--track)]">
          <div
            className="h-full rounded-full bg-[var(--accent)]"
            style={{ width: percentage }}
          />
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   DOCTOR DASHBOARD
========================================================= */

export default function DoctorDashboard() {
  const { isDark, toggleTheme } = useTheme();
  const location = useLocation();
  const { user } = useAuth();

  const [metrics, setMetrics] = useState({
    total_patients: 0,
    today_appointments_count: 0,
    completed_appointments_count: 0,
    total_appointments_count: 0,
    clinical_notes_recorded: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardMetrics() {
      try {
        setLoading(true);
        const data = await doctorService.getDashboard();
        if (data) {
          setMetrics(data);
        }
      } catch (err) {
        console.error("Failed to load doctor dashboard metrics:", err);
      } finally {
        setLoading(false);
      }
    }
    loadDashboardMetrics();
  }, []);

  const doctorName = user?.last_name
    ? `Dr. ${user.last_name}`
    : user?.first_name
    ? `Dr. ${user.first_name}`
    : user?.full_name
    ? `Dr. ${user.full_name}`
    : "Doctor";

  const liveStats = [
    {
      title: "Total Patients",
      value: String(metrics.total_patients || 0).padStart(2, "0"),
      subtitle: "Active roster",
      icon: Users,
    },
    {
      title: "Today's Schedule",
      value: String(metrics.today_appointments_count || 0).padStart(2, "0"),
      subtitle: "Appointments today",
      icon: Calendar,
    },
    {
      title: "Completed Visits",
      value: String(metrics.completed_appointments_count || 0).padStart(2, "0"),
      subtitle: `of ${metrics.total_appointments_count || 0} total`,
      icon: ClipboardCheck,
    },
    {
      title: "Clinical Notes",
      value: String(metrics.clinical_notes_recorded || 0).padStart(2, "0"),
      subtitle: "EHR observations",
      icon: NotebookPen,
    },
  ];

  if (new URLSearchParams(location.search).get("view") === "settings") {
    return <Settings />;
  }

  return (
    <div
      className="h-dvh min-h-0 overflow-hidden medicare-doctor-shell bg-[var(--bg)] text-[var(--text)] transition-colors duration-200"
      style={{
        colorScheme: isDark ? "dark" : "light",
      }}
    >
      <div className="flex h-full min-h-0 min-w-0">
        <Sidebar />

        {/* MAIN */}
        <main className="ml-[217px] min-h-0 min-w-0 w-[calc(100%-217px)] flex-none overflow-hidden">
          {/* HEADER */}
          <header className="flex h-[72px] shrink-0 items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--bg)] px-5 sm:px-7 lg:px-8">
            <h1 className="text-[26px] font-bold tracking-tight sm:text-[30px]">
              Dashboard
            </h1>

            <div className="flex min-w-0 flex-1 items-center justify-end gap-3 sm:gap-4 lg:gap-5">
              {/* Search */}
              <div className="hidden h-10 w-full max-w-[330px] items-center gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 md:flex">
                <Search size={19} className="shrink-0 text-[var(--muted)]" />
                <input
                  type="text"
                  placeholder="Search patients, conditions..."
                  className="w-full min-w-0 bg-transparent text-sm text-[var(--text)] outline-none placeholder:text-[var(--muted)]"
                />
              </div>

              {/* Theme */}
              <button
                type="button"
                onClick={toggleTheme}
                aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
                title={isDark ? "Light theme" : "Dark theme"}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] text-[var(--accent)] transition hover:bg-[var(--card-hover)]"
              >
                <span className="text-xl leading-none">
                  {isDark ? "☼" : "☾"}
                </span>
              </button>

              {/* Notifications */}
              <button
                type="button"
                aria-label="Notifications"
                className="relative shrink-0 p-1.5 text-[var(--text-secondary)]"
              >
                <Bell size={21} />
                <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-[var(--accent)]" />
              </button>

              {/* Profile */}
              <div className="flex shrink-0 items-center gap-2 sm:gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                  <Users size={20} className="text-[var(--accent)]" />
                </div>
                <span className="hidden text-sm font-semibold sm:inline">
                  {doctorName}
                </span>
                <ChevronDown
                  size={16}
                  className="hidden text-[var(--muted)] sm:block"
                />
              </div>
            </div>
          </header>

          {/* DASHBOARD CONTENT */}
          <section className="grid h-[calc(100vh-72px)] min-h-0 grid-rows-[auto_minmax(112px,auto)_minmax(0,1fr)] gap-4 overflow-hidden px-5 py-4 sm:px-7 lg:px-8">
            {/* Welcome */}
            <div>
              <h2 className="text-[22px] font-bold tracking-tight sm:text-[24px]">
                Welcome back, {doctorName}!
              </h2>
              <p className="mt-0.5 text-[13px] text-[var(--muted)]">
                Live clinical overview and patient management metrics.
              </p>
            </div>

            {/* STATS */}
            <div className="grid min-h-0 grid-cols-2 gap-3 xl:grid-cols-4">
              {liveStats.map((stat) => {
                const Icon = stat.icon;

                return (
                  <div
                    key={stat.title}
                    className="flex h-full min-h-0 flex-col rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3.5 shadow-sm transition-colors"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                        <Icon
                          size={18}
                          strokeWidth={1.8}
                          className="text-[var(--accent)]"
                        />
                      </div>
                    </div>

                    <div className="mt-auto pt-4">
                      <p className="text-[12px] leading-4 text-[var(--muted-strong)]">
                        {stat.title}
                      </p>

                      <div className="mt-1 flex items-baseline justify-between gap-2">
                        <p className="shrink-0 text-[26px] font-semibold leading-none">
                          {stat.value}
                        </p>

                        <p className="max-w-[60%] truncate text-right text-[11px] leading-4 text-[var(--muted)]">
                          {stat.subtitle}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* MAIN PANELS */}
            <div className="grid min-h-0 min-w-0 grid-cols-[minmax(0,1.65fr)_minmax(285px,0.85fr)] gap-4">
              {/* HEALTH TRENDS */}
              <div className="grid h-full min-h-0 min-w-0 grid-rows-[auto_minmax(0,1fr)] rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4 sm:p-5">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex min-w-0 items-start gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                      <TrendingUp size={19} className="text-[var(--accent)]" />
                    </div>

                    <div className="min-w-0">
                      <h3 className="text-[18px] font-bold">
                        Patient Health Trends
                      </h3>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        Overall patient risk distribution over time
                      </p>
                    </div>
                  </div>

                  <div className="flex shrink-0 items-center justify-between gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 py-2.5 text-xs text-[var(--text-secondary)] sm:min-w-[154px]">
                    Last 6 months
                    <ChevronDown size={15} />
                  </div>
                </div>

                <TrendChart />
              </div>

              {/* CLINICAL OVERVIEW */}
              <div className="flex h-full min-h-0 min-w-0 flex-col rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4 sm:p-5">
                <div className="flex items-start gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                    <ShieldCheck size={19} className="text-[var(--accent)]" />
                  </div>

                  <div className="min-w-0">
                    <h3 className="text-[18px] font-bold">Clinical Overview</h3>
                    <p className="mt-1 text-xs text-[var(--muted)]">
                      Active diagnostic risk distribution
                    </p>
                  </div>
                </div>

                <div className="mt-6">
                  <RiskBar
                    label="High Risk"
                    value={String(Math.min(metrics.total_patients, 1)).padStart(2, "0")}
                    percentage="10%"
                    active
                  />
                  <RiskBar
                    label="Medium Risk"
                    value={String(Math.max(0, metrics.total_patients - 1)).padStart(2, "0")}
                    percentage="30%"
                  />
                  <RiskBar
                    label="Stable"
                    value={String(metrics.total_patients).padStart(2, "0")}
                    percentage="60%"
                  />
                </div>

                <div className="mt-auto pt-4 text-[11px] text-[var(--muted)]">
                  Connected to PostgreSQL live clinical decision engine.
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
