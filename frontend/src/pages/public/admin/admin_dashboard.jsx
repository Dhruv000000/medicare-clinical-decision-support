// ==============================================================================
// FILE: frontend/src/pages/public/admin/admin_dashboard.jsx
// PURPOSE: Administrative control center for platform telemetry, role governance, and HIPAA audit trail oversight.
// VIVA EXPLANATION: This interface provides clinical system administrators with deep observability. It visualizes platform activity analytics, allows administrators to activate or suspend user accounts, and inspects immutable server-side security audit logs (USER_LOGIN, RECORD_VIEW, CLINICAL_NOTE_CREATE).
// ==============================================================================

import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Users,
  Activity,
  ShieldCheck,
  FileText,
  Calendar,
  Lock,
  LogOut,
  Search,
  Filter,
  Sun,
  Moon,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  RefreshCw,
  Heart,
  ChevronRight,
  Database,
  Sliders,
} from "lucide-react";
import { useAuth } from "../../../_core/hooks/useAuth";
import adminService from "../../../services/adminService";

// --- AdminDashboard ---
// What it does: Central administrative portal managing system telemetry metrics, user access controls, and security audit log inspection.
// Why it's structured this way: Utilizes tabbed navigation (overview, users, audit) and concurrently queries administrative endpoints via Promise.all.
// Parameters & Returns: None. Returns administrative management console JSX.
// ------------------------------------------------------------------------------
export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window === "undefined") return false;
    const saved = localStorage.getItem("medicare-theme");
    return saved === "dark";
  });

  useEffect(() => {
    localStorage.setItem("medicare-theme", darkMode ? "dark" : "light");
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  const [activeTab, setActiveTab] = useState("overview"); // 'overview', 'users', 'audit'
  const [analytics, setAnalytics] = useState(null);
  const [usersList, setUsersList] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  // Filters
  const [userRoleFilter, setUserRoleFilter] = useState("All");
  const [userSearch, setUserSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("All");

  const loadData = async () => {
    try {
      setError("");
      const [analyticsData, usersData, auditData] = await Promise.all([
        adminService.getAnalytics().catch((e) => {
          console.warn("Analytics fetch error:", e);
          return null;
        }),
        adminService.getUsers().catch((e) => {
          console.warn("Users fetch error:", e);
          return { results: [] };
        }),
        adminService.getAuditLogs().catch((e) => {
          console.warn("Audit logs fetch error:", e);
          return { results: [] };
        }),
      ]);

      if (analyticsData) setAnalytics(analyticsData);
      setUsersList(Array.isArray(usersData) ? usersData : usersData?.results || []);
      setAuditLogs(Array.isArray(auditData) ? auditData : auditData?.results || []);
    } catch (err) {
      console.error("Failed to load admin data:", err);
      setError("Failed to load administrative console data from backend.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const handleToggleUserStatus = async (targetUser) => {
    try {
      await adminService.updateUserStatus(targetUser.id, {
        is_active: !targetUser.is_active,
      });
      // Refresh local user list
      setUsersList((prev) =>
        prev.map((u) =>
          u.id === targetUser.id ? { ...u, is_active: !u.is_active } : u
        )
      );
    } catch (err) {
      console.error("Failed to toggle user status:", err);
      alert("Failed to update user account status.");
    }
  };

  const filteredUsers = useMemo(() => {
    const q = userSearch.trim().toLowerCase();
    return usersList.filter((u) => {
      const matchesRole = userRoleFilter === "All" || u.role === userRoleFilter.toLowerCase();
      const name = `${u.first_name || ""} ${u.last_name || ""}`.trim();
      const matchesQuery =
        !q ||
        name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        String(u.id).includes(q);
      return matchesRole && matchesQuery;
    });
  }, [usersList, userRoleFilter, userSearch]);

  const filteredAuditLogs = useMemo(() => {
    return auditLogs.filter((log) => {
      if (actionFilter === "All") return true;
      return log.action === actionFilter;
    });
  }, [auditLogs, actionFilter]);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div
      className={`min-h-screen w-full transition-colors duration-200 ${
        darkMode ? "bg-[#0a1210] text-slate-100" : "bg-[#f4f7f6] text-slate-800"
      }`}
    >
      {/* Top Navbar */}
      <header
        className={`sticky top-0 z-40 flex h-16 items-center justify-between border-b px-6 backdrop-blur-md ${
          darkMode
            ? "border-slate-800 bg-[#0e1917]/90"
            : "border-slate-200 bg-white/90"
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500 text-white shadow-sm">
            <Heart size={20} strokeWidth={2.5} />
          </div>
          <span className="text-xl font-black tracking-tight text-emerald-500">
            medicare<span className={darkMode ? "text-white" : "text-slate-900"}>.admin</span>
          </span>
          <span className="ml-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-500">
            Control Console
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleRefresh}
            disabled={refreshing}
            className={`flex h-9 w-9 items-center justify-center rounded-xl border transition ${
              darkMode
                ? "border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
            title="Refresh database records"
          >
            <RefreshCw size={15} className={refreshing ? "animate-spin text-emerald-500" : ""} />
          </button>

          <button
            type="button"
            onClick={() => setDarkMode(!darkMode)}
            className={`flex h-9 w-9 items-center justify-center rounded-xl border transition ${
              darkMode
                ? "border-slate-700 bg-slate-900 text-yellow-300 hover:bg-slate-800"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
            aria-label="Toggle theme"
          >
            {darkMode ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          <div
            className={`flex items-center gap-2 rounded-xl border px-3 py-1.5 ${
              darkMode ? "border-slate-800 bg-slate-900/60" : "border-slate-200 bg-white"
            }`}
          >
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-[10px] font-bold text-white">
              {user?.email?.slice(0, 2).toUpperCase() || "AD"}
            </div>
            <span className="text-xs font-semibold">{user?.email || "Admin"}</span>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-1.5 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-1.5 text-xs font-semibold text-red-500 transition hover:bg-red-500/20"
          >
            <LogOut size={14} />
            <span>Sign out</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto max-w-7xl px-6 py-8">
        {/* Title & Tabs */}
        <div className="flex flex-wrap items-center justify-between gap-4 pb-6">
          <div>
            <h1 className="text-2xl font-black tracking-tight">System Administration & Audit Trail</h1>
            <p className={`mt-1 text-xs ${darkMode ? "text-slate-400" : "text-slate-500"}`}>
              Live operational metrics, user registry management, and server-controlled security logs.
            </p>
          </div>

          {/* Navigation Tabs */}
          <div
            className={`flex rounded-xl border p-1 ${
              darkMode ? "border-slate-800 bg-[#0e1917]" : "border-slate-200 bg-white shadow-sm"
            }`}
          >
            {[
              { id: "overview", label: "Analytics Overview", icon: Activity },
              { id: "users", label: "User Registry", icon: Users },
              { id: "audit", label: "Security Audit Logs", icon: ShieldCheck },
            ].map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition ${
                    active
                      ? "bg-emerald-500 text-white shadow-sm"
                      : darkMode
                      ? "text-slate-400 hover:text-white"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Icon size={14} />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-xs font-medium text-red-500">
            <AlertCircle size={16} className="shrink-0" />
            {error}
          </div>
        )}

        {/* TAB 1: OVERVIEW */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div
                className={`rounded-2xl border p-5 transition-all ${
                  darkMode ? "border-slate-800 bg-[#0e1917]" : "border-slate-200 bg-white shadow-sm"
                }`}
              >
                <div className="flex items-center justify-between text-slate-500">
                  <span className="text-xs font-semibold uppercase tracking-wider">Total Users</span>
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
                    <Users size={16} />
                  </div>
                </div>
                <div className="mt-3 text-3xl font-black tracking-tight">
                  {analytics?.users?.total ?? usersList.length}
                </div>
                <div className="mt-2 flex items-center gap-2 text-xs">
                  <span className="text-emerald-500 font-semibold">
                    {analytics?.users?.active ?? usersList.filter((u) => u.is_active).length} Active
                  </span>
                  <span className={darkMode ? "text-slate-500" : "text-slate-400"}>&bull;</span>
                  <span className={darkMode ? "text-slate-400" : "text-slate-500"}>
                    {analytics?.users?.patients ?? 0} Patients, {analytics?.users?.doctors ?? 0} Doctors
                  </span>
                </div>
              </div>

              <div
                className={`rounded-2xl border p-5 transition-all ${
                  darkMode ? "border-slate-800 bg-[#0e1917]" : "border-slate-200 bg-white shadow-sm"
                }`}
              >
                <div className="flex items-center justify-between text-slate-500">
                  <span className="text-xs font-semibold uppercase tracking-wider">Total Appointments</span>
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500">
                    <Calendar size={16} />
                  </div>
                </div>
                <div className="mt-3 text-3xl font-black tracking-tight">
                  {analytics?.appointments?.total ?? 0}
                </div>
                <div className="mt-2 flex items-center gap-2 text-xs">
                  <span className="text-blue-500 font-semibold">
                    {analytics?.appointments?.by_status?.completed ?? 0} Completed
                  </span>
                  <span className={darkMode ? "text-slate-500" : "text-slate-400"}>&bull;</span>
                  <span className={darkMode ? "text-slate-400" : "text-slate-500"}>
                    {analytics?.appointments?.by_status?.scheduled ?? 0} Scheduled
                  </span>
                </div>
              </div>

              <div
                className={`rounded-2xl border p-5 transition-all ${
                  darkMode ? "border-slate-800 bg-[#0e1917]" : "border-slate-200 bg-white shadow-sm"
                }`}
              >
                <div className="flex items-center justify-between text-slate-500">
                  <span className="text-xs font-semibold uppercase tracking-wider">Clinical Records</span>
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-500">
                    <FileText size={16} />
                  </div>
                </div>
                <div className="mt-3 text-3xl font-black tracking-tight">
                  {(analytics?.clinical_data?.medical_records ?? 0) +
                    (analytics?.clinical_data?.lab_reports ?? 0)}
                </div>
                <div className="mt-2 flex items-center gap-2 text-xs">
                  <span className="text-indigo-500 font-semibold">
                    {analytics?.clinical_data?.lab_reports ?? 0} Lab Reports
                  </span>
                  <span className={darkMode ? "text-slate-500" : "text-slate-400"}>&bull;</span>
                  <span className={darkMode ? "text-slate-400" : "text-slate-500"}>
                    {analytics?.clinical_data?.medications ?? 0} Prescriptions
                  </span>
                </div>
              </div>

              <div
                className={`rounded-2xl border p-5 transition-all ${
                  darkMode ? "border-slate-800 bg-[#0e1917]" : "border-slate-200 bg-white shadow-sm"
                }`}
              >
                <div className="flex items-center justify-between text-slate-500">
                  <span className="text-xs font-semibold uppercase tracking-wider">Audit Trail Events</span>
                  <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-500/10 text-amber-500">
                    <ShieldCheck size={16} />
                  </div>
                </div>
                <div className="mt-3 text-3xl font-black tracking-tight">
                  {analytics?.clinical_data?.audit_logs_count ?? auditLogs.length}
                </div>
                <div className="mt-2 text-xs text-amber-500 font-semibold">
                  Immutable Server-Enforced Logging
                </div>
              </div>
            </div>

            {/* Platform Health & Breakdown Grid */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* User Roles Breakdown */}
              <div
                className={`rounded-2xl border p-6 ${
                  darkMode ? "border-slate-800 bg-[#0e1917]" : "border-slate-200 bg-white shadow-sm"
                }`}
              >
                <div className="flex items-center justify-between border-b pb-4 dark:border-slate-800">
                  <h3 className="font-bold text-sm">User Role Breakdown</h3>
                  <Database size={15} className="text-emerald-500" />
                </div>
                <div className="mt-5 space-y-4">
                  {[
                    { label: "Patients", count: analytics?.users?.patients ?? 0, color: "bg-emerald-500" },
                    { label: "Doctors", count: analytics?.users?.doctors ?? 0, color: "bg-blue-500" },
                    { label: "Administrators", count: analytics?.users?.admins ?? 0, color: "bg-amber-500" },
                  ].map((role) => {
                    const total = analytics?.users?.total || 1;
                    const pct = Math.round((role.count / total) * 100);
                    return (
                      <div key={role.label}>
                        <div className="flex justify-between text-xs font-semibold">
                          <span>{role.label}</span>
                          <span>
                            {role.count} ({pct}%)
                          </span>
                        </div>
                        <div className={`mt-1.5 h-2 w-full rounded-full ${darkMode ? "bg-slate-800" : "bg-slate-100"}`}>
                          <div
                            className={`h-2 rounded-full ${role.color}`}
                            style={{ width: `${Math.max(5, pct)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Appointment Status Distribution */}
              <div
                className={`rounded-2xl border p-6 ${
                  darkMode ? "border-slate-800 bg-[#0e1917]" : "border-slate-200 bg-white shadow-sm"
                }`}
              >
                <div className="flex items-center justify-between border-b pb-4 dark:border-slate-800">
                  <h3 className="font-bold text-sm">Appointment Operational Status</h3>
                  <Calendar size={15} className="text-blue-500" />
                </div>
                <div className="mt-5 grid grid-cols-2 gap-3">
                  {[
                    { label: "Scheduled", val: analytics?.appointments?.by_status?.scheduled ?? 0, color: "text-amber-500" },
                    { label: "Confirmed", val: analytics?.appointments?.by_status?.confirmed ?? 0, color: "text-emerald-500" },
                    { label: "Completed", val: analytics?.appointments?.by_status?.completed ?? 0, color: "text-blue-500" },
                    { label: "Cancelled", val: analytics?.appointments?.by_status?.cancelled ?? 0, color: "text-red-500" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className={`rounded-xl border p-3.5 ${
                        darkMode ? "border-slate-800 bg-[#09110f]" : "border-slate-100 bg-slate-50"
                      }`}
                    >
                      <p className="text-[10px] uppercase font-bold tracking-wider text-slate-500">{item.label}</p>
                      <p className={`mt-1 text-2xl font-black ${item.color}`}>{item.val}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: USER REGISTRY */}
        {activeTab === "users" && (
          <div
            className={`rounded-2xl border overflow-hidden ${
              darkMode ? "border-slate-800 bg-[#0e1917]" : "border-slate-200 bg-white shadow-sm"
            }`}
          >
            {/* User Filters Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b p-4 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Users size={16} className="text-emerald-500" />
                <span className="font-bold text-sm">Platform Users Registry</span>
                <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-500">
                  {filteredUsers.length} Users
                </span>
              </div>

              <div className="flex items-center gap-3">
                <div
                  className={`flex h-9 items-center gap-2 rounded-xl border px-3 text-xs ${
                    darkMode ? "border-slate-700 bg-slate-900" : "border-slate-200 bg-slate-50"
                  }`}
                >
                  <Search size={14} className="text-slate-400" />
                  <input
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    placeholder="Search by name, email, ID..."
                    className="bg-transparent outline-none placeholder:text-slate-400"
                  />
                </div>

                <select
                  value={userRoleFilter}
                  onChange={(e) => setUserRoleFilter(e.target.value)}
                  className={`h-9 rounded-xl border px-3 text-xs outline-none ${
                    darkMode ? "border-slate-700 bg-slate-900" : "border-slate-200 bg-white"
                  }`}
                >
                  <option value="All">All Roles</option>
                  <option value="patient">Patients</option>
                  <option value="doctor">Doctors</option>
                  <option value="admin">Administrators</option>
                </select>
              </div>
            </div>

            {/* Users Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead
                  className={`border-b text-[10px] font-bold uppercase tracking-wider ${
                    darkMode ? "border-slate-800 bg-slate-900/50 text-slate-400" : "border-slate-100 bg-slate-50 text-slate-500"
                  }`}
                >
                  <tr>
                    <th className="px-5 py-3">User ID</th>
                    <th className="px-5 py-3">Name</th>
                    <th className="px-5 py-3">Email</th>
                    <th className="px-5 py-3">Role</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-slate-800/60">
                  {filteredUsers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-5 py-8 text-center text-slate-500">
                        No users found matching query.
                      </td>
                    </tr>
                  ) : (
                    filteredUsers.map((u) => (
                      <tr
                        key={u.id}
                        className={`transition ${
                          darkMode ? "hover:bg-slate-900/30" : "hover:bg-slate-50/80"
                        }`}
                      >
                        <td className="px-5 py-3 font-mono text-slate-400">#{u.id}</td>
                        <td className="px-5 py-3 font-semibold">
                          {u.first_name || u.last_name
                            ? `${u.first_name || ""} ${u.last_name || ""}`.trim()
                            : "—"}
                        </td>
                        <td className="px-5 py-3">{u.email}</td>
                        <td className="px-5 py-3">
                          <span
                            className={`rounded-md px-2 py-0.5 font-semibold text-[10px] uppercase ${
                              u.role === "doctor"
                                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                : u.role === "admin"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            }`}
                          >
                            {u.role}
                          </span>
                        </td>
                        <td className="px-5 py-3">
                          <span
                            className={`inline-flex items-center gap-1 font-semibold ${
                              u.is_active ? "text-emerald-500" : "text-red-400"
                            }`}
                          >
                            {u.is_active ? (
                              <>
                                <CheckCircle2 size={13} /> Active
                              </>
                            ) : (
                              <>
                                <XCircle size={13} /> Suspended
                              </>
                            )}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-right">
                          <button
                            type="button"
                            onClick={() => handleToggleUserStatus(u)}
                            className={`rounded-lg border px-2.5 py-1 text-[10px] font-semibold transition ${
                              u.is_active
                                ? "border-red-500/20 text-red-400 hover:bg-red-500/10"
                                : "border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/10"
                            }`}
                          >
                            {u.is_active ? "Suspend Access" : "Activate User"}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: AUDIT TRAIL LOGS */}
        {activeTab === "audit" && (
          <div
            className={`rounded-2xl border overflow-hidden ${
              darkMode ? "border-slate-800 bg-[#0e1917]" : "border-slate-200 bg-white shadow-sm"
            }`}
          >
            {/* Audit Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b p-4 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck size={16} className="text-amber-500" />
                <span className="font-bold text-sm">Server-Controlled Security Audit Trail</span>
                <span className="rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-500">
                  {filteredAuditLogs.length} Events
                </span>
              </div>

              <div className="flex items-center gap-3">
                <select
                  value={actionFilter}
                  onChange={(e) => setActionFilter(e.target.value)}
                  className={`h-9 rounded-xl border px-3 text-xs outline-none ${
                    darkMode ? "border-slate-700 bg-slate-900" : "border-slate-200 bg-white"
                  }`}
                >
                  <option value="All">All Actions</option>
                  <option value="USER_LOGIN">USER_LOGIN</option>
                  <option value="RECORD_VIEW">RECORD_VIEW</option>
                  <option value="RECORD_UPDATE">RECORD_UPDATE</option>
                  <option value="CLINICAL_NOTE_CREATE">CLINICAL_NOTE_CREATE</option>
                  <option value="PASSWORD_CHANGE">PASSWORD_CHANGE</option>
                </select>
              </div>
            </div>

            {/* Audit Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead
                  className={`border-b text-[10px] font-bold uppercase tracking-wider ${
                    darkMode ? "border-slate-800 bg-slate-900/50 text-slate-400" : "border-slate-100 bg-slate-50 text-slate-500"
                  }`}
                >
                  <tr>
                    <th className="px-5 py-3">Timestamp</th>
                    <th className="px-5 py-3">Actor Email</th>
                    <th className="px-5 py-3">Action</th>
                    <th className="px-5 py-3">Resource Target</th>
                    <th className="px-5 py-3">IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y dark:divide-slate-800/60">
                  {filteredAuditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-5 py-8 text-center text-slate-500">
                        No audit events recorded matching filter.
                      </td>
                    </tr>
                  ) : (
                    filteredAuditLogs.map((log) => {
                      const dt = new Date(log.created_at);
                      return (
                        <tr
                          key={log.id}
                          className={`transition ${
                            darkMode ? "hover:bg-slate-900/30" : "hover:bg-slate-50/80"
                          }`}
                        >
                          <td className="px-5 py-3 text-slate-400 font-mono text-[11px]">
                            {!isNaN(dt.getTime())
                              ? `${dt.toLocaleDateString()} ${dt.toLocaleTimeString()}`
                              : "Recent"}
                          </td>
                          <td className="px-5 py-3 font-semibold">{log.user_email || log.user || "System"}</td>
                          <td className="px-5 py-3">
                            <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[10px] font-semibold text-emerald-400">
                              {log.action}
                            </span>
                          </td>
                          <td className="px-5 py-3 text-slate-400">
                            {log.resource_type ? `${log.resource_type} (#${log.resource_id})` : "General"}
                          </td>
                          <td className="px-5 py-3 font-mono text-[11px] text-slate-400">
                            {log.ip_address || "127.0.0.1"}
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
