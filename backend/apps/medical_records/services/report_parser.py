import io
import logging
import re
import zlib
from typing import Union, List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


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


def _extract_text_from_pdf_bytes(content: bytes) -> str:
    """
    Extracts plain text from PDF stream by decompressing FlateDecode streams
    and reading text operators (Tj, TJ, ', \").
    """
    text_chunks = []

    # 1. Parse PDF stream objects: << ... >> stream ... endstream
    stream_pattern = re.compile(rb"<<(.*?)>>\s*stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
    found_stream = False

    for match in stream_pattern.finditer(content):
        found_stream = True
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

        # Extract array text elements in TJ (e.g., [(text1) -10 (text2)] TJ)
        for tj in re.finditer(rb"\[(.*?)\]\s*TJ", decompressed):
            tj_content = tj.group(1)
            for m in re.finditer(rb"\(((?:\\\(|\\\)|\\[^()]|[^()])*)\)", tj_content):
                cleaned = _clean_pdf_string(m.group(1))
                if cleaned:
                    text_chunks.append(cleaned)

    # 2. Fallback: uncompressed / literal matches across entire content
    if not text_chunks:
        direct_matches = re.findall(rb"\(([^\(\)]*)\)\s*(?:Tj|TJ|\')?", content)
        for m in direct_matches:
            try:
                decoded = m.decode("utf-8", errors="ignore").strip()
                if decoded and len(decoded) > 1:
                    text_chunks.append(decoded)
            except Exception:
                pass

    # 3. If extracted text is still minimal, extract printable ASCII sequences
    joined_text = " ".join(text_chunks).strip()
    if len(joined_text) < 10:
        printable = re.sub(rb"[^\x20-\x7E\r\n\t]", b" ", content)
        ascii_candidate = printable.decode("utf-8", errors="ignore").strip()
        # Filter out PDF syntax markers
        filtered_lines = [
            line.strip() for line in ascii_candidate.splitlines()
            if line.strip() and not line.strip().startswith(("%", "obj", "endobj", "xref", "trailer", "startxref"))
        ]
        if filtered_lines:
            joined_text = "\n".join(filtered_lines)

    # Normalize whitespace
    joined_text = re.sub(r"[ \t]+", " ", joined_text).replace("\x00", "")
    return joined_text.strip()


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


def extract_text_from_stream(content: Union[str, bytes], file_type: str = "") -> str:
    """
    Extracts plain text from string, raw bytes, PDF streams (with FlateDecode support),
    or image files via OCR when dependencies are available.
    """
    if isinstance(content, str):
        return content.replace("\x00", "")

    if isinstance(content, bytes):
        # 1. PDF detection
        if content.startswith(b"%PDF") or file_type.lower() == "pdf":
            return _extract_text_from_pdf_bytes(content).replace("\x00", "")

        # 2. Image detection (PNG, JPEG, WebP)
        is_image = (
            content.startswith(b"\x89PNG\r\n\x1a\n")
            or content.startswith(b"\xff\xd8\xff")
            or (content.startswith(b"RIFF") and b"WEBP" in content[:16])
            or file_type.lower() in ("png", "jpg", "jpeg", "webp")
        )
        if is_image:
            ocr_text, status, _ = _extract_text_from_image_bytes(content)
            if ocr_text:
                return ocr_text.replace("\x00", "")
            # Graceful non-blocking degradation when OCR is not available/returns empty
            logger.info("Image upload processed; OCR status: %s", status)
            return ""

        # 3. Default text decoding
        return content.decode("utf-8", errors="replace").replace("\x00", "")

    return str(content).replace("\x00", "")


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


def extract_metrics_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extracts key quantitative metrics and reference range flags from text using regex.
    Preserves exact keys and format required by LabResult persistence and frontend contracts.
    """
    metrics = []

    # 1. Blood Pressure: e.g. "135/88", "BP: 120/80 mmHg"
    bp_match = re.search(
        r"(?:blood\s*pressure|b\.?p\.?)?[:\s]*\b([0-9]{2,3})\s*[/]\s*([0-9]{2,3})\s*(?:mm\s*hg)?\b",
        text,
        re.IGNORECASE,
    )
    if bp_match:
        sys_val = float(bp_match.group(1))
        dia_val = float(bp_match.group(2))
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

    # 2. Glucose / Fasting Blood Sugar
    fbs_match = re.search(
        r"(?:fasting\s*(?:blood)?\s*(?:sugar|glucose)|fbs|blood\s*glucose|glucose)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if fbs_match:
        val = float(fbs_match.group(1))
        flag, note = classify_glucose(val)
        metrics.append({
            "test_name": "Fasting Blood Glucose",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "70-99",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 3. HbA1c
    hba1c_match = re.search(
        r"(?:hba1c|glycated\s*hemoglobin|a1c)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*%?",
        text,
        re.IGNORECASE,
    )
    if hba1c_match:
        val = float(hba1c_match.group(1))
        flag, note = classify_hba1c(val)
        metrics.append({
            "test_name": "HbA1c",
            "value": str(val),
            "unit": "%",
            "reference_range": "< 5.7",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 4. Total Cholesterol
    chol_match = re.search(
        r"(?:total\s*cholesterol|cholesterol)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if chol_match:
        val = float(chol_match.group(1))
        flag, note = classify_cholesterol(val)
        metrics.append({
            "test_name": "Total Cholesterol",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "< 200",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 5. LDL Cholesterol
    ldl_match = re.search(
        r"(?:ldl(?:\s*cholesterol)?|bad\s*cholesterol)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if ldl_match:
        val = float(ldl_match.group(1))
        flag, note = classify_ldl(val)
        metrics.append({
            "test_name": "LDL Cholesterol",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "< 100",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 6. HDL Cholesterol
    hdl_match = re.search(
        r"(?:hdl(?:\s*cholesterol)?|good\s*cholesterol)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if hdl_match:
        val = float(hdl_match.group(1))
        flag, note = classify_hdl(val)
        metrics.append({
            "test_name": "HDL Cholesterol",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": ">= 40",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 7. Triglycerides
    tg_match = re.search(
        r"(?:triglycerides|trigs)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if tg_match:
        val = float(tg_match.group(1))
        flag, note = classify_triglycerides(val)
        metrics.append({
            "test_name": "Triglycerides",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "< 150",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 8. Hemoglobin
    hb_match = re.search(
        r"(?:hemoglobin|hb|hgb)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:g\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if hb_match:
        val = float(hb_match.group(1))
        flag, note = classify_hemoglobin(val)
        metrics.append({
            "test_name": "Hemoglobin",
            "value": str(val),
            "unit": "g/dL",
            "reference_range": "12.0-17.5",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 9. Platelets
    plt_match = re.search(
        r"(?:platelets?|platelet\s*count|plt)[:\s]*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:x10\^?[0-9]*/u[lL]|cells/mc[lL]|/mc[lL]|k/u[lL])?",
        text,
        re.IGNORECASE,
    )
    if plt_match:
        raw_val = plt_match.group(1).replace(",", "")
        val = float(raw_val)
        flag, note = classify_platelets(val)
        metrics.append({
            "test_name": "Platelet Count",
            "value": str(int(val * 1000 if val < 1000 else val)),
            "unit": "cells/mcL",
            "reference_range": "150,000-450,000",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 10. White Blood Cells (WBC)
    wbc_match = re.search(
        r"(?:total\s*)?(?:white\s*blood\s*(?:cell\s*count|cells?|count)|w\.?\s*b\.?\s*c\.?|leu[ck]ocytes?(?:\s*count)?|\btlc\b)[:\s=\-]+([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:x?10\^?[0-9]*/(?:u[lL]|mc[lL]|L)|k/(?:u[lL]|mc[lL])|cells/(?:mc[lL]|u[lL]|cumm)|/(?:mc[lL]|u[lL]|cumm|mm3))?",
        text,
        re.IGNORECASE,
    )
    if wbc_match:
        raw_val = wbc_match.group(1).replace(",", "")
        val = float(raw_val)
        normalized_val = round(val / 1000.0, 2) if val >= 100 else val
        flag, note = classify_wbc(normalized_val)
        metrics.append({
            "test_name": "White Blood Cell Count",
            "value": str(normalized_val),
            "unit": "x10^3/mcL",
            "reference_range": "4.0-11.0",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 11. Serum Creatinine
    cr_match = re.search(
        r"(?:serum\s*creatinine|creatinine)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mg\s*/\s*dl)?",
        text,
        re.IGNORECASE,
    )
    if cr_match:
        val = float(cr_match.group(1))
        flag, note = classify_creatinine(val)
        metrics.append({
            "test_name": "Serum Creatinine",
            "value": str(val),
            "unit": "mg/dL",
            "reference_range": "0.6-1.3",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 12. Potassium
    k_match = re.search(
        r"(?:serum\s*potassium|potassium|\bk\+?\b)[:\s]*([0-9]+(?:\.[0-9]+)?)\s*(?:mmol\s*/\s*l|meq\s*/\s*l)?",
        text,
        re.IGNORECASE,
    )
    if k_match:
        val = float(k_match.group(1))
        flag, note = classify_potassium(val)
        metrics.append({
            "test_name": "Potassium",
            "value": str(val),
            "unit": "mmol/L",
            "reference_range": "3.5-5.1",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    # 13. Sodium
    na_match = re.search(
        r"(?:serum\s*sodium|sodium|\bna\+?\b)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(?:mmol\s*/\s*l|meq\s*/\s*l)?",
        text,
        re.IGNORECASE,
    )
    if na_match:
        val = float(na_match.group(1))
        flag, note = classify_sodium(val)
        metrics.append({
            "test_name": "Sodium",
            "value": str(val),
            "unit": "mmol/L",
            "reference_range": "135-145",
            "flag": flag,
            "clinical_note": note,
            "confidence": "high",
            "source": "pattern_match",
        })

    return metrics


def parse_report_content(content: Union[str, bytes], title: str = "", file_type: str = "") -> Dict[str, Any]:
    """
    Main report parsing and clinical analysis pipeline:
    1. Extracts text from raw bytes (PDF, Image with OCR fallback, or text stream).
    2. Parses quantitative clinical values and flags abnormal/critical findings.
    3. Synthesizes a structured clinical interpretation summary.
    """
    ocr_status = "not_applicable"
    confidence = "high"

    if isinstance(content, bytes):
        if content.startswith(b"\x89PNG") or content.startswith(b"\xff\xd8\xff") or file_type in ("png", "jpg", "jpeg", "webp"):
            text, ocr_status, confidence = _extract_text_from_image_bytes(content)
        else:
            text = extract_text_from_stream(content, file_type=file_type)
    else:
        text = extract_text_from_stream(content)

    sanitized_text = text.replace("\x00", "").strip()
    raw_metrics = extract_metrics_from_text(sanitized_text)

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

    return {
        "extracted_text": sanitized_text,
        "metrics": metrics,
        "total_metrics_extracted": len(metrics),
        "abnormal_flags_count": len(abnormal_metrics),
        "critical_flags_count": len(critical_metrics),
        "summary": summary_text,
        "ocr_status": ocr_status,
        "confidence": confidence,
    }

