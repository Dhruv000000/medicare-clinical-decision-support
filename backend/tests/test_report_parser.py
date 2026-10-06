import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile
from apps.appointments.models import Appointment
from apps.medical_records.models import MedicalRecord, LabReport, LabResult
from apps.medical_records.services.report_parser import (
    extract_metrics_from_text,
    parse_report_content,
    classify_blood_pressure,
    classify_glucose,
    classify_hba1c,
    classify_hemoglobin,
    classify_platelets,
    classify_wbc,
)


@pytest.mark.django_db
class TestMedicalReportParser:
    """
    Test suite for clinical metrics regex extraction, reference range flagging,
    and report analysis endpoints with permission checks.
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.patient_a = User.objects.create_user(
            email="patient.report.a@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.profile_a = PatientProfile.objects.create(user=self.patient_a)

        self.patient_b = User.objects.create_user(
            email="patient.report.b@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.profile_b = PatientProfile.objects.create(user=self.patient_b)

        self.doctor = User.objects.create_user(
            email="doctor.report@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Marcus",
            last_name="Welby",
        )
        self.doc_profile = DoctorProfile.objects.create(
            user=self.doctor,
            license_number="LIC-MD-REP",
            specialization="General Medicine",
        )

        self.client = APIClient()

    # --- Unit Tests: Metric Classification & Regex Parsing ---

    def test_blood_pressure_classification(self):
        # Normal
        flag, _ = classify_blood_pressure(115, 75)
        assert flag == "normal"

        # Elevated / Stage 1
        flag, _ = classify_blood_pressure(135, 85)
        assert flag == "elevated"

        # Stage 2 High
        flag, _ = classify_blood_pressure(155, 98)
        assert flag == "high"

        # Hypertensive Crisis
        flag, _ = classify_blood_pressure(185, 125)
        assert flag == "critical"

        # Hypotension
        flag, _ = classify_blood_pressure(80, 50)
        assert flag == "low"

    def test_glucose_and_hba1c_classification(self):
        assert classify_glucose(85)[0] == "normal"
        assert classify_glucose(115)[0] == "elevated"
        assert classify_glucose(145)[0] == "high"
        assert classify_glucose(350)[0] == "critical"
        assert classify_glucose(50)[0] == "critical"

        assert classify_hba1c(5.2)[0] == "normal"
        assert classify_hba1c(6.0)[0] == "elevated"
        assert classify_hba1c(7.4)[0] == "high"
        assert classify_hba1c(11.2)[0] == "critical"

    def test_hemoglobin_and_platelets_classification(self):
        assert classify_hemoglobin(14.5)[0] == "normal"
        assert classify_hemoglobin(10.5)[0] == "low"
        assert classify_hemoglobin(6.2)[0] == "critical"
        assert classify_hemoglobin(19.0)[0] == "high"

        assert classify_platelets(250000)[0] == "normal"
        assert classify_platelets(110000)[0] == "low"
        assert classify_platelets(35000)[0] == "critical"
        assert classify_platelets(550000)[0] == "high"

    def test_wbc_classification(self):
        assert classify_wbc(6.5)[0] == "normal"
        assert classify_wbc(3.2)[0] == "low"
        assert classify_wbc(12.4)[0] == "high"
        assert classify_wbc(32.0)[0] == "critical"
        assert classify_wbc(1.5)[0] == "critical"
        # High count passed as cells/mcL
        assert classify_wbc(12400)[0] == "high"

    def test_wbc_extraction_variations(self):
        variations = [
            ("WBC = 12.4", "12.4", "high"),
            ("WBC: 12.4", "12.4", "high"),
            ("W.B.C: 12.4", "12.4", "high"),
            ("W.B.C. = 12.4", "12.4", "high"),
            ("Total WBC = 12.4", "12.4", "high"),
            ("Total WBC: 12.4 10^3/uL", "12.4", "high"),
            ("Total Leucocyte Count: 12.4", "12.4", "high"),
            ("Total Leukocyte Count = 12.4 x10^3/mcL", "12.4", "high"),
            ("TLC: 12.4", "12.4", "high"),
            ("White Blood Cells: 12.4 /mcL", "12.4", "high"),
            ("White Blood Cell Count: 12.4", "12.4", "high"),
            ("WBC: 12,400 cells/mcL", "12.4", "high"),
            ("WBC: 7.0", "7.0", "normal"),
        ]
        for text, expected_val, expected_flag in variations:
            extracted = extract_metrics_from_text(text)
            assert len(extracted) == 1, f"Failed for text '{text}': got {extracted}"
            wbc_metric = extracted[0]
            assert wbc_metric["test_name"] == "White Blood Cell Count"
            assert wbc_metric["value"] == expected_val
            assert wbc_metric["flag"] == expected_flag

    def test_parse_report_content_13_metrics_full_panel(self):
        full_panel_text = """
        OUTPATIENT CLINICAL SUMMARY & COMPREHENSIVE LAB PANEL:
        Blood Pressure: 138/86 mmHg
        Fasting Glucose: 110 mg/dL
        HbA1c: 6.2%
        Total Cholesterol: 210 mg/dL
        LDL Cholesterol: 140 mg/dL
        HDL Cholesterol: 38 mg/dL
        Triglycerides: 180 mg/dL
        Hemoglobin: 13.0 g/dL
        Platelet Count: 210,000 cells/mcL
        WBC = 12.4 10^3/uL
        Serum Creatinine: 1.0 mg/dL
        Potassium: 4.2 mmol/L
        Sodium: 140 mmol/L
        """
        analysis = parse_report_content(full_panel_text, title="Full Comprehensive Panel")
        assert analysis["total_metrics_extracted"] == 13
        metric_names = [m["test_name"] for m in analysis["metrics"]]
        assert "White Blood Cell Count" in metric_names
        wbc_metric = next(m for m in analysis["metrics"] if m["test_name"] == "White Blood Cell Count")
        assert wbc_metric["value"] == "12.4"
        assert wbc_metric["flag"] == "high"

    def test_parse_report_content_multimetric(self):
        raw_text = """
        OUTPATIENT CLINICAL SUMMARY & LAB PANEL:
        Blood Pressure: 142/92 mmHg
        Fasting Glucose: 135 mg/dL
        HbA1c: 7.1%
        Total Cholesterol: 235 mg/dL
        LDL Cholesterol: 162 mg/dL
        HDL Cholesterol: 36 mg/dL
        Triglycerides: 215 mg/dL
        Hemoglobin: 11.5 g/dL
        Platelet Count: 140,000 cells/mcL
        Serum Creatinine: 1.1 mg/dL
        """
        analysis = parse_report_content(raw_text, title="Annual Health Evaluation")

        assert analysis["total_metrics_extracted"] >= 8
        assert analysis["abnormal_flags_count"] >= 5
        metrics_dict = {m["test_name"]: m for m in analysis["metrics"]}

        assert metrics_dict["Blood Pressure"]["flag"] == "high"
        assert metrics_dict["Fasting Blood Glucose"]["flag"] == "high"
        assert metrics_dict["HbA1c"]["flag"] == "high"
        assert metrics_dict["Total Cholesterol"]["flag"] == "elevated"
        assert metrics_dict["HDL Cholesterol"]["flag"] == "low"
        assert metrics_dict["Hemoglobin"]["flag"] == "low"
        assert metrics_dict["Serum Creatinine"]["flag"] == "normal"

        assert "Attention required" in analysis["summary"]

    # --- API Endpoint & Authorization Tests ---

    def test_patient_can_analyze_own_lab_report(self):
        report = LabReport.objects.create(
            patient=self.patient_a,
            title="Metabolic Profile",
            extracted_text="BP: 130/85 mmHg. Fasting Blood Sugar: 105 mg/dL. Hemoglobin: 13.8 g/dL.",
        )

        self.client.force_authenticate(user=self.patient_a)
        res = self.client.post(f"/api/v1/records/{report.id}/analyze/", format="json")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["record_id"] == report.id
        assert data["patient_id"] == self.patient_a.id
        assert data["total_metrics_extracted"] >= 2

        # Verify LabResult models were created and linked to the LabReport
        assert LabResult.objects.filter(report=report, test_name="Blood Pressure").exists()
        assert LabResult.objects.filter(report=report, test_name="Fasting Blood Glucose").exists()

        # Check alias endpoint /api/v1/medical-records/<id>/analyze/
        alias_res = self.client.post(f"/api/v1/medical-records/{report.id}/analyze/", format="json")
        assert alias_res.status_code == status.HTTP_200_OK

    def test_unauthorized_patient_cannot_analyze_another_patients_report(self):
        report = LabReport.objects.create(
            patient=self.patient_b,
            title="Private Panel",
            extracted_text="Blood Pressure: 120/80 mmHg",
        )

        self.client.force_authenticate(user=self.patient_a)
        res = self.client.post(f"/api/v1/medical-records/{report.id}/analyze/", format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "cannot access medical records belonging to another patient" in res.json()["error"]["message"]

    def test_doctor_cannot_analyze_unauthorized_patients_report(self):
        report = LabReport.objects.create(
            patient=self.patient_b,
            title="Patient B Lab Report",
            extracted_text="Fasting Glucose: 140 mg/dL",
        )

        self.client.force_authenticate(user=self.doctor)
        res = self.client.post(f"/api/v1/medical-records/{report.id}/analyze/", format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "Doctor does not have active clinical authorization" in res.json()["error"]["message"]

    def test_doctor_can_analyze_authorized_patients_report(self):
        # Establish relationship via appointment
        Appointment.objects.create(
            patient=self.patient_b,
            doctor=self.doctor,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            status=Appointment.Status.CONFIRMED,
        )

        report = LabReport.objects.create(
            patient=self.patient_b,
            title="Cardiac & Renal Workup",
            extracted_text="Blood Pressure: 165/100 mmHg. Serum Creatinine: 1.8 mg/dL.",
        )

        self.client.force_authenticate(user=self.doctor)
        res = self.client.post(f"/api/v1/medical-records/{report.id}/analyze/", format="json")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["record_id"] == report.id
        assert data["patient_id"] == self.patient_b.id
        assert data["abnormal_flags_count"] >= 2
        assert LabResult.objects.filter(report=report, test_name="Serum Creatinine", flag="high").exists()

    def test_parse_and_save_report_with_null_bytes(self):
        text_with_null = "Fasting Glucose: 115\x00 mg/dL.\x00 HbA1c: 6.0%.\x00"
        report = LabReport.objects.create(
            patient=self.patient_a,
            title="Blood Test with Null Bytes",
        )

        self.client.force_authenticate(user=self.patient_a)
        res = self.client.post(
            f"/api/v1/medical-records/{report.id}/analyze/",
            data={"text": text_with_null},
            format="json",
        )

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "\x00" not in data["extracted_text"]
        assert "\x00" not in data["summary"]
        report.refresh_from_db()
        assert "\x00" not in report.extracted_text
        assert "\x00" not in report.analysis_summary
        assert LabResult.objects.filter(report=report).count() >= 2
        for result in LabResult.objects.filter(report=report):
            assert "\x00" not in result.test_name
            assert "\x00" not in result.value
            assert "\x00" not in result.unit
