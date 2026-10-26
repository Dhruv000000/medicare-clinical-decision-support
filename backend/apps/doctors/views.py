# ==============================================================================
# FILE: backend/apps/doctors/views.py
# PURPOSE: HTTP REST API controllers for physician profiles, authorized patient charts, and clinical notes.
# VIVA EXPLANATION: Implements the clinician dashboard backend. It strictly enforces the doctor_can_access_patient security boundary so physicians can only view patient charts, medical records, and diagnostic lab reports when an active appointment or note relationship exists.
# ==============================================================================

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from core.permissions import IsDoctor, doctor_can_access_patient, IsAuthenticatedUser
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User
from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentSerializer
from apps.medical_records.models import MedicalRecord, LabReport
from apps.medical_records.serializers import MedicalRecordSerializer, LabReportSerializer
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog

from .models import DoctorProfile, ClinicalNote
from .serializers import (
    DoctorProfileSerializer,
    ClinicalNoteSerializer,
    DoctorPatientSummarySerializer,
)
from .services import get_authorized_patients_for_doctor, get_doctor_insights


# --- get_patient_or_404 ---
# What it does: Helper function resolving patient User by ID or raising HTTP 404 NotFound.
# Why it's structured this way: Enforces role verification ensuring queried ID represents a patient rather than a doctor/admin.
# Parameters & Returns: patient_id -> User instance with role == 'patient'.
# ------------------------------------------------------------------------------
def get_patient_or_404(patient_id):
    try:
        return User.objects.get(id=patient_id, role=User.Roles.PATIENT)
    except (User.DoesNotExist, ValueError):
        raise NotFound(f"Patient with ID {patient_id} does not exist.")


# --- DoctorProfileView ---
# What it does: GET retrieves doctor credentials; PATCH updates bio, specialization, hospital, or experience.
# Why it's structured this way: Uses get_or_create to guarantee profile existence for authenticated clinicians.
# Parameters & Returns: GET/PATCH request -> Serialized DoctorProfile.
# ------------------------------------------------------------------------------
class DoctorProfileView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
        serializer = DoctorProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
        serializer = DoctorProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- DoctorPublicListView ---
# What it does: GET /api/v1/doctor/list/ - Returns directory of active physicians with names, specializations, and licenses.
# Why it's structured this way: Read-only endpoint open to all authenticated users (including patients) to populate appointment booking selectors.
# Parameters & Returns: GET request -> List of doctor profiles with IDs and specialty information.
# ------------------------------------------------------------------------------
class DoctorPublicListView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        doctors = (
            User.objects.filter(role=User.Roles.DOCTOR, is_active=True)
            .select_related("doctor_profile")
            .order_by("last_name", "first_name")
        )
        data = []
        for doc in doctors:
            profile = getattr(doc, "doctor_profile", None)
            data.append({
                "id": doc.id,
                "email": doc.email,
                "first_name": doc.first_name,
                "last_name": doc.last_name,
                "name": f"Dr. {doc.first_name} {doc.last_name}".strip() or doc.email,
                "specialization": profile.specialization if profile else "General Medicine",
                "license_number": profile.license_number if profile else "",
                "experience_years": profile.experience_years if profile else 0,
            })
        return Response(data, status=status.HTTP_200_OK)


# --- PatientsView ---
# What it does: GET /api/v1/doctor/patients/ - Returns paginated list of patients with whom this doctor has active relationships.
# Why it's structured this way: Enforces role security; doctors cannot browse all patients in the system, only assigned/consulting ones.
# Parameters & Returns: GET request with pagination query params -> Paginated DoctorPatientSummarySerializer payload.
# ------------------------------------------------------------------------------
class PatientsView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        patients = get_authorized_patients_for_doctor(request.user)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(patients, request)
        serializer = DoctorPatientSummarySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# --- PatientDetailView ---
