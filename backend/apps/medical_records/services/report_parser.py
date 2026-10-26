# ==============================================================================
# FILE: backend/apps/medical_records/services/report_parser.py
# PURPOSE: Clinical diagnostic document parser and quantitative biomarker extraction engine.
# VIVA EXPLANATION: This service parses PDF document byte streams and images to extract clinical laboratory markers (HbA1c, glucose, lipid panels, CBC, renal function). It applies expert clinical threshold classifiers to evaluate each value against biological reference ranges and assign clinical flags (normal, abnormal, or critical).
# ==============================================================================

import io
import logging
import re
import zlib
from typing import Union, List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


# --- _clean_pdf_string ---
# What it does: Decodes escaped PDF string literals and strips null bytes.
# Why it's structured this way: Sanitizes raw PDF stream encoding artifacts to prevent null byte errors in database storage.
# Parameters & Returns: data (bytes) -> clean decoded string.
# ------------------------------------------------------------------------------
def _clean_pdf_string(data: bytes) -> str:
    """Decodes PDF escaped string literals."""
    try:
        text = data.decode("latin1")
        text = text.replace(r"\n", "\n").replace(r"\r", "\r").replace(r"\t", "\t")
        text = text.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")
        text = text.replace("\x00", "")
        return text.strip()
    except Exception:
        return ""


def _clean_pdf_hex_string(data: bytes) -> str:
    """Decodes PDF hexadecimal string literals, e.g. <48656c6c6f>."""
    try:
        raw_hex = re.sub(rb"\s+", b"", data)
        if len(raw_hex) % 2 != 0:
            raw_hex += b"0"
        decoded = bytes.fromhex(raw_hex.decode("ascii", errors="ignore")).decode("latin1", errors="ignore")
        return decoded.strip().replace("\x00", "")
    except Exception:
        return ""


# --- _extract_text_from_pdf_bytes ---
# What it does: Primary robust text extraction from PDF byte streams using pypdf,
# with multi-stage fallbacks to native FlateDecode decompressors, hex string decoders,
# uncompressed literal scrapers, and printable ASCII sequence recovery.
# Why it's structured this way: Guarantees extraction across all standard modern PDFs
# (including cross-reference object streams /ObjStm and font encodings) while maintaining
# flawless fallback safety for malformed streams and scanned documents.
# Parameters & Returns: content (bytes), fallback_log (list) -> extracted text string.
# ------------------------------------------------------------------------------
def _extract_text_from_pdf_bytes(content: bytes, fallback_log: Optional[List[str]] = None) -> str:
    """
    Extracts plain text from PDF bytes via a resilient multi-tier extraction pipeline:
    1. pypdf.PdfReader (handles /ObjStm, xref streams, font encodings, and layout mode)
    2. FlateDecode stream decompressor with Tj/TJ literal & hexadecimal string decoding
    3. Direct literal and hex match scanning across entire payload
    4. Cleaned printable ASCII sequence recovery (filtering PDF structural keywords)
    5. Embedded image OCR fallback when dependencies are present
    """
    log_sink = fallback_log if fallback_log is not None else []
    content_len = len(content)
    logger.info("[PDF Extractor] Initiating extraction pipeline on PDF byte stream (%d bytes)", content_len)
    log_sink.append(f"[PDF Init] Initiating extraction pipeline on PDF document ({content_len} bytes).")

    # --------------------------------------------------------------------------
    # TIER 1: Standard PDF Reader via pypdf
    # --------------------------------------------------------------------------
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        total_pages = len(reader.pages)
        pages_text = []

        for p_idx, page in enumerate(reader.pages):
            page_text = ""
            try:
                page_text = page.extract_text(extraction_mode="layout") or ""
            except Exception:
                page_text = page.extract_text() or ""
            if not page_text or not page_text.strip():
                page_text = page.extract_text() or ""
            if page_text and page_text.strip():
                pages_text.append(page_text.strip())

        if pages_text:
            extracted_pypdf = "\n\n".join(pages_text).strip()
            if len(extracted_pypdf) >= 10:
                preview = extracted_pypdf[:140].replace("\n", " ").strip()
                msg = f"pypdf successfully extracted {len(extracted_pypdf)} characters across {total_pages} page(s). Preview: '{preview}...'"
                logger.info("[PDF Extractor] %s", msg)
                log_sink.append(f"[PDF Extractor: pypdf] {msg}")
                return extracted_pypdf.replace("\x00", "")
            else:
                log_sink.append(f"[PDF Extractor: pypdf] Extracted text too brief ({len(extracted_pypdf)} chars). Triggering native stream fallback.")
        else:
            log_sink.append(f"[PDF Extractor: pypdf] Zero characters extracted from {total_pages} page(s). Triggering native stream fallback.")
    except Exception as e:
        logger.warning("[PDF Extractor] pypdf reader encountered exception: %s. Engaging fallback parser.", e)
        log_sink.append(f"[PDF Extractor: pypdf Warning] {type(e).__name__}: {e}. Engaging native stream fallback.")

    # --------------------------------------------------------------------------
    # TIER 2: Native FlateDecode Stream Decompressor & Operator Parser
    # --------------------------------------------------------------------------
    logger.info("[PDF Fallback] Attempting FlateDecode stream decompression.")
    log_sink.append("[PDF Fallback 1] Attempting FlateDecode stream decompression & operator parsing.")
    text_chunks = []
    stream_pattern = re.compile(rb"<<(.*?)>>\s*stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
    stream_count = 0

    for match in stream_pattern.finditer(content):
        stream_count += 1
        dict_part = match.group(1)
        raw_stream = match.group(2)

        decompressed = raw_stream
        if b"/FlateDecode" in dict_part:
            try:
                decompressed = zlib.decompress(raw_stream)
            except Exception:
                try:
                    decompressed = zlib.decompress(raw_stream, -zlib.MAX_WBITS)
                except Exception:
                    decompressed = raw_stream

        # Extract literal text strings in Tj, ', "
        for m in re.finditer(rb"\(((?:\\\(|\\\)|\\[^()]|[^()])*)\)\s*(?:Tj|'|\")", decompressed):
            cleaned = _clean_pdf_string(m.group(1))
            if cleaned:
                text_chunks.append(cleaned)

        # Extract hexadecimal text strings in Tj, ', " (e.g. <4862413163> Tj)
        for m in re.finditer(rb"<([0-9A-Fa-f\s]+)>\s*(?:Tj|'|\")", decompressed):
            cleaned_hex = _clean_pdf_hex_string(m.group(1))
            if cleaned_hex:
                text_chunks.append(cleaned_hex)

        # Extract array text elements in TJ (e.g., [(text1) -10 (text2)] TJ)
        for tj in re.finditer(rb"\[(.*?)\]\s*TJ", decompressed):
            tj_content = tj.group(1)
            for m in re.finditer(rb"\(((?:\\\(|\\\)|\\[^()]|[^()])*)\)", tj_content):
                cleaned = _clean_pdf_string(m.group(1))
                if cleaned:
                    text_chunks.append(cleaned)
            for m in re.finditer(rb"<([0-9A-Fa-f\s]+)>", tj_content):
                cleaned_hex = _clean_pdf_hex_string(m.group(1))
                if cleaned_hex:
                    text_chunks.append(cleaned_hex)

    stream_text = " ".join(text_chunks).strip()
    if len(stream_text) >= 10:
        preview = stream_text[:140].replace("\n", " ").strip()
        msg = f"Decompressed {stream_count} stream(s), retrieved {len(text_chunks)} tokens ({len(stream_text)} chars). Preview: '{preview}...'"
        logger.info("[PDF Fallback] %s", msg)
        log_sink.append(f"[PDF Fallback: Flate Streams] {msg}")
        return re.sub(r"[ \t]+", " ", stream_text).replace("\x00", "")

    # --------------------------------------------------------------------------
    # TIER 3: Uncompressed / Direct Literal Match Scanning
    # --------------------------------------------------------------------------
    log_sink.append("[PDF Fallback 2] Attempting direct uncompressed literal extraction.")
    direct_matches = re.findall(rb"\(([^\(\)]*)\)\s*(?:Tj|TJ|\')?", content)
    for m in direct_matches:
        try:
            decoded = m.decode("utf-8", errors="ignore").strip()
            if decoded and len(decoded) > 1:
                text_chunks.append(decoded)
        except Exception:
            pass

    direct_text = " ".join(text_chunks).strip()
    if len(direct_text) >= 10:
        log_sink.append(f"[PDF Fallback: Direct Literals] Retrieved {len(direct_text)} characters.")
        return re.sub(r"[ \t]+", " ", direct_text).replace("\x00", "")

    # --------------------------------------------------------------------------
    # TIER 4: Printable ASCII Sequence Recovery
    # --------------------------------------------------------------------------
    log_sink.append("[PDF Fallback 3] Attempting printable ASCII sequence recovery.")
    printable = re.sub(rb"[^\x20-\x7E\r\n\t]", b" ", content)
    ascii_candidate = printable.decode("utf-8", errors="ignore").strip()
    filtered_lines = [
        line.strip() for line in ascii_candidate.splitlines()
        if line.strip() and not line.strip().startswith(("%", "obj", "endobj", "xref", "trailer", "startxref"))
    ]
    if filtered_lines:
        ascii_text = "\n".join(filtered_lines).strip()
        if len(ascii_text) >= 10:
            log_sink.append(f"[PDF Fallback: ASCII Recovery] Recovered {len(ascii_text)} characters.")
            return re.sub(r"[ \t]+", " ", ascii_text).replace("\x00", "")

    # --------------------------------------------------------------------------
    # TIER 5: Embedded Scanned Image OCR Fallback
    # --------------------------------------------------------------------------
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        for p_idx, page in enumerate(reader.pages):
            for img_file in page.images:
                img_data = img_file.data
                ocr_text, status, _ = _extract_text_from_image_bytes(img_data)
                if ocr_text:
                    msg = f"Extracted {len(ocr_text)} characters via OCR from embedded image on page {p_idx + 1}."
                    logger.info("[PDF OCR Fallback] %s", msg)
                    log_sink.append(f"[PDF Fallback: Image OCR] {msg}")
                    return ocr_text.replace("\x00", "")
    except Exception:
        pass

    log_sink.append("[PDF Extraction Complete] No readable textual content could be recovered from PDF.")
    return ""


def _extract_text_from_image_bytes(content: bytes) -> Tuple[str, str, str]:
    """
    Attempts OCR on image bytes using pytesseract / PIL.
    Returns: (extracted_text, ocr_status, confidence)
    """
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(content))
        try:
            import pytesseract
            text = pytesseract.image_to_string(img)
            clean_text = text.strip().replace("\x00", "")
            if clean_text:
                return clean_text, "success", "high"
            return "", "empty", "low"
        except ImportError:
            logger.info("OCR engine (pytesseract) is not installed in the environment.")
            return "", "unavailable", "low"
        except Exception as e:
            logger.warning("OCR image processing failed: %s", e)
            return "", "failed", "low"
    except Exception as e:
        logger.warning("Failed to open image for OCR: %s", e)
        return "", "invalid_image", "low"


