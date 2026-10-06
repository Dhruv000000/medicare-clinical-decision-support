from pathlib import Path
from django.core.files.base import ContentFile
from core.utilities import validate_uploaded_file, generate_safe_filename
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog
from ..models import LabReport
from .report_parser import parse_report_content, extract_metrics_from_text, extract_text_from_stream


def save_lab_report(patient_user, uploaded_file, title="", request=None):
    """
    Validates uploaded file (size, MIME, magic bytes signature),
    generates safe server-side filename, persists the file and report metadata,
    and logs an audit event.
    """
    validate_uploaded_file(uploaded_file)

    safe_name = generate_safe_filename(uploaded_file.name)
    ext = Path(uploaded_file.name).suffix.lower()

    report = LabReport(
        patient=patient_user,
        title=(title if title else Path(uploaded_file.name).stem).replace("\x00", "").strip(),
        file_type=ext.lstrip("."),
        file_size=uploaded_file.size,
    )
    # Save the file using the sanitized server filename
    report.file.save(safe_name, ContentFile(uploaded_file.read()), save=True)

    log_audit_event(
        user=patient_user,
        action=AuditLog.Actions.REPORT_UPLOAD,
        resource_type="LabReport",
        resource_id=report.id,
        request=request,
        metadata={
            "file_size": uploaded_file.size,
            "file_type": ext,
            "title": report.title,
        },
    )

    return report


__all__ = [
    "save_lab_report",
    "parse_report_content",
    "extract_metrics_from_text",
    "extract_text_from_stream",
]
