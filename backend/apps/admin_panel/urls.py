# ==============================================================================
# FILE: backend/apps/admin_panel/urls.py
# PURPOSE: URL routing configuration for the system administration back-office.
# VIVA EXPLANATION: Maps admin routes under /api/v1/admin/ to user directory management, audit trail logs, and system analytics views.
# ==============================================================================

from django.urls import path
from .views import (
    AdminUsersView,
    AdminUserDetailView,
    AdminAuditLogsView,
    AdminAnalyticsView,
)

urlpatterns = [
    path("users/", AdminUsersView.as_view(), name="admin-users"),
    path("users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("audit-logs/", AdminAuditLogsView.as_view(), name="admin-audit-logs"),
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
]