# --- extract_text_and_logs ---
# What it does: Extracts text from byte stream or string while capturing full audit/inspection logs.
# Why it's structured this way: Provides end-to-end visibility into text extraction stages for frontend inspection modals.
# Parameters & Returns: content, file_type -> (extracted_text, fallback_log, ocr_status, confidence).
# ------------------------------------------------------------------------------
def extract_text_and_logs(content: Union[str, bytes], file_type: str = "") -> Tuple[str, List[str], str, str]:
    """
    Unified multi-format extraction engine returning both clean plaintext and
    step-by-step diagnostic fallback verification logs.
    """
    fallback_log: List[str] = []
    ocr_status = "not_applicable"
    confidence = "high"

    if isinstance(content, str):
        fallback_log.append(f"[Input Source] Plain string input ({len(content)} characters).")
        return content.replace("\x00", ""), fallback_log, ocr_status, confidence

    if isinstance(content, bytes):
        is_pdf = content.startswith(b"%PDF") or file_type.lower() == "pdf"
        if is_pdf:
            extracted_text = _extract_text_from_pdf_bytes(content, fallback_log=fallback_log)
            return extracted_text.replace("\x00", ""), fallback_log, ocr_status, confidence

        is_image = (
            content.startswith(b"\x89PNG\r\n\x1a\n")
            or content.startswith(b"\xff\xd8\xff")
            or (content.startswith(b"RIFF") and b"WEBP" in content[:16])
            or file_type.lower() in ("png", "jpg", "jpeg", "webp")
        )
        if is_image:
            ocr_text, ocr_status, confidence = _extract_text_from_image_bytes(content)
            fallback_log.append(f"[Image Input] Processed image format. OCR status: {ocr_status}. Chars: {len(ocr_text)}.")
            return ocr_text.replace("\x00", ""), fallback_log, ocr_status, confidence

        decoded = content.decode("utf-8", errors="replace").replace("\x00", "")
        fallback_log.append(f"[Binary Stream] Decoded UTF-8 content ({len(decoded)} characters).")
        return decoded, fallback_log, ocr_status, confidence

    raw_str = str(content).replace("\x00", "")
    fallback_log.append(f"[Fallback String Conversion] Formatted string representation ({len(raw_str)} characters).")
    return raw_str, fallback_log, ocr_status, confidence


# --- extract_text_from_stream ---
# What it does: Extracts text from bytes or strings, dispatching to PDF flate decoders or image OCR handlers.
# Why it's structured this way: Backward-compatible unified multi-format ingestion endpoint.
# Parameters & Returns: content (Union[str, bytes]), file_type (str) -> clean extracted string.
# ------------------------------------------------------------------------------
def extract_text_from_stream(content: Union[str, bytes], file_type: str = "") -> str:
    """
    Extracts plain text from string, raw bytes, PDF streams (with FlateDecode and pypdf support),
    or image files via OCR when dependencies are available.
    """
    text, _, _, _ = extract_text_and_logs(content, file_type=file_type)
    return text