# What it does: GET /api/v1/doctor/patients/<id>/ - Returns specific patient demographic and clinical overview.
# Why it's structured this way: Checks doctor_can_access_patient permission guard before returning protected medical data.
# Parameters & Returns: patient_id URL argument -> DoctorPatientSummarySerializer or 403 Forbidden.
# ------------------------------------------------------------------------------
class PatientDetailView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("You are not authorized to view this patient's records.")
        serializer = DoctorPatientSummarySerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- PatientRecordsView ---
# What it does: GET /api/v1/doctor/patients/<id>/records/ - Retrieves chronological EHR records for an authorized patient.
# Why it's structured this way: Applies pagination and verification guards to protect longitudinal medical histories.
# Parameters & Returns: patient_id URL argument -> Paginated MedicalRecordSerializer collection.
# ------------------------------------------------------------------------------
class PatientRecordsView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("You are not authorized to view this patient's records.")

        records = MedicalRecord.objects.filter(patient=patient).order_by("-recorded_at")
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(records, request)
        serializer = MedicalRecordSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# --- PatientReportsView ---
# What it does: GET /api/v1/doctor/patients/<id>/reports/ - Retrieves diagnostic laboratory tests and parsed biomarkers.
# Why it's structured this way: Uses prefetch_related('results') for performance optimization across biomarker sets.
# Parameters & Returns: patient_id URL argument -> Paginated LabReportSerializer results.
# ------------------------------------------------------------------------------
class PatientReportsView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("You are not authorized to view this patient's reports.")

        reports = LabReport.objects.filter(patient=patient).prefetch_related("results").order_by("-uploaded_at")
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(reports, request)
        serializer = LabReportSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# --- PatientClinicalNotesView ---
# What it does: GET lists physician consultation notes; POST creates a new SOAP clinical note and logs an audit trail event.
# Why it's structured this way: Enforces mandatory physician-patient clinical authorization and writes to immutable audit logs.
# Parameters & Returns: patient_id URL argument, POST body (note, diagnosis) -> Created ClinicalNoteSerializer response.
# ------------------------------------------------------------------------------
class PatientClinicalNotesView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("You are not authorized to view this patient's clinical notes.")
        notes = ClinicalNote.objects.filter(doctor=request.user, patient=patient).order_by("-created_at")
        serializer = ClinicalNoteSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")

        note_text = request.data.get("note", "").strip()
        diagnosis = request.data.get("diagnosis", "").strip()

        if not note_text:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "Clinical note content cannot be empty."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        note = ClinicalNote.objects.create(
            doctor=request.user,
            patient=patient,
            diagnosis=diagnosis,
            note=note_text,
        )

        log_audit_event(
            user=request.user,
            action=AuditLog.Actions.CLINICAL_NOTE_CREATE,
            resource_type="ClinicalNote",
            resource_id=note.id,
            request=request,
            metadata={"patient_id": patient.id},
        )

        serializer = ClinicalNoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# --- AppointmentsView ---
# What it does: GET /api/v1/doctor/appointments/ - Lists all scheduled, completed, and pending appointments for this clinician.
# Why it's structured this way: Optimized with select_related for patient/doctor records and ordered chronologically.
# Parameters & Returns: GET request -> Paginated AppointmentSerializer items.
# ------------------------------------------------------------------------------
class AppointmentsView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        appointments = (
            Appointment.objects.filter(doctor=request.user)
            .select_related("patient", "doctor")
            .order_by("starts_at")
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(appointments, request)
        serializer = AppointmentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# --- InsightsView ---
# What it does: GET /api/v1/doctor/insights/ - Computes real clinical KPI metrics, patient volume, and appointment stats.
# Why it's structured this way: Aggregates real DB counts via get_doctor_insights service to drive analytical clinical dashboard.
# Parameters & Returns: GET request -> Dict of statistical metrics (total_patients, pending_reviews, etc.).
# ------------------------------------------------------------------------------
class InsightsView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        insights = get_doctor_insights(request.user)
        return Response(insights, status=status.HTTP_200_OK)

