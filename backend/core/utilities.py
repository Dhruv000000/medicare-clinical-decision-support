# ==============================================================================
# FILE: backend/core/utilities.py
# PURPOSE: Security validation utilities for database health and medical document upload verification.
# VIVA EXPLANATION: Implements defense-in-depth file security (magic byte verification, MIME matching, UUID sanitization) to prevent malicious executable injection via medical lab report uploads.
# ==============================================================================

import os
import uuid
from pathlib import Path
from django.db import connection
from rest_framework.exceptions import ValidationError

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}

FILE_SIGNATURES = {
    "pdf": [b"%PDF"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpeg": [b"\xff\xd8\xff"],
    "webp": [b"RIFF"],
}


# --- check_database_connection ---
# What it does: Executes a lightweight 'SELECT 1' ping to verify database liveness without exposing credentials.
# Why it's structured this way: Used by the '/health/' endpoint for load balancers and deployment probes.
# Parameters & Returns: Returns status dictionary with connection state and database vendor.
# ------------------------------------------------------------------------------
def check_database_connection():
    """
    Safely ping the database and return connectivity status.
    Never exposes internal passwords or stack traces.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {
            "status": "connected",
            "vendor": connection.vendor,
        }
    except Exception as exc:
        return {
            "status": "error",
            "vendor": getattr(connection, "vendor", "unknown"),
            "message": "Database connection check failed",
        }


# --- validate_uploaded_file ---
# What it does: Enforces strict 4-layer validation on uploaded medical lab files (size, extension, MIME, magic bytes).
# Why it's structured this way: Prevents polyglot file attacks and malicious scripts disguised as diagnostic PDFs or images.
# Parameters & Returns: Takes uploaded_file; raises ValidationError if invalid, returns True if verified.
# ------------------------------------------------------------------------------
def validate_uploaded_file(uploaded_file):
    """
    Strong validation for medical report uploads.
    Validates:
      1. File size (max 10MB)
      2. File extension (.pdf, .jpeg, .jpg, .png, .webp)
      3. Content type header
      4. Magic byte signature verification
    """
    if not uploaded_file:
        raise ValidationError("No file was uploaded.")

    # 1. File size check
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # 2. Extension check
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    # 3. MIME type check
    content_type = getattr(uploaded_file, "content_type", "").lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"Unsupported MIME type '{content_type}'. Allowed types are: {', '.join(sorted(ALLOWED_MIME_TYPES))}."
        )

    # 4. Content signature (magic bytes) verification
    pos = uploaded_file.tell()
    try:
        header = uploaded_file.read(32)
        uploaded_file.seek(pos)

        if ext == ".pdf":
            if not header.startswith(b"%PDF"):
                raise ValidationError("Invalid PDF file: corrupted or invalid file signature.")
        elif ext in (".jpg", ".jpeg"):
            if not header.startswith(b"\xff\xd8\xff"):
                raise ValidationError("Invalid JPEG file: corrupted or invalid file signature.")
        elif ext == ".png":
            if not header.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValidationError("Invalid PNG file: corrupted or invalid file signature.")
        elif ext == ".webp":
            if not (header.startswith(b"RIFF") and header[8:12] == b"WEBP"):
                raise ValidationError("Invalid WebP file: corrupted or invalid file signature.")
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"Failed to verify file integrity: {str(exc)}")

    return True


# --- generate_safe_filename ---
# What it does: Sanitizes filenames by replacing client-supplied names with randomized UUID4 hex strings.
# Why it's structured this way: Mitigates directory traversal (path traversal) vulnerabilities and filename collisions.
# Parameters & Returns: Takes original_filename string; returns sanitized '<uuid>.<ext>' string.
# ------------------------------------------------------------------------------
def generate_safe_filename(original_filename):
    """
    Generates an unguessable, safe server-side filename using UUID4,
    preserving only the validated extension.
    Never trusts client-provided paths or names.
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".bin"
    return f"{uuid.uuid4().hex}{ext}"