def classify_blood_pressure(systolic: float, diastolic: float) -> tuple[str, str]:
    """Classifies blood pressure per AHA/ACC clinical guidelines."""
    if systolic >= 180 or diastolic >= 120:
        return "critical", "Hypertensive crisis. Immediate emergency clinical attention advised."
    if systolic >= 140 or diastolic >= 90:
        return "high", "Stage 2 Hypertension. Clinical management recommended."
    if systolic >= 130 or diastolic >= 80:
        return "elevated", "Stage 1 Hypertension or elevated reading."
    if systolic < 90 or diastolic < 60:
        return "low", "Hypotension reading."
    return "normal", "Blood pressure within normal clinical limits."


def classify_glucose(val: float) -> tuple[str, str]:
    """Classifies blood glucose reading in mg/dL."""
    if val >= 300 or val < 54:
        return "critical", "Severe hypoglycemia/hyperglycemia alert."
    if val >= 126:
        return "high", "Fasting glucose indicates diabetic range."
    if val >= 100:
        return "elevated", "Impaired fasting glucose (prediabetic range)."
    if val < 70:
        return "low", "Hypoglycemic range."
    return "normal", "Normal fasting glucose."


def classify_hba1c(val: float) -> tuple[str, str]:
    """Classifies HbA1c percentage."""
    if val >= 10.0:
        return "critical", "Severely elevated glycation index."
    if val >= 6.5:
        return "high", "Diabetic diagnostic threshold (HbA1c >= 6.5%)."
    if val >= 5.7:
        return "elevated", "Prediabetic range (5.7% - 6.4%)."
    return "normal", "Normal glycemic regulation (< 5.7%)."


def classify_cholesterol(val: float) -> tuple[str, str]:
    """Classifies Total Cholesterol in mg/dL."""
    if val >= 300:
        return "critical", "Markedly elevated total cholesterol."
    if val >= 240:
        return "high", "High total cholesterol."
    if val >= 200:
        return "elevated", "Borderline elevated cholesterol."
    return "normal", "Desirable total cholesterol (< 200 mg/dL)."


def classify_ldl(val: float) -> tuple[str, str]:
    """Classifies LDL cholesterol in mg/dL."""
    if val >= 190:
        return "critical", "Very high LDL. Increased cardiovascular event risk."
    if val >= 160:
        return "high", "High LDL cholesterol."
    if val >= 130:
        return "elevated", "Borderline high LDL."
    return "normal", "Optimal/desirable LDL cholesterol."


def classify_hdl(val: float) -> tuple[str, str]:
    """Classifies HDL cholesterol in mg/dL."""
    if val < 40:
        return "low", "Low HDL cholesterol (cardiovascular risk factor)."
    return "normal", "Protective HDL level (>= 40 mg/dL)."


def classify_triglycerides(val: float) -> tuple[str, str]:
    """Classifies Triglycerides in mg/dL."""
    if val >= 500:
        return "critical", "Very high triglycerides. Pancreatitis risk."
    if val >= 200:
        return "high", "High triglyceride level."
    if val >= 150:
        return "elevated", "Borderline high triglycerides."
    return "normal", "Normal triglyceride level (< 150 mg/dL)."


def classify_hemoglobin(val: float) -> tuple[str, str]:
    """Classifies Hemoglobin in g/dL."""
    if val < 7.0 or val > 20.0:
        return "critical", "Critical hemoglobin requiring urgent attention."
    if val < 12.0:
        return "low", "Low hemoglobin (anemic range)."
    if val > 17.5:
        return "high", "Elevated hemoglobin / polycythemia."
    return "normal", "Hemoglobin within normal reference range."


def classify_platelets(val: float) -> tuple[str, str]:
    """Classifies Platelet count."""
    actual = val * 1000 if val < 1000 else val
    if actual < 50000:
        return "critical", "Severe thrombocytopenia alert."
    if actual < 150000:
        return "low", "Mild to moderate thrombocytopenia."
    if actual > 450000:
        return "high", "Thrombocytosis."
    return "normal", "Platelet count within standard clinical limits."


def classify_wbc(val: float) -> tuple[str, str]:
    """Classifies WBC count."""
    actual = val if val < 50 else val / 1000.0
    if actual < 2.0 or actual > 30.0:
        return "critical", "Critical leukopenia/leukocytosis alert."
    if actual < 4.0:
        return "low", "Leukopenia."
    if actual > 11.0:
        return "high", "Leukocytosis (potential infection/inflammation)."
    return "normal", "WBC within normal limits."


def classify_creatinine(val: float) -> tuple[str, str]:
    """Classifies Serum Creatinine in mg/dL."""
    if val > 4.0:
        return "critical", "Critical renal impairment indicator."
    if val > 1.3:
        return "high", "Elevated creatinine. Potential reduced GFR."
    if val < 0.6:
        return "low", "Low serum creatinine."
    return "normal", "Serum creatinine within normal renal reference."


def classify_potassium(val: float) -> tuple[str, str]:
    """Classifies Serum Potassium in mmol/L or mEq/L."""
    if val < 2.8 or val > 6.2:
        return "critical", "Critical dyskalemia. Cardiac arrhythmia risk."
    if val < 3.5:
        return "low", "Hypokalemia."
    if val > 5.1:
        return "high", "Hyperkalemia."
    return "normal", "Potassium within standard reference range."


def classify_sodium(val: float) -> tuple[str, str]:
    """Classifies Serum Sodium in mmol/L or mEq/L."""
    if val < 120 or val > 158:
        return "critical", "Critical dysnatremia. Neurologic risk."
    if val < 135:
        return "low", "Hyponatremia."
    if val > 145:
        return "high", "Hypernatremia."
    return "normal", "Sodium within standard reference range."


def classify_egfr(val: float, operator: str = "") -> tuple[str, str]:
    """
    Classifies Estimated Glomerular Filtration Rate (eGFR in mL/min/1.73m2)
    per KDIGO clinical kidney disease staging guidelines.
    """
    clean_op = (operator or "").strip()
    if ">" in clean_op:
        return "normal", "eGFR >= 60 mL/min/1.73m2 indicates normal or mildly decreased kidney function."
    if "<" in clean_op and val <= 15:
        return "critical", "eGFR < 15 indicates kidney failure (Stage 5 CKD). Urgent nephrology evaluation advised."
    if "<" in clean_op and val <= 30:
        return "critical", "eGFR < 30 indicates severely decreased kidney function (Stage 4 CKD)."
    if val >= 60:
        return "normal", "eGFR within normal or mildly reduced limits (>= 60 mL/min/1.73m2)."
    if val >= 45:
        return "elevated", "Mild to moderate decrease in kidney function (Stage 3a CKD)."
    if val >= 30:
        return "low", "Moderate to severe decrease in kidney function (Stage 3b CKD)."
    if val >= 15:
        return "critical", "Severely decreased kidney function (Stage 4 CKD)."
    return "critical", "Kidney failure (Stage 5 CKD). Immediate clinical care advised."


