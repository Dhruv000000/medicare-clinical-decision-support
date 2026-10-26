# ==============================================================================
# FILE: backend/apps/doctors/urls.py
# PURPOSE: URL routing configuration for the clinician portal and decision support endpoints.
# VIVA EXPLANATION: Maps HTTP endpoints to clinician profile, patient management, lab reports, clinical notes, and analytical insights views under /api/v1/doctor/.
# ==============================================================================

from django.urls import path
from apps.appointments.views import AppointmentDetailView
from .views import (
    DoctorProfileView,
    DoctorPublicListView,
    PatientsView,
    PatientDetailView,
    PatientRecordsView,
    PatientReportsView,
    PatientClinicalNotesView,
    AppointmentsView,
    InsightsView,
)

urlpatterns = [
    path("profile/", DoctorProfileView.as_view(), name="doctor-profile"),
    path("list/", DoctorPublicListView.as_view(), name="doctor-list"),
    path("dashboard/", InsightsView.as_view(), name="doctor-dashboard"),
    path("patients/", PatientsView.as_view(), name="doctor-patients"),
    path("patients/<int:patient_id>/", PatientDetailView.as_view(), name="doctor-patient-detail"),
    path("patients/<int:patient_id>/records/", PatientRecordsView.as_view(), name="doctor-patient-records"),
    path("patients/<int:patient_id>/reports/", PatientReportsView.as_view(), name="doctor-patient-reports"),
    path("patients/<int:patient_id>/clinical-notes/", PatientClinicalNotesView.as_view(), name="doctor-patient-notes"),
    path("appointments/", AppointmentsView.as_view(), name="doctor-appointments"),
    path("appointments/<int:appointment_id>/", AppointmentDetailView.as_view(), name="doctor-appointment-detail"),
    path("insights/", InsightsView.as_view(), name="doctor-insights"),
]
