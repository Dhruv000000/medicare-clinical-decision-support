# ==============================================================================
# FILE: backend/apps/medical_records/urls.py
# PURPOSE: URL routing configuration for medical records, lab report uploads, and biomarker analytics.
# VIVA EXPLANATION: Defines URL routes for EHR consultation records, diagnostic report file uploads, and biomarker analysis triggers under the /api/v1/records/ and /api/v1/medical-records/ namespaces.
# ==============================================================================

from django.urls import path
from .views import (
    MedicalRecordListCreateView,
    MedicalRecordDetailView,
    LabReportListView,
    LabReportUploadView,
    LabReportDetailView,
    MedicalRecordAnalyzeView,
)

# --- urlpatterns ---
# What it does: Registers URL route handlers for clinical records, lab report uploads, and report analysis.
# Why it's structured this way: Follows RESTful URL conventions supporting both records and diagnostic reports.
# Parameters & Returns: List of django.urls.path route objects.
# ------------------------------------------------------------------------------
urlpatterns = [
    path("", MedicalRecordListCreateView.as_view(), name="record-list-create"),
    path("<int:record_id>/", MedicalRecordDetailView.as_view(), name="record-detail"),
    path("<int:record_id>/analyze/", MedicalRecordAnalyzeView.as_view(), name="record-analyze"),
    path("reports/", LabReportListView.as_view(), name="report-list"),
    path("reports/upload/", LabReportUploadView.as_view(), name="report-upload"),
    path("reports/<int:report_id>/", LabReportDetailView.as_view(), name="report-detail"),
    path("reports/<int:record_id>/analyze/", MedicalRecordAnalyzeView.as_view(), name="report-analyze"),
]