# --- extract_metrics_from_text ---
# What it does: Scans clinical report text with regex patterns and heuristic table column parsers
# to extract standard quantitative laboratory biomarkers (HbA1c, glucose, eGFR, creatinine, lipid panel, CBC, electrolytes).
# Why it's structured this way: Highly resilient to line breaks, table cell dumps, tabs, colons,
# spaces, and sequential column layouts, preventing extraction failures on real-world clinical PDFs.
# Parameters & Returns: text (str), fallback_log (Optional[List[str]]) -> List of parsed metric dicts with clinical flags.
# ------------------------------------------------------------------------------
def extract_metrics_from_text(text: str, fallback_log: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Extracts key quantitative metrics and reference range flags from text using resilient regex
    and secondary columnar-table heuristics.
    Preserves exact keys and format required by LabResult persistence and frontend contracts.
    """
    log_sink = fallback_log if fallback_log is not None else []
    metrics: List[Dict[str, Any]] = []

    if not text or not text.strip():
        logger.warning("[Biomarker Scan] Input text is empty. Zero metrics extracted.")
        log_sink.append("[Biomarker Scan] Input text is empty. No biomarker patterns evaluated.")
        return metrics

    preview = text[:180].replace("\n", " ").strip()
    logger.debug("[Biomarker Scan] Scanning text (%d chars). Preview: '%s...'", len(text), preview)
    log_sink.append(f"[Biomarker Scan] Initiating biomarker pattern scan across {len(text)} characters. Preview: '{preview}...'")

    # Resilient delimiter matching:
    # 1. Colons, equals, hyphens, pipes, or leader dots followed by optional whitespace (including newlines)
    # 2. Horizontal tabs and spaces
    # 3. 1 or more line breaks with optional intermediate table headers / status / unit cells
    # 4. Optional trailing whitespace and multiline indentation before numerical value
    DELIM = (
        r"(?:"
        r"[ \t]*[:=\-\|\.]{1,}\s*"
        r"|[ \t]+"
        r"|[\r\n]+(?:[ \t]*(?:"
        r"result|value|reading|level|test\s*result|val|res|observed|quantitative|"
        r"\([^\)\r\n]{1,30}\)|high|low|normal|critical|abnormal|"
        r"\%|mg/dl|mmol/l|meq/l|g/dl|cells/mcl|k/ul|x?10\^?[0-9]*/[a-z]+|ml/min(?:/1\.73m2)?"
        r")[:=\-\s]*[\r\n]*)*"
        r")\s*"
    )

    # 1. Blood Pressure: e.g. "135/88", "BP: 120/80 mmHg", "Blood Pressure\n120/80"
    bp_match = re.search(
        r"(?:blood\s*pressure|b\.?p\.?|systolic\s*/\s*diastolic)" + DELIM + r"\b([0-9]{2,3})\s*[/xX]\s*([0-9]{2,3})\s*(?:mm\s*hg)?\b",
        text,
        re.IGNORECASE,
    )
    if not bp_match:
        bp_match = re.search(
            r"\b([0-9]{2,3})\s*[/]\s*([0-9]{2,3})\s*(?:mm\s*hg)\b",
            text,
            re.IGNORECASE,
        )
    if not bp_match:
        bp_match = re.search(
            r"(?:blood\s*pressure|b\.?p\.?)?[:\s]*\b([0-9]{2,3})\s*[/]\s*([0-9]{2,3})\s*(?:mm\s*hg)?\b",
            text,
            re.IGNORECASE,
        )

    if bp_match:
        sys_val = float(bp_match.group(1))
        dia_val = float(bp_match.group(2))
        if 60 <= sys_val <= 260 and 40 <= dia_val <= 160:
            flag, note = classify_blood_pressure(sys_val, dia_val)
            metrics.append({
                "test_name": "Blood Pressure",
                "value": f"{int(sys_val)}/{int(dia_val)}",
                "unit": "mmHg",
                "reference_range": "90-120 / 60-80",
                "flag": flag,
                "clinical_note": note,
                "confidence": "high",
                "source": "pattern_match",
            })
            log_sink.append(f"[Pattern Match] Blood Pressure: {int(sys_val)}/{int(dia_val)} mmHg (Flag: {flag.upper()})")

    # 2. Glucose / Fasting Blood Sugar
    fbs_match = re.search(
        r"(?:fasting\s*(?:blood)?\s*(?:sugar|glucose)|fbs|blood\s*(?:sugar|glucose)|glucose(?:\s*,\s*fasting|\s*\(fasting\)|\s*\(f\))?|random\s*blood\s*(?:sugar|glucose)|rbs|serum\s*glucose|plasma\s*glucose|\bglucose\b)"
        + DELIM +
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if fbs_match:
        val = float(fbs_match.group(1))
        flag, note = classify_glucose(val)
        val_str = str(val if val != int(val) else int(val))
        metrics.append({
            "test_name": "Fasting Blood Glucose",
            "value": val_str,
            "unit": "mg/dL",
            "reference_range": "70-99",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] Fasting Blood Glucose: {val_str} mg/dL (Flag: {flag.upper()})")

    # 3. HbA1c / Hemoglobin A1c / A1C
    hba1c_match = re.search(
        r"(?:hba1c(?:\s*\(hemoglobin\s*a1c\))?|hemoglobin\s*a1c(?:\s*\(hba1c\))?|glycated\s*hemoglobin|glycosylated\s*hemoglobin|hgb[\s\-_]*a1c|\ba1c\b)"
        + DELIM +
        r"([0-9]+(?:\.[0-9]+)?)\s*%?",
        text,
        re.IGNORECASE,
    )
    if hba1c_match:
        val = float(hba1c_match.group(1))
        flag, note = classify_hba1c(val)
        val_str = str(val)
        metrics.append({
            "test_name": "HbA1c",
            "value": val_str,
            "unit": "%",
            "reference_range": "< 5.7",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] HbA1c: {val_str}% (Flag: {flag.upper()})")

    # 4. eGFR (Estimated Glomerular Filtration Rate)
    egfr_match = re.search(
        r"(?:estimated\s*(?:glomerular\s*filtration\s*rate|gfr)|glomerular\s*filtration\s*rate|egfr(?:\s*\(ckd-epi\)|\s*\(mdrd\))?|\bgfr\b)"
        + DELIM +
        r"([><]=?\s*)?([0-9]+(?:\.[0-9]+)?)\s*(?:ml\s*/\s*min(?:\s*/\s*1\.73\s*m\^?2)?)?",
        text,
        re.IGNORECASE,
    )
    if egfr_match:
        operator = (egfr_match.group(1) or "").strip()
        val = float(egfr_match.group(2))
        val_str = f"{operator}{val if val != int(val) else int(val)}" if operator else str(val if val != int(val) else int(val))
        flag, note = classify_egfr(val, operator=operator)
        metrics.append({
            "test_name": "eGFR",
            "value": val_str,
            "unit": "mL/min/1.73m2",
            "reference_range": "> 60",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] eGFR: {val_str} mL/min/1.73m2 (Flag: {flag.upper()})")

    # 5. Total Cholesterol
    chol_match = re.search(
        r"(?:total\s*cholesterol|cholesterol(?:\s*,\s*total)?|serum\s*cholesterol|total\s*chol|(?<!hdl\s)(?<!ldl\s)\bcholesterol\b)"
        + DELIM +
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if chol_match:
        val = float(chol_match.group(1))
        flag, note = classify_cholesterol(val)
        val_str = str(val if val != int(val) else int(val))
        metrics.append({
            "test_name": "Total Cholesterol",
            "value": val_str,
            "unit": "mg/dL",
            "reference_range": "< 200",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] Total Cholesterol: {val_str} mg/dL (Flag: {flag.upper()})")

    # 6. LDL Cholesterol
    ldl_match = re.search(
        r"(?:ldl(?:\s*cholesterol|\s*-?\s*c)?|bad\s*cholesterol|low\s*density\s*lipoprotein)"
        + DELIM +
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if ldl_match:
        val = float(ldl_match.group(1))
        flag, note = classify_ldl(val)
        val_str = str(val if val != int(val) else int(val))
        metrics.append({
            "test_name": "LDL Cholesterol",
            "value": val_str,
            "unit": "mg/dL",
            "reference_range": "< 100",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] LDL Cholesterol: {val_str} mg/dL (Flag: {flag.upper()})")

    # 7. HDL Cholesterol
    hdl_match = re.search(
        r"(?:hdl(?:\s*cholesterol|\s*-?\s*c)?|good\s*cholesterol|high\s*density\s*lipoprotein)"
        + DELIM +
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if hdl_match:
        val = float(hdl_match.group(1))
        flag, note = classify_hdl(val)
        val_str = str(val if val != int(val) else int(val))
        metrics.append({
            "test_name": "HDL Cholesterol",
            "value": val_str,
            "unit": "mg/dL",
            "reference_range": ">= 40",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] HDL Cholesterol: {val_str} mg/dL (Flag: {flag.upper()})")

    # 8. Triglycerides
    tg_match = re.search(
        r"(?:serum\s*triglycerides|triglycerides?|trigs|\btg\b)"
        + DELIM +
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if tg_match:
        val = float(tg_match.group(1))
        flag, note = classify_triglycerides(val)
        val_str = str(val if val != int(val) else int(val))
        metrics.append({
            "test_name": "Triglycerides",
            "value": val_str,
            "unit": "mg/dL",
            "reference_range": "< 150",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] Triglycerides: {val_str} mg/dL (Flag: {flag.upper()})")

    # 9. Hemoglobin
    hb_match = re.search(
        r"(?:total\s*hemoglobin|(?<!glycated\s)hemoglobin(?![\s\-_]*a1c)|(?<!hgb[\s\-_])\bhb\b|\bhgb\b(?![\s\-_]*a1c))"
        + DELIM +
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:g\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if hb_match:
        val = float(hb_match.group(1))
        flag, note = classify_hemoglobin(val)
        val_str = str(val)
        metrics.append({
            "test_name": "Hemoglobin",
            "value": val_str,
            "unit": "g/dL",
            "reference_range": "12.0-17.5",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] Hemoglobin: {val_str} g/dL (Flag: {flag.upper()})")

    # 10. Platelets
    plt_match = re.search(
        r"(?:total\s*platelet\s*count|total\s*platelets|platelet\s*count|platelets?|\bplt\b)"
        + DELIM +
        r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:x10\^?[0-9]*/u[lL]|cells/mc[lL]|/mc[lL]|k/u[lL])?",
        text,
        re.IGNORECASE,
    )
    if plt_match:
        raw_val = plt_match.group(1).replace(",", "")
        val = float(raw_val)
        flag, note = classify_platelets(val)
        final_val = str(int(val * 1000 if val < 1000 else val))
        metrics.append({
            "test_name": "Platelet Count",
            "value": final_val,
            "unit": "cells/mcL",
            "reference_range": "150,000-450,000",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] Platelet Count: {final_val} cells/mcL (Flag: {flag.upper()})")

    # 11. White Blood Cells (WBC)
    wbc_match = re.search(
        r"(?:total\s*)?(?:white\s*blood\s*(?:cell\s*count|cells?|count)|w\.?\s*b\.?\s*c\.?|leu[ck]ocytes?(?:\s*count)?|\btlc\b)"
        + DELIM +
        r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:x?10\^?[0-9]*/(?:u[lL]|mc[lL]|L)|k/(?:u[lL]|mc[lL])|cells/(?:mc[lL]|u[lL]|cumm)|/(?:mc[lL]|u[lL]|cumm|mm3))?",
        text,
        re.IGNORECASE,
    )
    if wbc_match:
        raw_val = wbc_match.group(1).replace(",", "")
        val = float(raw_val)
        normalized_val = round(val / 1000.0, 2) if val >= 100 else val
        flag, note = classify_wbc(normalized_val)
        val_str = str(normalized_val)
        metrics.append({
            "test_name": "White Blood Cell Count",
            "value": val_str,
            "unit": "x10^3/mcL",
            "reference_range": "4.0-11.0",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] White Blood Cell Count: {val_str} x10^3/mcL (Flag: {flag.upper()})")

    # 12. Serum Creatinine
    cr_match = re.search(
        r"(?:serum\s*creatinine|creatinine(?:\s*,\s*serum)?|s\.?\s*creatinine|\bcreatinine\b|\bcr\b)"
        + DELIM +
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl|umol\s*/\s*l)?",
        text,
        re.IGNORECASE,
    )
    if cr_match:
        val = float(cr_match.group(1))
        flag, note = classify_creatinine(val)
        val_str = str(val)
        metrics.append({
            "test_name": "Serum Creatinine",
            "value": val_str,
            "unit": "mg/dL",
            "reference_range": "0.6-1.3",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] Serum Creatinine: {val_str} mg/dL (Flag: {flag.upper()})")

    # 13. Potassium
    k_match = re.search(
        r"(?:serum\s*potassium|potassium(?:\s*,\s*serum)?|\bpotassium\b|\bk\+?\b)"
        + DELIM +
        r"([0-9]+(?:\.[0-9]+)?)\s*(?:mmol\s*/\s*l|meq\s*/\s*l)?",
        text,
        re.IGNORECASE,
    )
    if k_match:
        val = float(k_match.group(1))
        flag, note = classify_potassium(val)
        val_str = str(val)
        metrics.append({
            "test_name": "Potassium",
            "value": val_str,
            "unit": "mmol/L",
            "reference_range": "3.5-5.1",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] Potassium: {val_str} mmol/L (Flag: {flag.upper()})")

    # 14. Sodium
    na_match = re.search(
        r"(?:serum\s*sodium|sodium(?:\s*,\s*serum)?|\bsodium\b|\bna\+?\b)"
        + DELIM +
        r"([0-9]{2,3}(?:\.[0-9]+)?)\s*(?:mmol\s*/\s*l|meq\s*/\s*l)?",
        text,
        re.IGNORECASE,
    )
    if na_match:
        val = float(na_match.group(1))
        flag, note = classify_sodium(val)
        val_str = str(val if val != int(val) else int(val))
        metrics.append({
            "test_name": "Sodium",
            "value": val_str,
            "unit": "mmol/L",
            "reference_range": "135-145",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })
        log_sink.append(f"[Pattern Match] Sodium: {val_str} mmol/L (Flag: {flag.upper()})")

    # --------------------------------------------------------------------------
    # SECONDARY HEURISTIC: Sequential Column Pairing for Multi-Column PDF Dumps
    # --------------------------------------------------------------------------
    already_extracted = {m["test_name"] for m in metrics}
    column_candidates = [
        ("HbA1c", re.compile(r"^(?:hba1c|hemoglobin\s*a1c|\ba1c\b)$", re.I)),
        ("Fasting Blood Glucose", re.compile(r"^(?:fasting\s*(?:blood)?\s*(?:sugar|glucose)|glucose|fbs)$", re.I)),
        ("eGFR", re.compile(r"^(?:egfr|estimated\s*gfr|\bgfr\b)$", re.I)),
        ("Serum Creatinine", re.compile(r"^(?:serum\s*creatinine|creatinine|\bcr\b)$", re.I)),
        ("Total Cholesterol", re.compile(r"^(?:total\s*cholesterol|cholesterol)$", re.I)),
        ("LDL Cholesterol", re.compile(r"^(?:ldl\s*(?:cholesterol)?|ldl-c|\bldl\b)$", re.I)),
        ("HDL Cholesterol", re.compile(r"^(?:hdl\s*(?:cholesterol)?|hdl-c|\bhdl\b)$", re.I)),
        ("Triglycerides", re.compile(r"^(?:triglycerides?|trigs|\btg\b)$", re.I)),
        ("Hemoglobin", re.compile(r"^(?:hemoglobin|\bhb\b|\bhgb\b)$", re.I)),
        ("Platelet Count", re.compile(r"^(?:platelet\s*count|platelets?|\bplt\b)$", re.I)),
        ("White Blood Cell Count", re.compile(r"^(?:white\s*blood\s*(?:cells?|count)|wbc|tlc)$", re.I)),
        ("Potassium", re.compile(r"^(?:potassium|\bk\+?\b)$", re.I)),
        ("Sodium", re.compile(r"^(?:sodium|\bna\+?\b)$", re.I)),
    ]

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    matched_column_tests: List[Tuple[int, str]] = []
    for l_idx, line in enumerate(lines):
        clean_ln = re.sub(r"[:=\-\|\.]+$", "", line).strip()
        for t_name, pat in column_candidates:
            if t_name not in already_extracted and pat.search(clean_ln):
                matched_column_tests.append((l_idx, t_name))
                break

    if len(matched_column_tests) >= 2:
        val_pattern = re.compile(r"^([><]=?\s*)?([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*([a-zA-Z/%^0-9\.\-]+)?$")
        start_search = matched_column_tests[-1][0] + 1
        val_lines = []
        for idx in range(start_search, len(lines)):
            curr_ln = lines[idx]
            if re.search(r"^(?:result|value|reading|test\s*result|observed|obs)s?[:\s]*$", curr_ln, re.I):
                continue
            vm = val_pattern.search(curr_ln)
            if vm:
                val_lines.append(vm)
                if len(val_lines) == len(matched_column_tests):
                    break

        if len(val_lines) == len(matched_column_tests):
            log_sink.append(f"[Columnar Heuristic] Detected sequential column layout: aligning {len(val_lines)} test names with columnar values.")
            for (l_idx, t_name), vm in zip(matched_column_tests, val_lines):
                op = (vm.group(1) or "").strip()
                raw_num = vm.group(2).replace(",", "")
                num_val = float(raw_num)

                if t_name == "HbA1c":
                    flag, note = classify_hba1c(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val), "unit": "%", "reference_range": "< 5.7", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "Fasting Blood Glucose":
                    flag, note = classify_glucose(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val if num_val != int(num_val) else int(num_val)), "unit": "mg/dL", "reference_range": "70-99", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "eGFR":
                    flag, note = classify_egfr(num_val, operator=op)
                    v_str = f"{op}{num_val if num_val != int(num_val) else int(num_val)}" if op else str(num_val if num_val != int(num_val) else int(num_val))
                    metrics.append({"test_name": t_name, "value": v_str, "unit": "mL/min/1.73m2", "reference_range": "> 60", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "Serum Creatinine":
                    flag, note = classify_creatinine(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val), "unit": "mg/dL", "reference_range": "0.6-1.3", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "Total Cholesterol":
                    flag, note = classify_cholesterol(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val if num_val != int(num_val) else int(num_val)), "unit": "mg/dL", "reference_range": "< 200", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "LDL Cholesterol":
                    flag, note = classify_ldl(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val if num_val != int(num_val) else int(num_val)), "unit": "mg/dL", "reference_range": "< 100", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "HDL Cholesterol":
                    flag, note = classify_hdl(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val if num_val != int(num_val) else int(num_val)), "unit": "mg/dL", "reference_range": ">= 40", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "Triglycerides":
                    flag, note = classify_triglycerides(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val if num_val != int(num_val) else int(num_val)), "unit": "mg/dL", "reference_range": "< 150", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "Hemoglobin":
                    flag, note = classify_hemoglobin(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val), "unit": "g/dL", "reference_range": "12.0-17.5", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "Platelet Count":
                    flag, note = classify_platelets(num_val)
                    metrics.append({"test_name": t_name, "value": str(int(num_val * 1000 if num_val < 1000 else num_val)), "unit": "cells/mcL", "reference_range": "150,000-450,000", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "White Blood Cell Count":
                    norm_wbc = round(num_val / 1000.0, 2) if num_val >= 100 else num_val
                    flag, note = classify_wbc(norm_wbc)
                    metrics.append({"test_name": t_name, "value": str(norm_wbc), "unit": "x10^3/mcL", "reference_range": "4.0-11.0", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "Potassium":
                    flag, note = classify_potassium(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val), "unit": "mmol/L", "reference_range": "3.5-5.1", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                elif t_name == "Sodium":
                    flag, note = classify_sodium(num_val)
                    metrics.append({"test_name": t_name, "value": str(num_val if num_val != int(num_val) else int(num_val)), "unit": "mmol/L", "reference_range": "135-145", "flag": flag, "clinical_note": note, "confidence": "high", "source": "columnar_table_match"})
                log_sink.append(f"[Columnar Heuristic Match] {t_name}: {num_val} (Flag: {flag.upper()})")

    if not metrics:
        log_sink.append("[Biomarker Scan Complete] No standard quantitative biomarker patterns matched in document text.")
    else:
        log_sink.append(f"[Biomarker Scan Complete] Successfully identified {len(metrics)} quantitative analyte(s).")

    return metrics


# --- generate_structured_interpretation ---
# What it does: Synthesizes quantitative clinical biomarkers into domain-specific clinical impressions
# (Glycemic Control, Lipid Profile, Renal Function, Cardiovascular, Hematology, Electrolytes) and actionable next steps.
# Why it's structured this way: Transforms isolated numerical test metrics into an organized, physician-grade diagnostic summary.
# Parameters & Returns: metrics (List[Dict]) -> Tuple[List[Dict[str, str]], List[str]].
# ------------------------------------------------------------------------------
def generate_structured_interpretation(metrics: List[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Categorizes extracted quantitative biomarkers into physiological systems,
    evaluating disease patterns (hyperglycemia, mixed dyslipidemia, renal impairment,
    hematologic/electrolyte shifts) and formulating evidence-based recommended next steps.
    """
    metrics_by_name = {m.get("test_name", ""): m for m in metrics}
    impressions: List[Dict[str, str]] = []
    next_steps: List[str] = []

    # 1. Glycemic Control
    fbs = metrics_by_name.get("Fasting Blood Glucose")
    a1c = metrics_by_name.get("HbA1c")
    if fbs or a1c:
        glycemic_abnormal = (fbs and fbs.get("flag") != "normal") or (a1c and a1c.get("flag") != "normal")
        if fbs and a1c:
            if glycemic_abnormal:
                status = "critical" if (fbs.get("flag") == "critical" or a1c.get("flag") == "critical") else "abnormal"
                detail = f"Poorly controlled hyperglycemia indicated by elevated Fasting Blood Glucose ({fbs['value']} {fbs.get('unit', 'mg/dL')}) and HbA1c ({a1c['value']}{a1c.get('unit', '%')})."
            else:
                status = "normal"
                detail = f"Optimal glycemic regulation with Fasting Blood Glucose ({fbs['value']} {fbs.get('unit', 'mg/dL')}) and HbA1c ({a1c['value']}{a1c.get('unit', '%')}) within target clinical limits."
        elif fbs:
            status = fbs.get("flag", "normal")
            if status != "normal":
                detail = f"Impaired fasting glucose regulation indicated by elevated reading at {fbs['value']} {fbs.get('unit', 'mg/dL')}."
            else:
                detail = f"Fasting Blood Glucose ({fbs['value']} {fbs.get('unit', 'mg/dL')}) is within standard clinical limits."
        else:
            status = a1c.get("flag", "normal")
            if status != "normal":
                detail = f"Suboptimal glycation index indicated by elevated HbA1c ({a1c['value']}{a1c.get('unit', '%')})."
            else:
                detail = f"HbA1c ({a1c['value']}{a1c.get('unit', '%')}) indicates optimal long-term glycemic regulation."
        impressions.append({"domain": "Glycemic Control", "status": status, "interpretation": detail})

    # 2. Lipid Profile
    chol = metrics_by_name.get("Total Cholesterol")
    tg = metrics_by_name.get("Triglycerides")
    hdl = metrics_by_name.get("HDL Cholesterol")
    ldl = metrics_by_name.get("LDL Cholesterol")
    lipid_markers = [m for m in (chol, tg, hdl, ldl) if m]
    if lipid_markers:
        lipid_abnormal = any(m.get("flag") != "normal" for m in lipid_markers)
        if lipid_abnormal:
            elevated = []
            if chol and chol.get("flag") != "normal":
                elevated.append(f"Total Cholesterol ({chol['value']} mg/dL)")
            if tg and tg.get("flag") != "normal":
                elevated.append(f"Triglycerides ({tg['value']} mg/dL)")
            if ldl and ldl.get("flag") != "normal":
                elevated.append(f"LDL ({ldl['value']} mg/dL)")
            hdl_low = (hdl and hdl.get("flag") != "normal")

            if len(elevated) >= 2 and hdl_low:
                detail = f"Mixed dyslipidemia with elevated {elevated[0]} and {elevated[1]}, alongside sub-optimal protective HDL ({hdl['value']} mg/dL)."
            elif len(elevated) >= 1 and hdl_low:
                detail = f"Atherogenic lipid pattern with elevated {elevated[0]} and reduced protective HDL ({hdl['value']} mg/dL)."
            elif elevated:
                detail = f"Hyperlipidemia characterized by elevated {', '.join(elevated)}."
            else:
                detail = f"Low HDL cholesterol ({hdl['value']} mg/dL), presenting an isolated cardiovascular risk factor."
            status = "critical" if any(m.get("flag") == "critical" for m in lipid_markers) else "abnormal"
        else:
            status = "normal"
            detail = "Lipid profile markers (Total Cholesterol, Triglycerides, HDL, LDL) are balanced within cardioprotective target ranges."
        impressions.append({"domain": "Lipid Profile", "status": status, "interpretation": detail})

    # 3. Renal Function
    cr = metrics_by_name.get("Serum Creatinine")
    egfr = metrics_by_name.get("eGFR")
    if cr or egfr:
        renal_abnormal = (cr and cr.get("flag") != "normal") or (egfr and egfr.get("flag") != "normal")
        if renal_abnormal:
            status = "critical" if ((cr and cr.get("flag") == "critical") or (egfr and egfr.get("flag") == "critical")) else "abnormal"
            egfr_sub = f" and reduced eGFR ({egfr['value']} {egfr.get('unit', 'mL/min/1.73m2')})" if (egfr and egfr.get("flag") != "normal") else ""
            if cr and cr.get("flag") != "normal":
                severity = "markedly" if cr.get("flag") == "critical" else "mildly"
                detail = f"Serum Creatinine is {severity} elevated ({cr['value']} {cr.get('unit', 'mg/dL')}){egfr_sub}, warranting ongoing monitoring of kidney function."
            else:
                detail = f"Reduced glomerular filtration rate noted (eGFR {egfr['value']} {egfr.get('unit', 'mL/min/1.73m2')}), indicating compromised renal clearance."
        else:
            status = "normal"
            egfr_sub = f" and eGFR ({egfr['value']} {egfr.get('unit', 'mL/min/1.73m2')})" if egfr else ""
            detail = f"Renal function parameters (Serum Creatinine {cr['value']} {cr.get('unit', 'mg/dL')}{egfr_sub}) are intact within expected baseline clearance."
        impressions.append({"domain": "Renal Function", "status": status, "interpretation": detail})

    # 4. Cardiovascular & Vitals
    bp = metrics_by_name.get("Blood Pressure")
    if bp:
        status = bp.get("flag", "normal")
        if status != "normal":
            stage = "Hypertensive crisis" if status == "critical" else "Stage 2 Hypertension" if status == "high" else "Elevated blood pressure"
            detail = f"{stage} reading observed ({bp['value']} mmHg), requiring hemodynamic monitoring and clinical management."
        else:
            detail = f"Normotensive hemodynamic profile with Blood Pressure ({bp['value']} mmHg) within standard resting clinical parameters."
        impressions.append({"domain": "Cardiovascular & Vitals", "status": status, "interpretation": detail})

    # 5. Hematology
    hb = metrics_by_name.get("Hemoglobin")
    plt = metrics_by_name.get("Platelet Count")
    wbc = metrics_by_name.get("White Blood Cell Count")
    heme_markers = [m for m in (hb, plt, wbc) if m]
    if heme_markers:
        heme_abnormal = any(m.get("flag") != "normal" for m in heme_markers)
        if heme_abnormal:
            status = "critical" if any(m.get("flag") == "critical" for m in heme_markers) else "abnormal"
            issues = []
            if hb and hb.get("flag") != "normal":
                desc = "low hemoglobin suggestive of anemia" if hb.get("flag") in ("low", "critical") else "elevated hemoglobin"
                issues.append(f"{desc} ({hb['value']} {hb.get('unit', 'g/dL')})")
            if plt and plt.get("flag") != "normal":
                desc = "thrombocytopenia" if plt.get("flag") in ("low", "critical") else "thrombocytosis"
                issues.append(f"{desc} ({plt['value']} {plt.get('unit', 'cells/mcL')})")
            if wbc and wbc.get("flag") != "normal":
                desc = "leukocytosis reflecting possible infection or inflammation" if wbc.get("flag") in ("high", "critical") else "leukopenia"
                issues.append(f"{desc} ({wbc['value']} {wbc.get('unit', 'x10^3/mcL')})")
            detail = f"Hematologic evaluation indicates {', '.join(issues)}."
        else:
            status = "normal"
            labels = []
            if plt:
                try:
                    num_plt = int(float(str(plt["value"]).replace(",", "")))
                    labels.append(f"Platelet count ({num_plt:,} {plt.get('unit', 'cells/mcL')})")
                except Exception:
                    labels.append(f"Platelet count ({plt['value']} {plt.get('unit', 'cells/mcL')})")
            if hb:
                labels.append(f"Hemoglobin ({hb['value']} {hb.get('unit', 'g/dL')})")
            if wbc:
                labels.append(f"WBC ({wbc['value']} {wbc.get('unit', 'x10^3/mcL')})")
            detail = f"{', '.join(labels)} is within normal reference limits." if len(labels) == 1 else f"{', '.join(labels)} are within normal reference limits."
        impressions.append({"domain": "Hematology", "status": status, "interpretation": detail})

    # 6. Electrolytes
    k = metrics_by_name.get("Potassium")
    na = metrics_by_name.get("Sodium")
    if k or na:
        lytes_abnormal = (k and k.get("flag") != "normal") or (na and na.get("flag") != "normal")
        if lytes_abnormal:
            status = "critical" if ((k and k.get("flag") == "critical") or (na and na.get("flag") == "critical")) else "abnormal"
            disc = []
            if k and k.get("flag") != "normal":
                disc.append(f"Potassium is {k.get('flag')} ({k['value']} {k.get('unit', 'mmol/L')})")
            if na and na.get("flag") != "normal":
                disc.append(f"Sodium is {na.get('flag')} ({na['value']} {na.get('unit', 'mmol/L')})")
            detail = f"Electrolyte dysregulation identified: {'; '.join(disc)}."
        else:
            status = "normal"
            parts = []
            if na:
                parts.append(f"Sodium ({na['value']} {na.get('unit', 'mmol/L')})")
            if k:
                parts.append(f"Potassium ({k['value']} {k.get('unit', 'mmol/L')})")
            detail = f"Serum electrolytes ({', '.join(parts)}) demonstrate balanced fluid and osmolar homeostasis."
        impressions.append({"domain": "Electrolytes & Metabolic", "status": status, "interpretation": detail})

    # Recommended Next Steps Synthesis
    has_glycemic = any(imp["domain"] == "Glycemic Control" and imp["status"] != "normal" for imp in impressions)
    has_lipid = any(imp["domain"] == "Lipid Profile" and imp["status"] != "normal" for imp in impressions)
    has_renal = any(imp["domain"] == "Renal Function" and imp["status"] != "normal" for imp in impressions)
    has_bp = any(imp["domain"] == "Cardiovascular & Vitals" and imp["status"] != "normal" for imp in impressions)
    has_heme = any(imp["domain"] == "Hematology" and imp["status"] != "normal" for imp in impressions)
    has_lytes = any(imp["domain"] == "Electrolytes & Metabolic" and imp["status"] != "normal" for imp in impressions)

    if has_glycemic or has_lipid:
        next_steps.append("Schedule a follow-up appointment with your physician or endocrinologist to discuss glycemic management and lipid therapy.")
    if has_glycemic or has_renal:
        next_steps.append("Re-test fasting glucose and renal panel as directed by your clinician.")
    if has_bp:
        next_steps.append("Implement serial ambulatory blood pressure tracking (morning and evening) for clinical review.")
    if has_heme:
        next_steps.append("Consult your physician for complete blood count monitoring and nutritional evaluation.")
    if has_lytes:
        next_steps.append("Review fluid hydration status and electrolyte intake with your care provider.")

    # General lifestyle modification guidance
    if any(imp["status"] != "normal" for imp in impressions):
        next_steps.append("Discuss lifestyle, dietary, and physical activity modifications.")
    else:
        next_steps.append("Continue current wellness plan, balanced nutrition, and regular physical activity.")
        next_steps.append("Schedule routine annual clinical preventive screening with your primary care provider.")

    return impressions, next_steps


# --- parse_report_content ---
# What it does: Master parsing pipeline orchestrating text extraction, biomarker identification, and narrative summary generation.
# Why it's structured this way: End-to-end processing pipeline transforming unparsed files into fully structured, flagged clinical reports.
# Parameters & Returns: content (Union[str, bytes]), title (str), file_type (str) -> Complete dictionary with metrics, summary, logs, and OCR status.
# ------------------------------------------------------------------------------
def parse_report_content(content: Union[str, bytes], title: str = "", file_type: str = "") -> Dict[str, Any]:
    """
    Main report parsing and clinical analysis pipeline:
    1. Extracts text from raw bytes (PDF via pypdf with fallbacks, Image with OCR fallback, or text stream).
    2. Parses quantitative clinical values and flags abnormal/critical findings.
    3. Synthesizes a structured clinical interpretation summary, domain impressions, and recommended next steps.
    4. Returns extracted metrics, metadata, and full extraction fallback audit log.
    """
    text, fallback_log, ocr_status, confidence = extract_text_and_logs(content, file_type=file_type)

    sanitized_text = text.replace("\x00", "").strip()
    raw_metrics = extract_metrics_from_text(sanitized_text, fallback_log=fallback_log)

    # Sanitize all string fields in extracted metrics
    metrics = []
    for m in raw_metrics:
        clean_m = {}
        for k, v in m.items():
            if isinstance(v, str):
                clean_m[k] = v.replace("\x00", "")
            else:
                clean_m[k] = v
        metrics.append(clean_m)

    abnormal_metrics = [m for m in metrics if m["flag"] != "normal"]
    critical_metrics = [m for m in metrics if m["flag"] == "critical"]

    # Synthesize structured clinical impressions and recommended next steps
    clinical_impressions, next_steps = generate_structured_interpretation(metrics)

    clean_title = (title or "").replace("\x00", "").strip()
    summary_lines = []
    if clean_title:
        summary_lines.append(f"Clinical Report Analysis for '{clean_title}':")
    summary_lines.append(f"Total metrics identified: {len(metrics)}.")

    if critical_metrics:
        crit_names = ", ".join(m["test_name"] for m in critical_metrics)
        summary_lines.append(f"CRITICAL WARNING: Critical alerts for {crit_names}.")
    elif abnormal_metrics:
        abn_names = ", ".join(m["test_name"] for m in abnormal_metrics)
        summary_lines.append(f"Attention required: Abnormal findings detected for {abn_names}.")
    else:
        summary_lines.append("All extracted clinical indicators are within standard reference ranges.")

    summary_text = " ".join(summary_lines).replace("\x00", "").strip()
    fallback_log.append(f"[Report Summary] {summary_text}")

    return {
        "extracted_text": sanitized_text,
        "metrics": metrics,
        "total_metrics_extracted": len(metrics),
        "abnormal_flags_count": len(abnormal_metrics),
        "critical_flags_count": len(critical_metrics),
        "summary": summary_text,
        "clinical_impression": clinical_impressions,
        "recommended_next_steps": next_steps,
        "next_steps": next_steps,
        "ocr_status": ocr_status,
        "confidence": confidence,
        "fallback_log": fallback_log,
        "extraction_logs": fallback_log,
    }

