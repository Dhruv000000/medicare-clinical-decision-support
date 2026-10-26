# ==============================================================================
# FILE: backend/apps/patients/urls.py
# PURPOSE: URL routing configuration for the patient self-service portal.
# VIVA EXPLANATION: Directs patient requests under /api/v1/patient/ to their appropriate endpoints, including demographic profile, dashboard, appointments, electronic medical records, lab upload, medications, and prediction history.
# ==============================================================================

from django.urls import path
from .views import ProfileView, DashboardView
from apps.appointments.views import AppointmentListCreateView, AppointmentDetailView
from apps.medical_records.views import (
    MedicalRecordListCreateView,
    LabReportListView,
    LabReportUploadView,
)
from apps.medicines.views import MedicationListCreateView
from apps.predictions.views import PredictionListView, SymptomAnalysisListView

urlpatterns = [
    # Profile & Dashboard
    path("profile/", ProfileView.as_view(), name="patient-profile"),
    path("dashboard/", DashboardView.as_view(), name="patient-dashboard"),

    # Appointments
    path("appointments/", AppointmentListCreateView.as_view(), name="patient-appointments"),
    path("appointments/<int:appointment_id>/", AppointmentDetailView.as_view(), name="patient-appointment-detail"),

    # Medical Records & Labs
    path("medical-records/", MedicalRecordListCreateView.as_view(), name="patient-medical-records"),
    path("lab-tests/", LabReportListView.as_view(), name="patient-lab-tests"),
    path("reports/upload/", LabReportUploadView.as_view(), name="patient-report-upload"),

    # Medications
    path("medications/", MedicationListCreateView.as_view(), name="patient-medications"),

    # Prediction History & Symptoms
    path("predictions/", PredictionListView.as_view(), name="patient-predictions"),
    path("symptom-analyses/", SymptomAnalysisListView.as_view(), name="patient-symptom-analyses"),
]
