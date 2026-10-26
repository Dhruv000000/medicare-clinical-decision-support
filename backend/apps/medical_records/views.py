# ==============================================================================
# FILE: backend/apps/medical_records/views.py
# PURPOSE: HTTP REST API controllers for EHR medical records, lab report uploads, and biomarker analytics.
# VIVA EXPLANATION: This module handles medical document workflows. It enforces clinical authorization barriers so clinicians can only review authorized patient charts, accepts diagnostic document uploads, and triggers automated biomarker NLP parsing that extracts laboratory values into structured clinical records.
# ==============================================================================

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError

from core.permissions import IsAuthenticatedUser, IsPatient, doctor_can_access_patient
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog

from .models import MedicalRecord, LabReport
from .serializers import MedicalRecordSerializer, LabReportSerializer
from .services import (
    save_lab_report,
    analyze_and_sync_record_or_report,
)

logger = logging.getLogger(__name__)


# --- MedicalRecordListCreateView ---
# What it does: GET lists medical records with role-based filtering; POST creates a new medical record.
# Why it's structured this way: Enforces strict data access rules: patients see only their own records, doctors only authorized patients.
# Parameters & Returns: GET/POST request -> Paginated list or created MedicalRecord.
# ------------------------------------------------------------------------------
class MedicalRecordListCreateView(APIView):
    """
    GET /api/v1/records/  — Retrieves patient medical records with role-based filtering.
    POST /api/v1/records/ — Creates a new medical record for authorized patients or doctors.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        """
        Lists medical records for the authenticated user:
        - Patients only see their own records.
        - Doctors must supply 'patient_id' and have active authorization.
        - Admins can query all records.
        """
        user = request.user
        queryset = MedicalRecord.objects.select_related("patient")

        if user.role == User.Roles.PATIENT:
            queryset = queryset.filter(patient=user)
        elif user.role == User.Roles.DOCTOR:
            patient_id = request.query_params.get("patient_id")
            if not patient_id:
                raise ValidationError("Doctors must supply a 'patient_id' query parameter.")
            try:
                patient = User.objects.get(id=patient_id, role=User.Roles.PATIENT)
            except User.DoesNotExist:
                raise NotFound("Patient not found.")
            if not doctor_can_access_patient(user, patient):
                raise PermissionDenied("You are not authorized to access this patient's records.")
            queryset = queryset.filter(patient=patient)
        elif user.role == User.Roles.ADMIN or user.is_superuser:
            pass
        else:
            raise PermissionDenied("Access denied.")

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = MedicalRecordSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        """Creates a new clinical medical record with audit event logging."""
        user = request.user
        data = request.data.copy()

        if user.role == User.Roles.PATIENT:
            target_patient = user
        elif user.role == User.Roles.DOCTOR:
            patient_id = data.get("patient_id")
            if not patient_id:
                raise ValidationError("Field 'patient_id' is required.")
            try:
                target_patient = User.objects.get(id=patient_id, role=User.Roles.PATIENT)
            except User.DoesNotExist:
                raise NotFound("Target patient does not exist.")
            if not doctor_can_access_patient(user, target_patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")
        else:
            raise PermissionDenied("Only patients or authorized doctors can create medical records.")

        serializer = MedicalRecordSerializer(data=data, context={"request": request, "target_patient": target_patient})
        serializer.is_valid(raise_exception=True)

        record = MedicalRecord.objects.create(
            patient=target_patient,
            title=serializer.validated_data["title"],
            record_type=serializer.validated_data.get("record_type", ""),
            description=serializer.validated_data.get("description", ""),
            recorded_at=serializer.validated_data["recorded_at"],
        )

        log_audit_event(
            user=user,
            action=AuditLog.Actions.RECORD_CREATE,
            resource_type="MedicalRecord",
            resource_id=record.id,
            request=request,
            metadata={"patient_id": target_patient.id, "title": record.title},
        )

        return Response(MedicalRecordSerializer(record).data, status=status.HTTP_201_CREATED)


# --- MedicalRecordDetailView ---
# What it does: Retrieves a single clinical record after verifying patient ownership or doctor relationship.
# Why it's structured this way: Granular object-level permission check prevents ID enumeration vulnerabilities.
# Parameters & Returns: GET request with record_id -> MedicalRecord details.
# ------------------------------------------------------------------------------
class MedicalRecordDetailView(APIView):
    """
    GET /api/v1/records/<record_id>/
    Retrieves a single medical record with strict authorization checks.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request, record_id):
        try:
            record = MedicalRecord.objects.select_related("patient").get(id=record_id)
        except MedicalRecord.DoesNotExist:
            raise NotFound(f"Medical record with ID {record_id} not found.")

        user = request.user
        if user.role == User.Roles.PATIENT and record.patient != user:
            raise PermissionDenied("You cannot access medical records belonging to another patient.")
        elif user.role == User.Roles.DOCTOR and not doctor_can_access_patient(user, record.patient):
            raise PermissionDenied("You are not authorized to view this patient's record.")

        return Response(MedicalRecordSerializer(record).data, status=status.HTTP_200_OK)


