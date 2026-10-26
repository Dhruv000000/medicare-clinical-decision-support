# ==============================================================================
# FILE: backend/tests/test_gemini_integration.py
# PURPOSE: Automated test suite for Gemini API integration, independent emergency
#          triage, multi-turn freshness, rate-limit/timeout handling, and PubMed accuracy.
# ==============================================================================

import os
import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from apps.accounts.models import User
from apps.assistant.models import ChatConversation, ChatMessage
from apps.assistant.services.rag_engine import rag_assistant_engine, RAGAssistantEngine
from apps.assistant.services.llm_provider import GeminiProvider, get_llm_provider


@pytest.mark.django_db
class TestGeminiIntegrationAndSafety:
    """
    Test suite fulfilling all 10 requirements:
    1. Stroke emergency guidance (slurred speech, unilateral weakness, arm weakness).
    2. Cardiac emergency guidance (chest pressure, breathlessness, sweating).
    3. Leptospirosis input not reused for Allergic Rhinitis input.
    4. Fresh message triggers fresh inference.
    5. Invalid API key produces safe, useful error.
    6. Gemini rate limits and timeouts handled without returning stale results.
    7. Invalid model output rejected or safely handled.
    8. Irrelevant PubMed references not displayed for stroke or non-matching queries.
    9. Missing confidence scores are not fabricated.
    10. Regression and endpoint contracts verified.
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        cache.clear()
        self.patient_user = User.objects.create_user(
            email="patient.gemini.test@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Jane",
            last_name="Doe",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.patient_user)

    # -------------------------------------------------------------------------
    # 1. STROKE EMERGENCY TRIAGE
    # -------------------------------------------------------------------------
    def test_stroke_emergency_guidance(self):
        """
        1. Sudden slurred speech, unilateral facial weakness, and arm weakness
        trigger immediate stroke emergency guidance advising calling emergency
        services, recording time of onset/last known well, and not driving oneself.
        """
        prompt = "Sudden slurred speech, unilateral facial weakness, and arm weakness"
        result = rag_assistant_engine.process_chat(
            user=self.patient_user,
            prompt=prompt,
        )

        assert result["is_emergency"] is True
        assert result["emergency_triage"]["is_emergency"] is True
        assert "stroke_symptoms" in result["emergency_triage"]["categories"]
        assert result["urgency_level"] == "CRITICAL_EMERGENCY"

        response_text = result["response"].lower()
        # Advice to call emergency services
        assert "call emergency services immediately" in response_text or "911" in response_text or "112" in response_text
        # Record time of onset / last known well
        assert "time of onset" in response_text or "last known well" in response_text
        # Advise not driving themselves
        assert "do not drive" in response_text or "do not attempt to drive" in response_text
        # Advise not waiting for symptoms to resolve
        assert "do not wait" in response_text

        # Emergency guidance triggered independently of classifier or PubMed
        assert result["citations"] == []
        assert result["literature_references"] == []
        assert result["predicted_condition"] is None
        assert result["confidence"] is None

    def test_stroke_emergency_natural_language_presentation(self):
        """
        Verifies naturalistic acute stroke narrative:
        'I was talking normally a few minutes ago when my speech suddenly became slurred.
        The right side of my face feels weak, and I cannot lift my right arm properly.
        I feel confused, and these symptoms started very suddenly.'
        triggers independent red-flag emergency triage immediately.
        """
        prompt = (
            "I was talking normally a few minutes ago when my speech suddenly became slurred. "
            "The right side of my face feels weak, and I cannot lift my right arm properly. "
            "I feel confused, and these symptoms started very suddenly."
        )
        result = rag_assistant_engine.process_chat(
            user=self.patient_user,
            prompt=prompt,
        )

        assert result["is_emergency"] is True
        assert result["emergency_triage"]["is_emergency"] is True
        assert "stroke_symptoms" in result["emergency_triage"]["categories"]
        assert result["urgency_level"] == "CRITICAL_EMERGENCY"
        assert result["citations"] == []
        assert result["predicted_condition"] is None
        assert result["confidence"] is None

        resp_text = result["response"].lower()
        assert "call emergency services" in resp_text or "911" in resp_text or "112" in resp_text
        assert "time of onset" in resp_text or "last known well" in resp_text
        assert "do not drive" in resp_text

    # -------------------------------------------------------------------------
    # 2. CARDIAC EMERGENCY TRIAGE
    # -------------------------------------------------------------------------
    def test_cardiac_emergency_guidance(self):
        """
        2. Severe chest pressure with breathlessness and sweating triggers
        cardiac emergency guidance.
        """
        prompt = "Severe chest pressure with breathlessness and sweating"
        result = rag_assistant_engine.process_chat(
            user=self.patient_user,
            prompt=prompt,
        )

        assert result["is_emergency"] is True
        assert result["emergency_triage"]["is_emergency"] is True
        assert "chest_pain" in result["emergency_triage"]["categories"]
        assert result["urgency_level"] == "CRITICAL_EMERGENCY"

        response_text = result["response"].lower()
        assert "call emergency services" in response_text or "911" in response_text or "112" in response_text
        assert "do not drive" in response_text
        assert result["citations"] == []
        assert result["literature_references"] == []

    def test_reflux_heartburn_differentiated_and_passed_to_gemini(self):
        """
        Differentiates mild reflux/heartburn from acute cardiac distress:
        'mild burning sensation in my chest after eating spicy meals and lying down'
        must NOT trigger RED-FLAG EMERGENCY alert and must pass through to Gemini API.
        """
        prompt = "mild burning sensation in my chest after eating spicy meals and lying down"

        def mock_generate(*args, **kwargs):
            return {
                "response": "1. Primary Clinical Impression: Symptoms are consistent with gastroesophageal reflux (GERD) or heartburn triggered by recumbency and spicy food.",
                "provider": "gemini",
                "model": "gemini-3.5-flash",
                "grounded": True,
                "predicted_condition": "GERD",
                "confidence": "85.0%",
            }

        with patch.object(GeminiProvider, "generate_response", side_effect=mock_generate) as mock_gemini:
            result = rag_assistant_engine.process_chat(
                user=self.patient_user,
                prompt=prompt,
            )

            # Must NOT be an emergency
            assert result["is_emergency"] is False
            assert result["emergency_triage"]["is_emergency"] is False
            assert result["emergency_triage"]["status"] == "NON_EMERGENCY"
            assert result["urgency_level"] != "CRITICAL_EMERGENCY"
            assert result["urgency_level"] in ["ROUTINE", "NON_EMERGENCY", "EVALUATION_RECOMMENDED"]
            assert "emergency medical alert" not in result["response"].lower()
            # Verified pass-through to Gemini provider
            assert mock_gemini.called
            assert "reflux" in result["response"].lower() or "gerd" in result["response"].lower()

    def test_negation_aware_symptoms_suppress_emergency_triggers(self):
        """
        Negation tokens ('no', 'not', 'denies', 'without', 'negative for') within
        a 3-word window suppress red-flag emergency triggers.
        'no shortness of breath, no arm pain, and no sweating' must NOT trigger cardiac alerts.
        """
        prompt = "mild burning sensation in my chest after eating spicy meals and lying down, no shortness of breath, no arm pain, and no sweating"

        def mock_generate(*args, **kwargs):
            return {
                "response": "Clinical Impression: Non-cardiac postprandial burning consistent with acid reflux. Red flags explicitly denied.",
                "provider": "gemini",
                "model": "gemini-3.5-flash",
                "grounded": True,
                "predicted_condition": "GERD",
                "confidence": "88.0%",
            }

        with patch.object(GeminiProvider, "generate_response", side_effect=mock_generate) as mock_gemini:
            result = rag_assistant_engine.process_chat(
                user=self.patient_user,
                prompt=prompt,
            )

            assert result["is_emergency"] is False
            assert result["emergency_triage"]["is_emergency"] is False
            assert result["emergency_triage"]["status"] == "NON_EMERGENCY"
            assert mock_gemini.called

        # Also test bare negated cardiac symptoms directly through detect_emergency
        bare_negated = "no shortness of breath, no arm pain, and no sweating"
        assert rag_assistant_engine.detect_emergency(bare_negated) is None

    def test_active_high_acuity_cardiac_emergency_triggers(self):
        """
        Active (non-negated) high-acuity features (radiation, acute dyspnea, cold sweat)
        properly trigger the RED-FLAG CARDIAC emergency banner.
        """
        prompt = "Crushing chest pain radiating to left arm and jaw with cold sweating"
        result = rag_assistant_engine.process_chat(
            user=self.patient_user,
            prompt=prompt,
        )

        assert result["is_emergency"] is True
        assert result["emergency_triage"]["is_emergency"] is True
        assert "chest_pain" in result["emergency_triage"]["categories"]
        assert result["urgency_level"] == "CRITICAL_EMERGENCY"
        assert "call emergency services" in result["response"].lower() or "911" in result["response"].lower()

    # -------------------------------------------------------------------------
    # 3. LEPTOSPIROSIS NOT REUSED FOR ALLERGIC RHINITIS IN SAME CONVERSATION
    # -------------------------------------------------------------------------
    def test_leptospirosis_not_reused_for_allergic_rhinitis(self):
        """
        3. A Leptospirosis-like input followed by an Allergic Rhinitis-like input
        in the same conversation ensures the second response is based on the second input.
        """
        def mock_generate(*args, **kwargs):
            disease = kwargs.get("top_predicted_disease") or "Clinical Inquiry"
            return {
                "response": f"1. Primary Clinical Impression: The presentation points toward potential {disease}.",
                "provider": "gemini",
                "model": "gemini-3.5-flash",
                "grounded": True,
                "predicted_condition": disease,
                "confidence": kwargs.get("confidence"),
            }

        with patch.object(GeminiProvider, "generate_response", side_effect=mock_generate):
            turn1_prompt = (
                "sudden fever, severe calf muscle pain, headache, red eyes, "
                "recent floodwater exposure, weakness, and nausea"
            )
            r1 = rag_assistant_engine.process_chat(
                user=self.patient_user,
                prompt=turn1_prompt,
            )
            conv_id = r1["conversation_id"]
            assert "Leptospirosis" in r1["predicted_condition"]

            turn2_prompt = (
                "repeated sneezing, itchy nose, clear watery nasal discharge, "
                "itchy watery eyes, and dust triggers"
            )
            r2 = rag_assistant_engine.process_chat(
                user=self.patient_user,
                prompt=turn2_prompt,
                conversation_id=conv_id,
            )

            assert r2["conversation_id"] == conv_id
            assert "Allergic Rhinitis" in r2["predicted_condition"]
            assert "Leptospirosis" not in r2["predicted_condition"]
            assert "Leptospirosis" not in r2["response"]
            assert "Allergic Rhinitis" in r2["response"] or "rhinitis" in r2["response"].lower()

    # -------------------------------------------------------------------------
    # 4. FRESH MESSAGE TRIGGERS FRESH INFERENCE
    # -------------------------------------------------------------------------
    def test_fresh_message_triggers_fresh_inference(self):
        """
        4. Verifies each user message with symptoms triggers independent fresh inference.
        """
        def mock_generate(*args, **kwargs):
            disease = kwargs.get("top_predicted_disease") or "Clinical Inquiry"
            return {
                "response": f"1. Primary Clinical Impression: Evaluated {disease}.",
                "provider": "gemini",
                "model": "gemini-3.5-flash",
                "grounded": True,
                "predicted_condition": disease,
                "confidence": kwargs.get("confidence"),
            }

        with patch.object(GeminiProvider, "generate_response", side_effect=mock_generate):
            r1 = rag_assistant_engine.process_chat(
                user=self.patient_user,
                prompt="High fever, severe chills, sweating, and headache",
            )
            cond1 = r1["predicted_condition"]
            assert cond1 is not None

            r2 = rag_assistant_engine.process_chat(
                user=self.patient_user,
                prompt="Itchy rash on elbows, scaly silvery plaques, and dry skin",
                conversation_id=r1["conversation_id"],
            )
            cond2 = r2["predicted_condition"]
            assert cond2 is not None
            assert cond1 != cond2

    # -------------------------------------------------------------------------
    # 5. INVALID API KEY PRODUCES SAFE, USEFUL ERROR
    # -------------------------------------------------------------------------
    def test_invalid_api_key_produces_safe_useful_error(self, monkeypatch):
        """
        5. An invalid API key produces a safe, useful error (HTTP 502 LLM_PROVIDER_ERROR).
        """
        monkeypatch.setenv("GEMINI_API_KEY", "invalid_expired_api_key_xyz")
        monkeypatch.setenv("LLM_PROVIDER", "gemini")

        provider = GeminiProvider(api_key="invalid_key")
        # Mocking the client generate_content call to simulate API key error
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API_KEY_INVALID: The provided API key is invalid.")
        provider._client = mock_client

        with pytest.raises(RuntimeError) as exc_info:
            provider.generate_response(
                prompt="Explain diabetes management.",
                citations=[],
            )
        assert "API_KEY_INVALID" in str(exc_info.value) or "400" in str(exc_info.value)

        # Test endpoint returns 502 with code LLM_PROVIDER_ERROR
        with patch("apps.assistant.services.rag_engine.get_llm_provider", return_value=provider):
            res = self.client.post(
                "/api/v1/assistant/chat/",
                {"prompt": "Explain diabetes management."},
            )
            assert res.status_code == status.HTTP_502_BAD_GATEWAY
            assert res.data["error"]["code"] == "LLM_PROVIDER_ERROR"

    # -------------------------------------------------------------------------
    # 6. RATE LIMITS AND TIMEOUTS HANDLED WITHOUT STALE RESULTS
    # -------------------------------------------------------------------------
    def test_gemini_rate_limit_and_timeout_handled_without_stale_results(self, monkeypatch):
        """
        6. Gemini rate limits (429) and timeouts are handled without returning stale results.
        """
        provider = GeminiProvider(api_key="test_key")
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("RESOURCE_EXHAUSTED: Rate limit exceeded (code 429)")
        provider._client = mock_client

        with pytest.raises(RuntimeError) as exc_info:
            provider.generate_response(
                prompt="Explain cholesterol tests.",
                citations=[],
            )
        assert "429" in str(exc_info.value) or "RESOURCE_EXHAUSTED" in str(exc_info.value)

        # Verify endpoint returns 502, never returning a stale result
        with patch("apps.assistant.services.rag_engine.get_llm_provider", return_value=provider):
            res = self.client.post(
                "/api/v1/assistant/chat/",
                {"prompt": "Explain cholesterol tests."},
            )
            assert res.status_code == status.HTTP_502_BAD_GATEWAY
            assert res.data["error"]["code"] == "LLM_PROVIDER_ERROR"

        # Now test timeout
        mock_client.models.generate_content.side_effect = TimeoutError("Request timed out after 15.0s")
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate_response(
                prompt="Explain cholesterol tests.",
                citations=[],
            )
        assert "timed out" in str(exc_info.value).lower()

    # -------------------------------------------------------------------------
    # 7. INVALID MODEL OUTPUT SAFELY REJECTED
    # -------------------------------------------------------------------------
    def test_invalid_model_output_rejected(self):
        """
        7. Invalid or empty model output is rejected safely.
        """
        provider = GeminiProvider(api_key="test_key")
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = ""  # Empty text from model
        mock_client.models.generate_content.return_value = mock_resp
        provider._client = mock_client

        with pytest.raises(RuntimeError) as exc_info:
            provider.generate_response(
                prompt="Explain fever management.",
                citations=[],
            )
        assert "empty text part" in str(exc_info.value).lower()

    # -------------------------------------------------------------------------
    # 8. IRRELEVANT PUBMED REFERENCES NOT DISPLAYED AS EVIDENCE
    # -------------------------------------------------------------------------
    def test_irrelevant_pubmed_references_not_displayed(self):
        """
        8. Irrelevant PubMed references (e.g., depression or pericarditis for stroke)
        are never presented as supporting evidence.
        """
        stroke_prompt = "Sudden weakness on one side of my body, drooping face, and slurred speech"
        result = rag_assistant_engine.process_chat(
            user=self.patient_user,
            prompt=stroke_prompt,
        )
        assert result["is_emergency"] is True
        assert result["citations"] == []
        assert result["literature_references"] == []

        # Check that unrelated queries don't arbitrarily return canned unrelated citations
        non_matching_search = rag_assistant_engine.extract_clinical_keywords(
            prompt="something completely obscure and unknown xyz999",
            patient_context="",
            intent="MEDICAL_QUESTION",
            predicted_condition=None,
        )
        from apps.assistant.services.pubmed_service import pubmed_service
        search_res = pubmed_service.search_pubmed(non_matching_search, limit=3)
        citations = search_res.get("citations", [])
        # Should not inject random general papers
        for c in citations:
            assert "depression" not in c.get("title", "").lower()
            assert "pericarditis" not in c.get("title", "").lower()

    # -------------------------------------------------------------------------
    # 9. MISSING CONFIDENCE SCORES ARE NOT FABRICATED
    # -------------------------------------------------------------------------
    def test_missing_confidence_scores_not_fabricated(self):
        """
        9. Missing confidence scores are not fabricated (e.g. for general questions or emergency triage).
        """
        # Emergency triage inquiry
        r_emerg = rag_assistant_engine.process_chat(
            user=self.patient_user,
            prompt="Sudden severe crushing chest pain radiating to left arm",
        )
        assert r_emerg["is_emergency"] is True
        assert r_emerg["confidence"] is None

        # General navigation inquiry
        r_nav = rag_assistant_engine.process_chat(
            user=self.patient_user,
            prompt="Where can I book an appointment with a doctor?",
        )
        assert r_nav["intent"] == "APP_NAVIGATION"
        assert r_nav["confidence"] is None

    # -------------------------------------------------------------------------
    # 10. STRUCTURED SCHEMA CONTRACT VALIDATION
    # -------------------------------------------------------------------------
    def test_structured_response_contract_fields(self):
        """
        10. Verifies structured response fields:
        input_summary, emergency_triage, urgency_level, possible_conditions,
        supporting_symptoms, missing_information, recommended_next_steps,
        literature_references, disclaimer.
        """
        res = self.client.post(
            "/api/v1/assistant/chat/",
            {"prompt": "Where can I apply for an appointment with a cardiologist?"},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.data

        # Original fields preserved
        assert "conversation_id" in data
        assert "message_id" in data
        assert "response" in data
        assert "citations" in data
        assert "disclaimer" in data

        # New structured fields present
        assert "input_summary" in data
        assert "emergency_triage" in data
        assert "urgency_level" in data
        assert "possible_conditions" in data
        assert "supporting_symptoms" in data
        assert "missing_information" in data
        assert "recommended_next_steps" in data
        assert "literature_references" in data
        assert data["urgency_level"] == "ROUTINE_NAVIGATION"
        assert data["emergency_triage"]["is_emergency"] is False
