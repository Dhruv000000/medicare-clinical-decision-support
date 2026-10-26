import pytest
import re
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile
from apps.appointments.models import Appointment
from apps.predictions.models import DiseasePrediction, SymptomAnalysis, DiseasePredictionHistory
from apps.predictions.services.symptom_parser import (
    parse_symptoms,
    get_canonical_symptom_catalog,
    suggest_related_symptoms,
)
from apps.predictions.services.disease_engine import predict_diseases
from apps.predictions.services.shap_explainer import explain_prediction


@pytest.mark.django_db
class TestPredictionsAndShap:
    """
    Test suite for symptom parsing, disease prediction engine, SHAP explanations,
    and patient authorization boundaries.
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.patient_a = User.objects.create_user(
            email="patient.pred.a@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.profile_a = PatientProfile.objects.create(user=self.patient_a)

        self.patient_b = User.objects.create_user(
            email="patient.pred.b@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.profile_b = PatientProfile.objects.create(user=self.patient_b)

        self.doctor = User.objects.create_user(
            email="doctor.pred@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Elena",
            last_name="Rostova",
        )
        self.doc_profile = DoctorProfile.objects.create(
            user=self.doctor,
            license_number="LIC-PRED-99",
            specialization="Internal Medicine",
        )

        self.client = APIClient()

    # --- Unit Tests: Symptom Parsing & Disease Engine ---

    def test_symptom_normalization_with_noisy_input(self):
        noisy_text = "I've been having high temperature, a hacking cough, and severe head hurting since yesterday!!"
        parsed = parse_symptoms(noisy_text)

        canonical = parsed["canonical_symptoms"]
        assert "fever" in canonical
        assert "cough" in canonical
        assert "headache" in canonical

        vector = parsed["feature_vector"]
        assert vector["fever"] == 1
        assert vector["cough"] == 1
        assert vector["headache"] == 1
        assert vector["polyuria"] == 0

        # Test array input with slang
        array_input = ["runny nose", "feverish", "peeing often"]
        parsed_array = parse_symptoms(array_input)
        assert "rhinorrhea" in parsed_array["canonical_symptoms"]
        assert "fever" in parsed_array["canonical_symptoms"]
        assert "polyuria" in parsed_array["canonical_symptoms"]

    def test_disease_prediction_probabilities_and_ranking(self):
        # Diabetes profile: polyuria + polydipsia + weight_loss
        parsed = parse_symptoms(["frequent urination", "excessive thirst", "unexplained weight loss"])
        prediction = predict_diseases(parsed["feature_vector"])

        top = prediction["top_prediction"]
        assert top["disease"] == "Type 2 Diabetes"
        assert top["probability"] > 0.40

        # Assert probability sum equals 1.0 (within float tolerance)
        prob_sum = sum(d["probability"] for d in prediction["ranked_diagnoses"])
        assert abs(prob_sum - 1.0) < 0.001

        # Assert ranked descending
        probs = [d["probability"] for d in prediction["ranked_diagnoses"]]
        assert probs == sorted(probs, reverse=True)

    def test_shap_attribution_schema_and_values(self):
        parsed = parse_symptoms(["fever", "cough", "headache"])
        prediction = predict_diseases(parsed["feature_vector"])
        top_disease = prediction["top_prediction"]["disease"]

        attributions = explain_prediction(parsed["feature_vector"], top_disease)
        assert len(attributions) > 0

        for attr in attributions:
            assert "feature" in attr
            assert "contribution" in attr
            assert "direction" in attr
            assert "baseline" in attr

            assert isinstance(attr["feature"], str)
            assert isinstance(attr["contribution"], (int, float))
            assert attr["direction"] in ["increases_risk", "decreases_risk"]
            assert isinstance(attr["baseline"], (int, float))
            assert attr["contribution"] >= 0

    # --- API Endpoint & Authorization Tests ---

    def test_symptoms_parse_endpoint(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {"text": "I feel dizzy, nauseous, and my head is throbbing."}
        res = self.client.post("/api/v1/predictions/symptoms/", payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "canonical_symptoms" in data
        assert "headache" in data["canonical_symptoms"]
        assert "dizziness" in data["canonical_symptoms"]
        assert "nausea" in data["canonical_symptoms"]
        assert "suggested_symptoms" in data
        assert "catalog" in data

    def test_patient_can_create_disease_prediction_for_self(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "symptoms": ["fever", "cough", "body aches", "chills"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["patient_id"] == self.patient_a.id
        assert data["predicted_condition"] == "Influenza"
        assert data["confidence"] > 0.40
        assert "shap_explanations" in data
        assert len(data["shap_explanations"]) > 0
        assert "disclaimer" in data
        assert "clinical decision support system" in data["disclaimer"]

        # Ensure saved to database
        assert DiseasePrediction.objects.filter(patient=self.patient_a, predicted_condition="Influenza").exists()
        assert DiseasePredictionHistory.objects.filter(patient=self.patient_a).count() == 1

    def test_patient_cannot_predict_for_another_patient(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "patient_id": self.patient_b.id,
            "symptoms": ["fever", "cough"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "Patients can only request predictions for themselves" in res.json()["error"]["message"]

    def test_doctor_cannot_predict_for_unauthorized_patient(self):
        self.client.force_authenticate(user=self.doctor)
        payload = {
            "patient_id": self.patient_b.id,
            "symptoms": ["chest pain", "shortness of breath"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "Doctor does not have active clinical authorization for this patient." in res.json()["error"]["message"]

    def test_doctor_can_predict_for_authorized_patient(self):
        # Establish relationship via appointment
        Appointment.objects.create(
            patient=self.patient_b,
            doctor=self.doctor,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            status=Appointment.Status.CONFIRMED,
        )

        self.client.force_authenticate(user=self.doctor)
        payload = {
            "patient_id": self.patient_b.id,
            "symptoms": ["dyspnea", "cough", "chest tightness", "high temperature"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["patient_id"] == self.patient_b.id
        assert data["predicted_condition"] == "Pneumonia"
        assert data["severity"] in ["high", "critical"]
        assert DiseasePrediction.objects.filter(patient=self.patient_b, predicted_condition="Pneumonia").exists()

    # --- Unit Tests: Decoupled Labs, Calibrated Differentials, Clarification Prompts, and Red-Flag Guardrails ---

    def test_decouple_background_metabolic_labs_from_gi_complaint(self):
        """Verify chronic metabolic labs do not hijack GI predictions or dominate SHAP attributions."""
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "symptoms": ["nausea", "vomiting", "abdominal pain"],
            "vitals": {
                "glucose": 168.0,
                "hba1c": 8.4,
            },
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        # The prediction must NOT be hijacked to Type 2 Diabetes
        assert "Diabetes" not in data["predicted_condition"]
        assert any(k in data["predicted_condition"].lower() for k in ["fistula", "gastro", "esophagitis", "duodenitis", "pancreatitis", "ulcer", "ischemia", "angiodysplasia"])

        # SHAP attributions must be driven by GI symptoms, and glucose/HbA1c must be gated out
        features = data["explanation"]["features"]
        feature_names = [f["feature"] for f in features]
        assert "glucose" not in feature_names
        assert "HbA1c" not in feature_names
        assert "abdominal_pain" in feature_names or "nausea" in feature_names or "vomiting" in feature_names

        # Present GI symptoms must be the primary drivers
        top_feature = features[0]["feature"]
        assert top_feature in ["abdominal_pain", "nausea", "vomiting"]

    def test_calibrate_flat_differentials_and_clarification_prompt(self):
        """Verify ambiguous GI cases produce separated differentials and trigger clarification prompt."""
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "symptoms": ["nausea", "vomiting", "abdominal pain"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        # Check differentials are not tied at flat 20%
        diffs = data["differential_diagnoses"]
        probs = [d["probability"] for d in diffs]
        assert len(set(probs)) > 1  # Not all identical
        assert probs[0] > probs[1]  # Strictly descending
        assert abs(sum(probs) - 1.0) < 0.001

        # Check clarification prompt
        cp = data.get("clarification_prompt")
        assert cp is not None
        assert "Where is the pain located: upper or lower abdomen?" in cp["question"]
        assert len(cp["options"]) >= 3

    def test_red_flag_emergency_guardrail_alerts(self):
        """Verify acute chest pain, dyspnea, or neurological deficits trigger red-flag emergency alert."""
        self.client.force_authenticate(user=self.patient_a)

        # 1. Chest pain
        payload_chest = {"symptoms": ["chest pain", "sweating"]}
        res_chest = self.client.post("/api/v1/predictions/disease/", payload_chest, format="json")
        assert res_chest.status_code == status.HTTP_201_CREATED
        data_chest = res_chest.json()
        assert data_chest["risk_level"] == "HIGH"
        assert "Warning: Selected symptoms include acute chest discomfort." in data_chest["red_flag_alert"]

        # 2. Shortness of breath
        payload_dyspnea = {"symptoms": ["shortness of breath", "cough"]}
        res_dyspnea = self.client.post("/api/v1/predictions/disease/", payload_dyspnea, format="json")
        assert res_dyspnea.status_code == status.HTTP_201_CREATED
        data_dyspnea = res_dyspnea.json()
        assert data_dyspnea["risk_level"] == "HIGH"
        assert "Warning: Selected symptoms include acute shortness of breath / dyspnea." in data_dyspnea["red_flag_alert"]

    def test_free_text_malarial_symptom_extraction_and_alignment(self):
        """
        Verify conversational symptoms map to training features and trigger Malaria:
        - "shivering chills" -> chills/rigors
        - "high cyclical fever" -> fever
        - "profuse sweating" -> excessive_sweating/sweating
        - "throbbing headache" -> headache
        - "muscle pain" -> myalgia/body_aches
        """
        self.client.force_authenticate(user=self.patient_a)
        query = (
            "High cyclical fever with severe shivering chills every other day, "
            "profuse sweating, throbbing headache, muscle pain, and extreme nausea"
        )
        payload = {"symptoms": [query]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        assert data["predicted_condition"] == "Malaria"
        # Confirm symptoms are mapped
        canon = data["canonical_symptoms"]
        assert "fever" in canon
        assert "chills" in canon
        assert "headache" in canon
        assert "nausea" in canon
        assert "myalgia" in canon or "body_aches" in canon
        assert "excessive_sweating" in canon or "sweating" in canon

        # Confirm Dyspnea triage banner did NOT trigger
        assert data.get("red_flag_alert") is None

    def test_chronic_ehr_labs_do_not_hijack_acute_infectious_queries(self):
        """
        Verify background chronic EHR labs (Fasting Glucose 168, HbA1c 8.4)
        do not hijack an acute presentation into a Type 2 Diabetes classification.
        """
        from apps.medical_records.models import LabReport, LabResult

        # Create background diabetic lab results in EHR for patient_a
        report = LabReport.objects.create(
            patient=self.patient_a,
            title="Comprehensive Metabolic Panel",
        )
        LabResult.objects.create(
            report=report,
            test_name="Fasting Glucose",
            value="168",
            unit="mg/dL",
            reference_range="70-99",
            flag="high",
        )
        LabResult.objects.create(
            report=report,
            test_name="HbA1c",
            value="8.4",
            unit="%",
            reference_range="< 5.7",
            flag="high",
        )

        self.client.force_authenticate(user=self.patient_a)
        query = (
            "High cyclical fever with severe shivering chills every other day, "
            "profuse sweating, throbbing headache, muscle pain, and extreme nausea"
        )
        payload = {"symptoms": [query]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        # Must NOT be Type 2 Diabetes
        assert data["predicted_condition"] != "Type 2 Diabetes"
        assert data["predicted_condition"] == "Malaria"

    def test_symptom_free_vector_with_background_ehr_labs_returns_validation_guardrail(self):
        """
        Guardrail rule 1: If extracted symptom features from user text is 0,
        DO NOT fall back to predicting chronic metabolic diseases based on background lab values.
        Must return explicit validation status.
        """
        from apps.medical_records.models import LabReport, LabResult

        # Add background diabetic labs
        report = LabReport.objects.create(
            patient=self.patient_a,
            title="Metabolic Profile",
        )
        LabResult.objects.create(
            report=report,
            test_name="Fasting Glucose",
            value="168",
            unit="mg/dL",
            flag="high",
        )
        LabResult.objects.create(
            report=report,
            test_name="HbA1c",
            value="8.4",
            unit="%",
            flag="high",
        )

        self.client.force_authenticate(user=self.patient_a)
        # Text with 0 recognized symptoms
        payload = {"symptoms": ["feeling completely normal today just testing the interface with no medical symptoms"]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        # Must NOT predict Type 2 Diabetes
        assert data["predicted_condition"] != "Type 2 Diabetes"
        assert "Diabetes" not in data["predicted_condition"]
        assert data["predicted_condition"] == "Undifferentiated / Unmapped Symptoms"

        # Explicit validation status returned
        expected_status = (
            "Unable to map entered text to recognized clinical symptom features. "
            "Please use specific symptom terms or select from common quick-add tags."
        )
        assert data.get("validation_status") == expected_status
        assert data.get("confidence") == 0.0

    def test_normalize_model_class_suffixes(self):
        """
        Verify all target disease class labels have taxonomy suffixes stripped
        (e.g., regex ' of [A-Za-z]+$' stripped) across predictions, differentials, and ranked diagnoses.
        """
        self.client.force_authenticate(user=self.patient_a)
        payload = {"symptoms": ["cough", "fever", "chest tightness"]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        suffix_regex = re.compile(r"\s+of\s+[A-Za-z\s]+$", re.IGNORECASE)

        # Main predicted condition
        assert not suffix_regex.search(data["predicted_condition"])

        # Differential diagnoses
        for item in data.get("differential_diagnoses", []):
            name = item.get("name") or item.get("condition")
            assert not suffix_regex.search(name)

        # Explanation ranked diagnoses
        ranked = data.get("explanation", {}).get("ranked_diagnoses", [])
        for item in ranked:
            name = item.get("condition") or item.get("name")
            assert not suffix_regex.search(name)

    def test_expanded_tokenizer_dermatology_psoriasis(self):
        """
        Verify Dermatology mappings:
        silvery white scales, red patches, flaking, pitted nails -> scaly_rash, skin_peeling, itching
        Predicts Psoriasis / Plaque Psoriasis, not Type 2 Diabetes.
        """
        self.client.force_authenticate(user=self.patient_a)
        query = "silvery white scales, red patches, flaking, pitted nails"
        payload = {"symptoms": [query]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        assert data["predicted_condition"] != "Type 2 Diabetes"
        assert any(p in data["predicted_condition"] for p in ["Psoriasis", "Plaque Psoriasis"])
        canon = data["canonical_symptoms"]
        assert any(s in canon for s in ["scaly_rash", "skin_peeling", "itching", "skin_rash"])

    def test_expanded_tokenizer_neurological_bells_palsy(self):
        """
        Verify Neurological mappings:
        facial drooping, unable to close eye, mouth drooping, dribbling food -> facial_palsy, cranial_nerve_deficit
        Predicts Bell's Palsy, not Type 2 Diabetes.
        """
        self.client.force_authenticate(user=self.patient_a)
        query = "facial drooping, unable to close eye, mouth drooping, dribbling food"
        payload = {"symptoms": [query]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        assert data["predicted_condition"] != "Type 2 Diabetes"
        assert "Bell's Palsy" in data["predicted_condition"]
        canon = data["canonical_symptoms"]
        assert any(s in canon for s in ["facial_palsy", "cranial_nerve_deficit", "facial_droop"])

    def test_expanded_tokenizer_musculoskeletal_acute_gout(self):
        """
        Verify Musculoskeletal mappings:
        big toe pain, joint burning hot, extreme sensitivity to touch -> podagra, joint_swelling
        Predicts Acute Gout.
        """
        self.client.force_authenticate(user=self.patient_a)
        query = "big toe pain, joint burning hot, extreme sensitivity to touch"
        payload = {"symptoms": [query]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        assert data["predicted_condition"] != "Type 2 Diabetes"
        assert any(g in data["predicted_condition"] for g in ["Acute Gout", "Gout"])
        canon = data["canonical_symptoms"]
        assert any(s in canon for s in ["podagra", "joint_swelling", "joint_pain", "erythema"])

    def test_expanded_tokenizer_abdominal_appendicitis_and_cardiac_exclusion(self):
        """
        Verify Abdominal mappings:
        lower right abdomen, belly button pain radiating to right, rebound tenderness -> acute_appendicitis
        Strongly activates acute_appendicitis and prevents cross-mapping to thoracic/cardiac classes (like Acute Pericarditis).
        """
        self.client.force_authenticate(user=self.patient_a)
        query = "lower right abdomen, belly button pain radiating to right, rebound tenderness"
        payload = {"symptoms": [query]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        assert "Appendicitis" in data["predicted_condition"]
        canon = data["canonical_symptoms"]
        assert any(s in canon for s in ["acute_appendicitis", "rebound_tenderness", "abdominal_pain", "right_lower_quadrant_pain"])

        # Cardiac conditions like Acute Pericarditis must NEVER appear in predicted condition or differentials
        assert "Pericarditis" not in data["predicted_condition"]
        assert "Angina" not in data["predicted_condition"]
        for diff in data.get("differential_diagnoses", []):
            name = diff.get("name", "")
            assert "Pericarditis" not in name
            assert "Angina" not in name

    def test_dynamic_lab_gating_decouples_unrelated_specialties(self):
        """
        Verify Dynamic Lab Gating:
        EHR background labs (Glucose 180, HbA1c 8.9, Creatinine 2.4) are gated out
        for non-metabolic specialties (Dermatology, Respiratory, Infectious)
        and only merged if symptoms include metabolic/endocrine indicators.
        """
        from apps.medical_records.models import LabReport, LabResult

        # Add background chronic metabolic & renal labs
        report = LabReport.objects.create(
            patient=self.patient_a,
            title="Chronic Metabolic & Renal Panel",
        )
        LabResult.objects.create(
            report=report,
            test_name="Fasting Blood Glucose",
            value="180",
            unit="mg/dL",
            flag="high",
        )
        LabResult.objects.create(
            report=report,
            test_name="HbA1c",
            value="8.9",
            unit="%",
            flag="high",
        )
        LabResult.objects.create(
            report=report,
            test_name="Serum Creatinine",
            value="2.4",
            unit="mg/dL",
            flag="high",
        )

        self.client.force_authenticate(user=self.patient_a)

        # 1. Dermatology presentation: should NOT inject metabolic or renal labs
        payload_derm = {"symptoms": ["silvery white scales, red patches, flaking, pitted nails"]}
        res_derm = self.client.post("/api/v1/predictions/disease/", payload_derm, format="json")
        assert res_derm.status_code == status.HTTP_201_CREATED
        data_derm = res_derm.json()

        assert "Diabetes" not in data_derm["predicted_condition"]
        assert "Kidney" not in data_derm["predicted_condition"]
        assert any(p in data_derm["predicted_condition"] for p in ["Psoriasis", "Plaque Psoriasis"])

        # Check extracted vitals do not contain gated background labs
        ext_vitals_derm = data_derm.get("extracted_vitals", {})
        assert "glucose" not in ext_vitals_derm
        assert "creatinine" not in ext_vitals_derm

        # Check SHAP features do not contain gated labs
        derm_features = [f["feature"] for f in data_derm["explanation"]["features"]]
        assert "glucose" not in derm_features
        assert "HbA1c" not in derm_features
        assert "creatinine" not in derm_features

        # 2. Metabolic presentation: SHOULD inject metabolic labs
        payload_metabolic = {"symptoms": ["polyuria", "polydipsia", "unexplained weight loss", "fatigue"]}
        res_meta = self.client.post("/api/v1/predictions/disease/", payload_metabolic, format="json")
        assert res_meta.status_code == status.HTTP_201_CREATED
        data_meta = res_meta.json()

        # Metabolic presentation merged the background glucose/hba1c labs
        ext_vitals_meta = data_meta.get("extracted_vitals", {})
        assert "glucose" in ext_vitals_meta
        assert ext_vitals_meta["glucose"] == 180.0
        assert "Diabetes" in data_meta["predicted_condition"]

    def test_fallback_structured_semantic_extraction_json_schema(self):
        """
        Verify Fallback to Structured Semantic Extraction:
        - Validates JSON schema against 154 CANONICAL_SYMPTOMS vocabulary
        - Rejects invalid schemas
        - Conversational narrative with < 2 regex matches falls back to structured semantic extraction
        """
        from ai.nlp_service import validate_symptom_extraction_schema, extract_symptoms_via_llm_fallback
        from ai.preprocessing import get_preprocessor_v2

        # 1. Test JSON Schema Validation
        allowed_keys = {"polyuria", "polydipsia", "fever", "cough", "abdominal_pain"}
        valid_payload = {"symptoms": ["polyuria", "polydipsia", "unknown_fake_token"]}
        validated = validate_symptom_extraction_schema(valid_payload, allowed_keys)
        assert validated == ["polyuria", "polydipsia"]

        # Missing required 'symptoms' field raises ValueError
        try:
            validate_symptom_extraction_schema({"wrong_key": ["polyuria"]}, allowed_keys)
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "Missing required schema field 'symptoms'" in str(exc)

        # Non-dict payload raises ValueError
        try:
            validate_symptom_extraction_schema(["polyuria"], allowed_keys)
            assert False, "Should have raised ValueError"
        except ValueError as exc:
            assert "Root JSON payload must be an object/dict" in str(exc)

        # 2. Test Conversational Extraction Fallback
        conversational_text = "I have been peeing constantly all night and drinking water all day"
        fallback_res = extract_symptoms_via_llm_fallback(conversational_text)
        assert "polyuria" in fallback_res
        assert "polydipsia" in fallback_res

        # 3. Verify Preprocessor invokes extraction fallback
        prep = get_preprocessor_v2()
        parsed = prep.parse_symptoms(conversational_text)
        assert "polyuria" in parsed["canonical_symptoms"]
        assert "polydipsia" in parsed["canonical_symptoms"]

    def test_low_confidence_ood_triage_shield(self):
        """
        Verify Low-Confidence / OOD Triage Shield in engine.py:
        If top disease probability after softmax calibration is below 40% (max_proba < 0.40):
        - Status is set to "inconclusive_broad_presentation"
        - Predicted condition displays the top 3 potential specialties (e.g. Inconclusive: SpecA / SpecB / SpecC)
        - Generates 2-3 relevant clarifying clinical follow-up questions
        """
        self.client.force_authenticate(user=self.patient_a)

        # Ambiguous presentation with low confidence (< 40%)
        payload = {"symptoms": ["insomnia"]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        # Calibrated top probability must be below 40%
        assert data["confidence"] < 0.40

        # Status must be set to "inconclusive_broad_presentation"
        assert data.get("status") == "inconclusive_broad_presentation"
        assert data.get("triage_status") == "inconclusive_broad_presentation"
        assert data["explanation"].get("status") == "inconclusive_broad_presentation"

        # Displays top 3 potential specialties rather than forcing a low-confidence disease name
        assert data["predicted_condition"].startswith("Inconclusive:")
        top_specs = data.get("top_specialties") or data.get("potential_specialties")
        assert top_specs is not None
        assert len(top_specs) >= 2
        for spec in top_specs:
            assert spec in data["predicted_condition"]

        # Generates 2-3 relevant clarifying clinical follow-up questions
        clarifying_qs = data.get("clarifying_questions")
        assert clarifying_qs is not None
        assert 2 <= len(clarifying_qs) <= 3
        for q_item in clarifying_qs:
            assert "question" in q_item
            assert "specialty" in q_item
            assert "options" in q_item
            assert len(q_item["options"]) >= 2

        # Clarification prompt structure
        cp = data.get("clarification_prompt")
        assert cp is not None
        assert cp.get("status") == "inconclusive_broad_presentation"
        assert len(cp.get("questions", [])) >= 2
        assert len(cp.get("options", [])) >= 2

    def test_exhaustive_100_disease_hallmark_token_bridges_and_calibration(self):
        """
        Verify Exhaustive 100-Disease Pathognomonic Token Bridge & KB Coherence Calibration:
        - Confirms zero unmapped drop-offs across colloquial hallmark phrases
        - Confirms zero inconclusive false-trips (status == 'conclusive', confidence >= 0.40)
        - Confirms pathognomonic conditions correctly matched across all 10 clinical specialties
        """
        self.client.force_authenticate(user=self.patient_a)

        specialty_hallmark_cases = [
            # Category 1: Infectious
            ("Dengue Fever", "retro-orbital pain, breakbone fever, petechial rash"),
            ("Cholera", "rice-water stool, profuse watery diarrhea without blood, severe rapid dehydration"),
            ("Pulmonary Tuberculosis", "chronic cough over 3 weeks, drenching night sweats, hemoptysis, unintentional weight loss"),

            # Category 2: Cardiovascular
            ("Acute Myocardial Infarction", "crushing substernal chest pressure, radiating to left arm/jaw, cold diaphoresis"),
            ("Congestive Heart Failure", "waking up gasping at night, orthopnea needing pillows, bilateral pitting ankle edema"),

            # Category 3: Respiratory
            ("Croup", "barking seal-like cough, inspiratory stridor, hoarseness in child"),
            ("Pulmonary Embolism", "sudden pleuritic chest pain, rapid breathing, coughing blood, recent long flight/immobility"),

            # Category 4: GI
            ("Gastroesophageal Reflux Disease", "heartburn behind breastbone, acid sour regurgitation, water brash"),
            ("Peptic Ulcer Disease", "burning epigastric gnawing pain relieved by food or antacids, dark tarry stools"),

            # Category 5: Neurological
            ("Migraine", "unilateral throbbing pulsating head pain, visual zigzag aura, photophobia, phonophobia"),
            ("Bell's Palsy", "inability to close eye, forehead not wrinkling, mouth drooping with food dribbling, hyperacusis"),

            # Category 6: Endocrine
            ("Type 1 Diabetes", "extreme unquenchable thirst, peeing constantly through night, rapid weight loss despite eating, fruity breath"),
            ("Acute Gout", "excruciating big toe metatarsophalangeal pain, podagra, joint burning hot red and swollen"),

            # Category 7: Renal
            ("Acute Cystitis", "burning pain during urination, frequent small-volume peeing, suprapubic cramping without fever"),
            ("Acute Pyelonephritis", "flank costovertebral angle pain, shivering rigors, high fever, painful cloudy urine"),

            # Category 8: Rheumatology
            ("Rheumatoid Arthritis", "symmetric swelling and morning stiffness in finger joints lasting >1 hour, boggy PIP/MCP joints"),
            ("Ankylosing Spondylitis", "chronic lower back and buttock stiffness waking at night, relieved by exercise not rest, bamboo spine"),

            # Category 9: Dermatology
            ("Plaque Psoriasis", "well-demarcated salmon pink plaques covered with silvery micaceous scales on elbows/knees, pitted nails"),
            ("Herpes Zoster", "unilateral dermatomal band of grouped painful fluid-filled vesicles, stabbing burning nerve pain preceding rash"),

            # Category 10: ENT & Ophthalmology
            ("Acute Angle-Closure Glaucoma", "severe unilateral eye and frontal headache, colored halos around lights, hazy cornea with fixed mid-dilated pupil, nausea"),
            ("Ménière's Disease", "triad of episodic true vertigo, fluctuating low-frequency hearing loss, and roaring tinnitus / aural fullness"),
        ]

        for expected_disease, query_text in specialty_hallmark_cases:
            res = self.client.post("/api/v1/predictions/disease/", {"symptoms": [query_text]}, format="json")
            assert res.status_code == status.HTTP_201_CREATED, f"Failed for {expected_disease}: {res.content}"
            data = res.json()

            pred_name = data.get("predicted_condition", "")
            triage_stat = data.get("status", "")
            conf = data.get("confidence", 0.0)
            primary_diff = data.get("primary_differentials", [{}])[0].get("condition", "")

            # 1. Zero inconclusive false-trips
            assert triage_stat == "conclusive", f"Expected conclusive for {expected_disease}, got status={triage_stat}"
            assert conf >= 0.40, f"Expected confidence >= 0.40 for {expected_disease}, got {conf}"

            # 2. Predicted condition or top differential matches target disease
            matched = (
                expected_disease.lower() in pred_name.lower()
                or pred_name.lower() in expected_disease.lower()
                or expected_disease.lower() in primary_diff.lower()
                or primary_diff.lower() in expected_disease.lower()
            )
            assert matched, f"Expected condition '{expected_disease}', got '{pred_name}' (top diff: '{primary_diff}')"

    def test_localized_abdominal_exam_phrases_map_to_abdominal_pain(self):
        """
        Verify localized abdominal exam phrases explicitly toggle abdominal_pain = 1.0:
        - 'periumbilical pain' -> abdominal_pain = 1.0
        - 'right lower quadrant pain' / 'rlq pain' -> abdominal_pain = 1.0
        - 'mcburney tenderness' / 'mcburney's point' -> abdominal_pain = 1.0
        - 'rebound tenderness' -> abdominal_pain = 1.0
        - 'stomach cramping' / 'belly pain' -> abdominal_pain = 1.0
        Allows Acute Appendicitis to predict with high confidence.
        """
        from ai.preprocessing import get_preprocessor_v2
        prep = get_preprocessor_v2()

        exam_phrases = [
            "periumbilical pain",
            "right lower quadrant pain",
            "rlq pain",
            "mcburney tenderness",
            "mcburney's point",
            "mcburney point",
            "rebound tenderness",
            "stomach cramping",
            "belly pain",
        ]

        # Verify each phrase explicitly toggles abdominal_pain = 1.0 in the feature vector
        for phrase in exam_phrases:
            res = prep.preprocess([phrase])
            assert res.raw_dict.get("abdominal_pain") == 1.0, f"Failed raw vector for {phrase}"
            assert res.imputed_dict.get("abdominal_pain") == 1.0, f"Failed imputed vector for {phrase}"
            parsed = prep.parse_symptoms([phrase])
            assert "abdominal_pain" in parsed["canonical_symptoms"], f"abdominal_pain missing from canonical for {phrase}"

        # Verify Acute Appendicitis prediction with high confidence
        self.client.force_authenticate(user=self.patient_a)
        res_app = self.client.post(
            "/api/v1/predictions/disease/",
            {"symptoms": ["right lower quadrant pain", "mcburney's point", "fever"]},
            format="json",
        )
        assert res_app.status_code == status.HTTP_201_CREATED
        data = res_app.json()
        assert "Appendicitis" in data["predicted_condition"]
        assert data["confidence"] >= 0.70
        assert data["status"] == "conclusive"
        assert res_app.data["canonical_symptoms"]
        assert "abdominal_pain" in res_app.data["canonical_symptoms"]

    def test_migrating_periumbilical_pain_predicts_acute_appendicitis(self):
        """
        Verify exact natural language clinical presentation:
        'Periumbilical pain migrating to the right lower quadrant, mcburney tenderness, rebound tenderness, nausea, low-grade fever, and loss of appetite.'
        - Ensures 'migrating' does not fuzzy-match to 'migraine' (headache = 0.0, photophobia = 0.0).
        - Ensures abdominal_pain evaluates to 1.0.
        - Predicts Acute Appendicitis with conclusive status and high confidence (>= 0.70).
        """
        from ai.preprocessing import get_preprocessor_v2
        prep = get_preprocessor_v2()

        input_text = "Periumbilical pain migrating to the right lower quadrant, mcburney tenderness, rebound tenderness, nausea, low-grade fever, and loss of appetite."
        parsed = prep.parse_symptoms(input_text)
        canonical = parsed["canonical_symptoms"]

        # Abdominal pain must be extracted
        assert "abdominal_pain" in canonical
        # Unexpected tokens (from migraine fuzzy match) must NOT be extracted
        assert "headache" not in canonical
        assert "photophobia" not in canonical
        assert "visual_aura" not in canonical

        # Preprocessed vector values
        preprocessed = prep.preprocess(input_text)
        assert preprocessed.raw_dict.get("abdominal_pain") == 1.0
        assert preprocessed.imputed_dict.get("abdominal_pain") == 1.0
        assert preprocessed.raw_dict.get("headache", 0.0) == 0.0
        assert preprocessed.raw_dict.get("photophobia", 0.0) == 0.0
        assert preprocessed.raw_dict.get("nausea") == 1.0
        assert preprocessed.raw_dict.get("anorexia") == 1.0

        # E2E Disease Prediction via API
        self.client.force_authenticate(user=self.patient_a)
        res = self.client.post(
            "/api/v1/predictions/disease/",
            {"symptoms": input_text},
            format="json",
        )
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["predicted_condition"] == "Acute Appendicitis"
        assert data["confidence"] >= 0.70
        assert data["status"] == "conclusive"