# --- LabReportListView ---
# What it does: Returns paginated list of uploaded diagnostic reports with pre-fetched biomarker results.
# Why it's structured this way: Uses prefetch_related('results') to avoid N+1 query performance degradation.
# Parameters & Returns: GET request -> Paginated list of LabReport objects.
# ------------------------------------------------------------------------------
class LabReportListView(APIView):
    """
    GET /api/v1/records/reports/
    Lists diagnostic laboratory reports and pre-fetched LabResults.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        user = request.user
        if user.role == User.Roles.PATIENT:
            reports = LabReport.objects.filter(patient=user).prefetch_related("results")
        elif user.role == User.Roles.DOCTOR:
            patient_id = request.query_params.get("patient_id")
            if not patient_id:
                raise ValidationError("Must supply 'patient_id' query param.")
            patient = User.objects.filter(id=patient_id, role=User.Roles.PATIENT).first()
            if not patient or not doctor_can_access_patient(user, patient):
                raise PermissionDenied("Unauthorized to view this patient's reports.")
            reports = LabReport.objects.filter(patient=patient).prefetch_related("results")
        elif user.role == User.Roles.ADMIN or user.is_superuser:
            reports = LabReport.objects.all().prefetch_related("results")
        else:
            raise PermissionDenied("Access denied.")

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(reports, request)
        serializer = LabReportSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


# --- LabReportUploadView ---
# What it does: Securely ingests PDF and medical image uploads, validating MIME types, extensions, and file sizes.
# Why it's structured this way: Enforces strict file security validation to prevent malicious payload uploads to clinical servers.
# Parameters & Returns: POST multipart request -> HTTP 201 Created with LabReport payload.
# ------------------------------------------------------------------------------
class LabReportUploadView(APIView):
    """
    POST /api/v1/records/reports/upload/
    Accepts multipart/form-data with file validation (size, MIME, magic bytes signature).
    """
    permission_classes = [IsPatient]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "No file was attached in the 'file' field."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        title = request.data.get("title", "")
        report = save_lab_report(
            patient_user=request.user,
            uploaded_file=uploaded_file,
            title=title,
            request=request,
        )

        serializer = LabReportSerializer(report, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# --- LabReportDetailView ---
# What it does: Returns single lab report details and extracted biomarker metrics with ownership authorization.
# Why it's structured this way: Enforces doctor-patient relationship checks before revealing sensitive laboratory data.
# Parameters & Returns: GET request with report_id -> LabReport details.
# ------------------------------------------------------------------------------
class LabReportDetailView(APIView):
    """
    GET /api/v1/records/reports/<report_id>/
    Retrieves full details of a specific lab report and its structured biomarkers.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request, report_id):
        try:
            report = LabReport.objects.prefetch_related("results").select_related("patient").get(id=report_id)
        except LabReport.DoesNotExist:
            raise NotFound(f"Lab report with ID {report_id} not found.")

        user = request.user
        if user.role == User.Roles.PATIENT and report.patient != user:
            raise PermissionDenied("Access to another patient's report is forbidden.")
        elif user.role == User.Roles.DOCTOR and not doctor_can_access_patient(user, report.patient):
            raise PermissionDenied("Unauthorized to access this report.")

        serializer = LabReportSerializer(report, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- MedicalRecordAnalyzeView ---
# What it does: Triggers NLP biomarker extraction on clinical narratives or lab reports, persisting discrete LabResult rows.
# Why it's structured this way: Decouples analysis from uploads, enabling on-demand reprocessing and retrospective analysis.
# Parameters & Returns: POST request with record_id -> Extracted biomarkers, critical flags, and clinical summary.
# ------------------------------------------------------------------------------
class MedicalRecordAnalyzeView(APIView):
    """
    POST /api/v1/medical-records/<id>/analyze/
    POST /api/v1/records/<id>/analyze/

    Purpose:
        Extracts key quantitative clinical biomarkers (glucose, HbA1c, BP, WBC, etc.),
        computes abnormal and critical flags, and synchronizes granular LabResult records.

    Architecture Walkthrough (Viva / Review Presentation Topic):
        - STEP 1: Resolves target LabReport or MedicalRecord and verifies authorization.
        - STEP 2: Delegates analysis and LabResult synchronization to service layer.
        - STEP 3: Returns standardized quantitative biomarker extraction payload.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request, record_id):
        user = request.user
        target_patient = None
        lab_report = None
        med_record = None

        # ----------------------------------------------------------------------
        # STEP 1: RESOLVE RECORD & ENFORCE AUTHORIZATION
        # ----------------------------------------------------------------------
        lab_report = LabReport.objects.filter(id=record_id).select_related("patient").first()
        if lab_report:
            target_patient = lab_report.patient
        else:
            med_record = MedicalRecord.objects.filter(id=record_id).select_related("patient").first()
            if med_record:
                target_patient = med_record.patient
            else:
                raise NotFound(f"Medical record or lab report with ID {record_id} not found.")

        if user.role == User.Roles.PATIENT and target_patient != user:
            raise PermissionDenied("You cannot access medical records belonging to another patient.")
        elif user.role == User.Roles.DOCTOR and not doctor_can_access_patient(user, target_patient):
            raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")

        # ----------------------------------------------------------------------
        # STEP 2: DELEGATE ANALYSIS WORKFLOW TO SERVICES LAYER
        # ----------------------------------------------------------------------
        text_override = request.data.get("text", "")
        analysis_payload = analyze_and_sync_record_or_report(
            user=user,
            target_patient=target_patient,
            record_id=record_id,
            lab_report=lab_report,
            med_record=med_record,
            text_override=text_override,
            request=request,
        )

        return Response(analysis_payload, status=status.HTTP_200_OK)
