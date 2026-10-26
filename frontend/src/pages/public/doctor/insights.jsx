// ==============================================================================
// FILE: frontend/src/pages/public/doctor/insights.jsx
// PURPOSE: AI-driven clinical analytics and proactive cohort risk intelligence dashboard for doctors.
// VIVA EXPLANATION: This screen aggregates machine learning predictive outputs across patient populations. It correlates ML risk tiers, highlights anomalies (such as high-risk cardiac or metabolic flags), and computes clinical workload metrics to assist physicians in preventive triage.
// ==============================================================================

import React, { useEffect, useMemo, useState } from "react";
import {
  Search,
  Bell,
  ChevronDown,
  Sparkles,
  Brain,
  AlertTriangle,
  TrendingUp,
  Activity,
  UserRound,
  ArrowRight,
  Clock3,
  ShieldCheck,
  MoreHorizontal,
  SlidersHorizontal,
  Loader2,
} from "lucide-react";

import Sidebar from "./sidebar";
import { useTheme } from "../ThemeContext";
import { useAuth } from "../../../_core/hooks/useAuth";
import doctorService from "../../../services/doctorService";
import api from "../../../services/api";

// --- SeverityBadge ---
// What it does: Displays color-differentiated clinical severity tags (High, Medium, Low).
// Why it's structured this way: Provides rapid visual alerting for urgent or critical diagnostic flags.
// Parameters & Returns: Props: severity (string). Returns styled JSX span tag.
// ------------------------------------------------------------------------------
function SeverityBadge({ severity }) {
  const styles = {
    High: "bg-red-500/10 text-red-500",
    Medium: "bg-amber-500/10 text-amber-500",
    Low: "bg-emerald-500/10 text-emerald-500",
  };

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${
        styles[severity] || styles.Low
      }`}
    >
      {severity}
    </span>
  );
}

// --- TypeIcon ---
// What it does: Maps insight classification categories (Risk Alert, Trend, Prediction) to distinct icons.
// Why it's structured this way: Enhances scannability across heterogeneous AI recommendations.
// Parameters & Returns: Props: type (string). Returns corresponding Lucide icon component.
// ------------------------------------------------------------------------------
function TypeIcon({ type }) {
  if (type === "Risk Alert") {
    return <AlertTriangle size={16} />;
  }

  if (type === "Trend") {
    return <TrendingUp size={16} />;
  }

  if (type === "Prediction") {
    return <Brain size={16} />;
  }

  return <Sparkles size={16} />;
}

// --- AIInsights ---
// What it does: Primary clinical intelligence console orchestrating cohort metrics, ML prediction aggregation, and risk filtering.
// Why it's structured this way: Combines doctorService dashboard metrics with batch prediction endpoints to display synthesized decision-support insights.
// Parameters & Returns: None. Returns AI clinical intelligence dashboard JSX.
// ------------------------------------------------------------------------------
export default function AIInsights() {
  const { isDark, toggleTheme } = useTheme();
  const { user } = useAuth();

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [loading, setLoading] = useState(true);

  const [metrics, setMetrics] = useState({
    total_patients: 0,
    today_appointments_count: 0,
    completed_appointments_count: 0,
    total_appointments_count: 0,
    clinical_notes_recorded: 0,
  });
  const [insights, setInsights] = useState([]);

  const loadInsightsData = async () => {
    try {
      setLoading(true);
      const dash = await doctorService.getDashboard();
      if (dash) setMetrics(dash);

      const patientsData = await doctorService.getPatients();
      const patientList = Array.isArray(patientsData) ? patientsData : patientsData?.results || [];

      const collected = [];
      for (const p of patientList) {
        try {
          const res = await api.get("/predictions/", { params: { patient_id: p.id } });
          const preds = Array.isArray(res.data) ? res.data : res.data?.results || [];
          preds.forEach((pred) => {
            const riskNorm = (pred.risk_level || "low").toLowerCase();
            const severity =
              riskNorm === "high" || riskNorm === "critical"
                ? "High"
                : riskNorm === "medium" || riskNorm === "moderate"
                ? "Medium"
                : "Low";
            const type = severity === "High" ? "Risk Alert" : "Prediction";
            const created = new Date(pred.created_at);
            collected.push({
              id: `AI-${pred.id}`,
              patient: `${p.first_name || ""} ${p.last_name || ""}`.trim() || p.email,
              type,
              title: `${pred.predicted_disease || "Diagnostic Risk"} Assessment`,
              description: `Automated disease risk stratification for ${
                pred.predicted_disease || "condition"
              } calculated from reported symptom vectors.`,
              severity,
              confidence: `${Math.round((pred.confidence_score || 0.85) * 100)}%`,
              time: !isNaN(created.getTime())
                ? created.toLocaleDateString("en-US", { month: "short", day: "numeric" })
                : "Recent",
            });
          });
        } catch (e) {
          console.warn(`Could not load predictions for patient ${p.id}:`, e);
        }
      }
      setInsights(collected);
    } catch (err) {
      console.error("Failed to load doctor insights:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInsightsData();
  }, []);

  const runAnalysis = async () => {
    if (isAnalyzing) return;
    setIsAnalyzing(true);
    await loadInsightsData();
    setIsAnalyzing(false);
  };

  const doctorName = user?.last_name
    ? `Dr. ${user.last_name}`
    : user?.first_name
    ? `Dr. ${user.first_name}`
    : user?.full_name
    ? `Dr. ${user.full_name}`
    : "Doctor";

  const highRiskCount = insights.filter((i) => i.severity === "High").length;

  const filteredInsights = useMemo(() => {
    const query = search.trim().toLowerCase();

    return insights.filter((item) => {
      const matchesSearch =
        !query ||
        item.patient.toLowerCase().includes(query) ||
        item.title.toLowerCase().includes(query) ||
        item.description.toLowerCase().includes(query);

      const matchesFilter = filter === "All" || item.severity === filter;

      return matchesSearch && matchesFilter;
    });
  }, [insights, search, filter]);

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
            <h1 className="text-[26px] font-bold tracking-tight">AI Insights</h1>

            <div className="flex items-center gap-3">
              <div className="hidden h-10 w-[280px] items-center gap-3 rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] px-4 md:flex">
                <Search size={18} className="text-[var(--muted)]" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search insights, patients, conditions..."
                  className="w-full bg-transparent text-sm outline-none placeholder:text-[var(--muted)]"
                />
              </div>

              <button
                type="button"
                onClick={toggleTheme}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border-soft)] bg-[var(--card-soft)] text-[var(--accent)]"
              >
                <span className="text-xl">{isDark ? "☼" : "☾"}</span>
              </button>

              <button
                type="button"
                className="relative p-2 text-[var(--text-secondary)]"
              >
                <Bell size={20} />
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[var(--accent)]" />
              </button>

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
                <div className="flex items-center gap-2">
                  <h2 className="text-[22px] font-bold">Clinical Intelligence</h2>
                  <span className="flex items-center gap-1 rounded-full bg-[var(--accent-soft)] px-2 py-1 text-[10px] font-semibold text-[var(--accent)]">
                    <Sparkles size={11} />
                    XGBoost & TreeSHAP
                  </span>
                </div>

                <p className="mt-1 text-sm text-[var(--muted)]">
                  Database-grounded diagnostic insights, risk stratifications, and EHR signals across your patient roster.
                </p>
              </div>

              <button
                type="button"
                onClick={runAnalysis}
                disabled={isAnalyzing}
                className="hidden shrink-0 items-center gap-2 rounded-xl bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-[#06231d] transition hover:brightness-105 disabled:cursor-wait disabled:opacity-70 sm:flex"
              >
                <Brain size={16} className={isAnalyzing ? "animate-pulse" : ""} />
                {isAnalyzing ? "Refreshing..." : "Refresh Insights"}
              </button>
            </div>

            {/* SUMMARY CARDS */}
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Active Insights</span>
                  <Sparkles size={17} className="text-[var(--accent)]" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(insights.length).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-emerald-500">Evaluated predictions</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">High Risk</span>
                  <AlertTriangle size={17} className="text-red-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(highRiskCount).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-red-500">Requires clinical attention</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Authorized Patients</span>
                  <ShieldCheck size={17} className="text-emerald-500" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(metrics.total_patients).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-emerald-500">In your roster</p>
              </div>

              <div className="rounded-2xl border border-[var(--border)] bg-[var(--card)] px-4 py-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[var(--muted)]">Today's Visits</span>
                  <Activity size={17} className="text-[var(--accent)]" />
                </div>
                <p className="mt-2 text-2xl font-bold">
                  {String(metrics.today_appointments_count).padStart(2, "0")}
                </p>
                <p className="mt-1 text-[10px] text-[var(--muted)]">Scheduled visits</p>
              </div>
            </div>

            {/* INSIGHT LIST */}
            <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--card)]">
              {/* TOOLBAR */}
              <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal size={16} className="text-[var(--muted)]" />
                  <span className="text-sm font-medium">Recent Insights</span>
                  <span className="rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-medium text-[var(--accent)]">
                    {filteredInsights.length}
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  {["All", "High", "Medium", "Low"].map((item) => (
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

              {/* LIST */}
              <div className="min-h-0 flex-1 overflow-y-auto">
                {loading ? (
                  <div className="flex h-full min-h-[220px] flex-col items-center justify-center">
                    <Loader2 size={24} className="animate-spin text-[var(--accent)]" />
                    <p className="mt-2 text-xs text-[var(--muted)]">Loading clinical AI insights from database...</p>
                  </div>
                ) : filteredInsights.length === 0 ? (
                  <div className="flex h-full min-h-[220px] items-center justify-center">
                    <div className="text-center">
                      <Brain size={34} className="mx-auto text-[var(--muted)]" />
                      <p className="mt-3 text-sm font-medium">No patient AI insights found</p>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        When patients undergo automated symptom assessments or prediction evaluations, diagnostic signals will appear here.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="grid min-h-full grid-cols-1">
                    {filteredInsights.map((item) => (
                      <div
                        key={item.id}
                        className="group flex min-h-[78px] items-center gap-4 border-b border-[var(--border)] px-4 transition hover:bg-[var(--card-soft)] last:border-b-0"
                      >
                        {/* ICON */}
                        <div
                          className={`
                            flex h-10 w-10 shrink-0 items-center justify-center rounded-xl
                            ${
                              item.severity === "High"
                                ? "bg-red-500/10 text-red-500"
                                : item.severity === "Medium"
                                ? "bg-amber-500/10 text-amber-500"
                                : "bg-emerald-500/10 text-emerald-500"
                            }
                          `}
                        >
                          <TypeIcon type={item.type} />
                        </div>

                        {/* CONTENT */}
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="truncate text-sm font-semibold">{item.title}</p>
                            <span className="hidden shrink-0 text-[10px] text-[var(--muted)] lg:inline">
                              {item.type}
                            </span>
                          </div>
                          <p className="mt-1 truncate text-xs text-[var(--muted)]">{item.description}</p>
                        </div>

                        {/* PATIENT */}
                        <div className="hidden w-[140px] shrink-0 items-center gap-2 xl:flex">
                          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--accent-soft)]">
                            <UserRound size={13} className="text-[var(--accent)]" />
                          </div>
                          <span className="truncate text-xs font-medium">{item.patient}</span>
                        </div>

                        {/* CONFIDENCE */}
                        <div className="hidden w-[72px] shrink-0 md:block">
                          <p className="text-[10px] text-[var(--muted)]">Confidence</p>
                          <p className="mt-0.5 text-xs font-semibold">{item.confidence}</p>
                        </div>

                        {/* TIME */}
                        <div className="hidden w-[85px] shrink-0 lg:flex items-center gap-1 text-[10px] text-[var(--muted)]">
                          <Clock3 size={12} />
                          {item.time}
                        </div>

                        {/* SEVERITY */}
                        <div className="hidden w-[75px] shrink-0 sm:block">
                          <SeverityBadge severity={item.severity} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* FOOTER */}
              <div className="flex shrink-0 items-center justify-between border-t border-[var(--border)] px-4 py-2.5">
                <div className="flex items-center gap-2 text-[10px] text-[var(--muted)]">
                  <ShieldCheck size={13} className="text-emerald-500" />
                  AI insights are clinical decision support tools and do not substitute definitive medical evaluations.
                </div>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}