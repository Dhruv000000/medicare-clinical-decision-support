from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from core.permissions import IsAuthenticatedUser, IsPatient, doctor_can_access_patient
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog

from .models import MedicalRecord, LabReport, LabResult
from .serializers import MedicalRecordSerializer, LabReportSerializer
from .services import save_lab_report, parse_report_content


class MedicalRecordListCreateView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
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


class MedicalRecordDetailView(APIView):
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


class LabReportListView(APIView):
    """
    GET /api/v1/records/reports/
    Lists lab reports for the authenticated patient.
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


class LabReportUploadView(APIView):
    """
    POST /api/v1/records/reports/upload/
    Accepts multipart/form-data with file validation (size, MIME, magic bytes).
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


class LabReportDetailView(APIView):
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


class MedicalRecordAnalyzeView(APIView):
    """
    POST /api/v1/medical-records/<id>/analyze/
    POST /api/v1/records/<id>/analyze/
    Extracts key quantitative clinical metrics, abnormal flags, and saves structured
    LabResult records with doctor-patient authorization enforcement.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request, record_id):
        user = request.user
        target_patient = None
        lab_report = None
        med_record = None

        # Check if record_id corresponds to a LabReport
        lab_report = LabReport.objects.filter(id=record_id).select_related("patient").first()
        if lab_report:
            target_patient = lab_report.patient
        else:
            med_record = MedicalRecord.objects.filter(id=record_id).select_related("patient").first()
            if med_record:
                target_patient = med_record.patient
            else:
                raise NotFound(f"Medical record or lab report with ID {record_id} not found.")

        # Enforce authorization
        if user.role == User.Roles.PATIENT and target_patient != user:
            raise PermissionDenied("You cannot access medical records belonging to another patient.")
        elif user.role == User.Roles.DOCTOR and not doctor_can_access_patient(user, target_patient):
            raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")

        # Extract content
        text_override = request.data.get("text", "")
        if text_override:
            content = text_override
        elif lab_report:
            if lab_report.file:
                try:
                    lab_report.file.seek(0)
                    content = lab_report.file.read()
                except Exception:
                    content = lab_report.extracted_text or lab_report.title
            else:
                content = lab_report.extracted_text or lab_report.title
        elif med_record:
            content = f"{med_record.title}. {med_record.description}"
        else:
            content = ""

        title = lab_report.title if lab_report else (med_record.title if med_record else "")
        file_type = lab_report.file_type if lab_report else ""
        analysis = parse_report_content(content, title=title, file_type=file_type)

        # Sanitize strings to ensure PostgreSQL compatibility (cannot contain 0x00 bytes)
        clean_extracted_text = (analysis.get("extracted_text") or "").replace("\x00", "")
        clean_summary = (analysis.get("summary") or "").replace("\x00", "")

        # Update lab report fields and create LabResults if it's a LabReport
        if lab_report:
            lab_report.extracted_text = clean_extracted_text
            lab_report.analysis_summary = clean_summary
            lab_report.save(update_fields=["extracted_text", "analysis_summary"])

            # Sync extracted metrics to LabResult models
            for metric in analysis.get("metrics", []):
                test_name = str(metric.get("test_name", "")).replace("\x00", "")
                if not test_name:
                    continue
                LabResult.objects.update_or_create(
                    report=lab_report,
                    test_name=test_name,
                    defaults={
                        "value": str(metric.get("value", "")).replace("\x00", ""),
                        "unit": str(metric.get("unit", "")).replace("\x00", ""),
                        "reference_range": str(metric.get("reference_range", "")).replace("\x00", ""),
                        "flag": str(metric.get("flag", "normal")).replace("\x00", ""),
                    },
                )

        log_audit_event(
            user=user,
            action=AuditLog.Actions.RECORD_UPDATE,
            resource_type="LabReport" if lab_report else "MedicalRecord",
            resource_id=record_id,
            request=request,
            metadata={
                "patient_id": target_patient.id,
                "metrics_count": analysis["total_metrics_extracted"],
                "abnormal_count": analysis["abnormal_flags_count"],
            },
        )

        return Response(
            {
                "record_id": record_id,
                "patient_id": target_patient.id,
                "type": "LabReport" if lab_report else "MedicalRecord",
                "extracted_text": analysis["extracted_text"],
                "metrics": analysis["metrics"],
                "total_metrics_extracted": analysis["total_metrics_extracted"],
                "abnormal_flags_count": analysis["abnormal_flags_count"],
                "critical_flags_count": analysis["critical_flags_count"],
                "summary": analysis["summary"],
                "ocr_status": analysis.get("ocr_status", "not_applicable"),
                "confidence": analysis.get("confidence", "high"),
            },
            status=status.HTTP_200_OK,
        )


