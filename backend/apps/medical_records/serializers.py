from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from .models import MedicalRecord, LabReport, LabResult


class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = ["id", "test_name", "value", "unit", "reference_range", "flag"]


class LabReportSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source="patient.email", read_only=True)
    results = LabResultSerializer(many=True, read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = LabReport
        fields = [
            "id",
            "patient",
            "patient_email",
            "title",
            "file",
            "file_url",
            "file_type",
            "file_size",
            "extracted_text",
            "analysis_summary",
            "results",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "patient",
            "file_size",
            "file_type",
            "extracted_text",
            "analysis_summary",
            "results",
            "uploaded_at",
        ]

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class MedicalRecordSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source="patient.email", read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            "id",
            "patient",
            "patient_email",
            "title",
            "record_type",
            "description",
            "recorded_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "patient", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context.get("request")
        target_patient = self.context.get("target_patient")
        if request and request.user and getattr(request.user, "role", None) == "doctor" and target_patient:
            from core.permissions import doctor_can_access_patient
            if not doctor_can_access_patient(request.user, target_patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")
        return attrs
