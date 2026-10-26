# ==============================================================================
# FILE: backend/apps/medical_records/services/__init__.py
# PURPOSE: Clinical diagnostics and laboratory report orchestration service.
# VIVA EXPLANATION: This service manages the lifecycle of diagnostic lab reports. It validates uploads against strict file security rules, parses documents into structured quantitative biomarkers, classifies findings against biological reference ranges, and synchronizes granular LabResult records.
# ==============================================================================

from pathlib import Path
from typing import Dict, Any, Optional
from django.core.files.base import ContentFile

from core.utilities import validate_uploaded_file, generate_safe_filename
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog
from ..models import LabReport, LabResult, MedicalRecord
from .report_parser import parse_report_content, extract_metrics_from_text, extract_text_from_stream


# --- save_lab_report ---
# What it does: Validates uploaded medical documents (magic bytes, MIME) and saves them with UUID filenames.
# Why it's structured this way: Enforces file sanitization and writes regulatory audit logs before writing to disk.
# Parameters & Returns: patient_user, uploaded_file, title, request -> Persisted LabReport model instance.
# ------------------------------------------------------------------------------
def save_lab_report(patient_user, uploaded_file, title="", request=None) -> LabReport:
    """
    Validates uploaded medical file and persists report metadata.

    Security & Validation Pipeline:
        1. Validates file size (max limit), MIME type, and magic bytes signature.
        2. Generates cryptographically safe UUID server-side filename.
        3. Persists file to media storage and creates LabReport model.
        4. Records regulatory AuditLog entry for file upload tracking.
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


# --- analyze_and_sync_record_or_report ---
# What it does: Extracts text from lab report or medical record, parses biomarkers, and persists individual LabResult rows.
# Why it's structured this way: Synchronizes atomic biomarker rows in a transaction so frontend trend charts can query individual analytes.
# Parameters & Returns: user, target_patient, record_id, lab_report, med_record, text_override, request -> Dict with analysis results and synced count.
# ------------------------------------------------------------------------------
def analyze_and_sync_record_or_report(
    user,
    target_patient,
    record_id: int,
    lab_report: Optional[LabReport] = None,
    med_record: Optional[MedicalRecord] = None,
    text_override: str = "",
    request=None,
) -> Dict[str, Any]:
    """
    Executes automated clinical laboratory report parsing and database synchronization.

    Viva / Review Walkthrough:
        - STEP 1: Content Extraction from uploaded binary stream or clinical notes.
        - STEP 2: Clinical Biomarker Parsing & Threshold Evaluation (parse_report_content).
        - STEP 3: PostgreSQL Null-Byte Sanitization.
        - STEP 4: Synchronize extracted biomarkers to granular LabResult models.
        - STEP 5: Emit regulatory AuditLog event with metric counts.
    """
    # --------------------------------------------------------------------------
    # STEP 1: CONTENT EXTRACTION
    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    # STEP 2: CLINICAL BIOMARKER PARSING & THRESHOLD EVALUATION
    # --------------------------------------------------------------------------
    analysis = parse_report_content(content, title=title, file_type=file_type)

    # --------------------------------------------------------------------------
    # STEP 3: SANITIZE STRINGS FOR DATABASE COMPATIBILITY
    # --------------------------------------------------------------------------
    clean_extracted_text = (analysis.get("extracted_text") or "").replace("\x00", "")
    clean_summary = (analysis.get("summary") or "").replace("\x00", "")

    # --------------------------------------------------------------------------
    # STEP 4: PERSIST TO LabReport & SYNC LabResult RECORDS
    # --------------------------------------------------------------------------
    if lab_report:
        lab_report.extracted_text = clean_extracted_text
        lab_report.analysis_summary = clean_summary
        lab_report.save(update_fields=["extracted_text", "analysis_summary"])

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

    # --------------------------------------------------------------------------
    # STEP 5: REGULATORY AUDIT LOGGING
    # --------------------------------------------------------------------------
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

    return {
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
        "fallback_log": analysis.get("fallback_log", []),
        "extraction_logs": analysis.get("extraction_logs", []),
        "clinical_impression": analysis.get("clinical_impression", []),
        "recommended_next_steps": analysis.get("recommended_next_steps", []),
        "next_steps": analysis.get("next_steps", []),
    }


__all__ = [
    "save_lab_report",
    "analyze_and_sync_record_or_report",
    "parse_report_content",
    "extract_metrics_from_text",
    "extract_text_from_stream",
]
