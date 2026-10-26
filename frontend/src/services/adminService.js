// ==============================================================================
// FILE: frontend/src/services/adminService.js
// PURPOSE: Client-side HTTP service facilitating administrator operations and audit inspection.
// VIVA EXPLANATION: Provides API calls for the administrative back-office, including real-time system KPI metrics, user management (modifying roles and active status), and querying immutable security audit logs.
// ==============================================================================

import api from "./api";

export const adminService = {
  // --- getAnalytics ---
  // What it does: Fetches platform-wide operational KPIs and clinical volume metrics.
  // Why it's structured this way: Powers the administrative analytics dashboard view.
  // Parameters & Returns: None -> Aggregated metrics object (users, appointments, clinical records).
  // ------------------------------------------------------------------------------
  async getAnalytics() {
    const response = await api.get("/admin/analytics/");
    return response.data;
  },

  // --- getUsers ---
  // What it does: Retrieves paginated user accounts with role and active status filtering.
  // Why it's structured this way: Populates user management tables with server-side pagination.
  // Parameters & Returns: params ({ role, is_active, page }) -> Paginated user list.
  // ------------------------------------------------------------------------------
  async getUsers(params = {}) {
    const response = await api.get("/admin/users/", { params });
    return response.data;
  },

  // --- updateUserStatus ---
  // What it does: Updates user role, names, or toggles active/disabled account status.
  // Why it's structured this way: Allows administrators to deactivate accounts or promote staff roles.
  // Parameters & Returns: userId (number), payload (object) -> Updated user record.
  // ------------------------------------------------------------------------------
  async updateUserStatus(userId, payload) {
    const response = await api.patch(`/admin/users/${userId}/`, payload);
    return response.data;
  },

  // --- getAuditLogs ---
  // What it does: Queries immutable audit trail events filtered by action or resource type.
  // Why it's structured this way: Provides compliance officers and administrators with forensic audit trails.
  // Parameters & Returns: params ({ action, resource_type, page }) -> Paginated AuditLog objects.
  // ------------------------------------------------------------------------------
  async getAuditLogs(params = {}) {
    const response = await api.get("/admin/audit-logs/", { params });
    return response.data;
  },
};

export default adminService;

