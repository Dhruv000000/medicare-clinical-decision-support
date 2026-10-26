import os
import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.assistant.services.llm_provider import (
    GeminiProvider,
    OpenAIProvider,
    GroundedExtractiveProvider,
    get_llm_provider,
    build_grounded_clinical_prompt,
)
from ai.explanation_service import generate_clinical_explanation
from ai.ai_chat_service import chat_with_clinical_ai
from ai.literature_service import search_medical_literature


@pytest.mark.django_db
class TestClinicalExplanationAndChatbot:
    """
    Test suite verifying live API key handling, model prediction grounding,
    system prompt compliance, and exact error propagation without canned fallbacks.
    """

    @pytest.fixture(autouse=True)
    def setup_users(self):
        self.patient = User.objects.create_user(
            email="patient.test@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Jane",
            last_name="Doe",
        )
        self.client = APIClient()

    # -------------------------------------------------------------------------
    # 1. LIVE API KEY INITIALIZATION & PROVIDER FACTORY
    # -------------------------------------------------------------------------

    def test_gemini_provider_live_key_init(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_123")
        provider = GeminiProvider()
        assert provider.api_key == "test_gemini_key_123"
        assert provider.is_configured is True

    def test_openai_provider_live_key_init(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key_456")
        provider = OpenAIProvider()
        assert provider.api_key == "test_openai_key_456"
        assert provider.is_configured is True

    def test_get_llm_provider_resolves_gemini(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_xyz")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        provider = get_llm_provider()
        assert isinstance(provider, GeminiProvider)

    def test_get_llm_provider_resolves_openai(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key_abc")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        provider = get_llm_provider()
        assert isinstance(provider, OpenAIProvider)

    # -------------------------------------------------------------------------
    # 2. SYSTEM PROMPT & PREDICTION GROUNDING
    # -------------------------------------------------------------------------

    def test_build_grounded_clinical_prompt_exact_template(self):
        sys_prompt, user_content = build_grounded_clinical_prompt(
            prompt="Explain my clinical results.",
            user_symptoms_text="Severe right lower quadrant pain and fever",
            top_predicted_disease="Acute Appendicitis",
            confidence=94.5,
            shap_drivers=["abdominal_pain", "fever", "rebound_tenderness"],
        )

        # 3-tier clinical response instructions
        assert "You are an expert clinical decision support assistant in MediCare." in sys_prompt
        assert "The patient described: Severe right lower quadrant pain and fever" in sys_prompt
        assert "The diagnostic model identified: Acute Appendicitis (94.5% confidence)." in sys_prompt
        assert "1. Primary Clinical Impression: Directly explain why the symptoms and history point toward Acute Appendicitis." in sys_prompt
        assert "2. Key Red Flags & Next Steps: Highlight specific urgent clinical signs to watch for and recommended clinical workup/tests for this specific condition." in sys_prompt
        assert "3. Provide a clear, actionable explanation rather than vague generic advice." in sys_prompt

        # User active context
        assert "User's exact complaint: Severe right lower quadrant pain and fever" in user_content
        assert "Model's predicted disease: Acute Appendicitis" in user_content
        assert "Model confidence & SHAP drivers: 94.5%, abdominal pain, fever, rebound tenderness" in user_content

    # -------------------------------------------------------------------------
    # 3. NO HARDCODED MOCK LITERATURE FALLBACKS (NO UNDERSEA HYPERB MED)
    # -------------------------------------------------------------------------

    def test_no_fake_undersea_hyperb_med_canned_text(self):
        citations = [
            {
                "pmid": "999999",
                "title": "Randomized Trial on Appendectomy Outcomes",
                "journal": "Undersea Hyperb Med",
                "year": "2024",
                "abstract": "Standard laparoscopy shows accelerated recovery.",
            }
        ]
        provider = GroundedExtractiveProvider()
        res = provider.generate_response(
            prompt="What are next steps for appendicitis?",
            citations=citations,
            top_predicted_disease="Acute Appendicitis",
            confidence=92.0,
            user_symptoms_text="right lower quadrant pain",
        )
        assert "Undersea Hyperb Med confirmed that evidence-based medical therapies and proactive health monitoring are the most effective foundation" not in res["response"]

    # -------------------------------------------------------------------------
    # 4. ERROR RAISING & LOGGING ON INVALID KEY OR API FAILURE
    # -------------------------------------------------------------------------

    def test_gemini_provider_unconfigured_raises_value_error(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)

        provider = GeminiProvider(api_key="")
        with pytest.raises(ValueError) as excinfo:
            provider.generate_response(
                prompt="Explain diagnosis",
                citations=[],
                user_symptoms_text="chest pain",
                top_predicted_disease="Angina Pectoris",
                confidence=88.0,
            )
        assert "Gemini API key is unconfigured" in str(excinfo.value)

    @patch("requests.post")
    def test_gemini_provider_api_error_raises_runtime_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = '{"error": {"code": 400, "message": "API_KEY_INVALID", "status": "INVALID_ARGUMENT"}}'
        mock_post.return_value = mock_resp

        provider = GeminiProvider(api_key="bad_invalid_key")
        with pytest.raises(RuntimeError) as excinfo:
            provider.generate_response(
                prompt="Explain diagnosis",
                citations=[],
                user_symptoms_text="severe migraine",
                top_predicted_disease="Migraine",
                confidence=91.0,
            )
        assert "Gemini API call failed with status 400" in str(excinfo.value)
        assert "API_KEY_INVALID" in str(excinfo.value)

    def test_openai_provider_unconfigured_raises_value_error(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)

        provider = OpenAIProvider(api_key="")
        with pytest.raises(ValueError) as excinfo:
            provider.generate_response(
                prompt="Explain diagnosis",
                citations=[],
                user_symptoms_text="polyuria polydipsia",
                top_predicted_disease="Diabetes Mellitus Type 2",
                confidence=96.0,
            )
        assert "OpenAI API key is unconfigured" in str(excinfo.value)

    @patch("requests.post")
    def test_openai_provider_api_error_raises_runtime_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = '{"error": {"message": "Incorrect API key provided", "type": "invalid_request_error"}}'
        mock_post.return_value = mock_resp

        provider = OpenAIProvider(api_key="sk-invalid-fake-key")
        with pytest.raises(RuntimeError) as excinfo:
            provider.generate_response(
                prompt="Explain diagnosis",
                citations=[],
                user_symptoms_text="cough and dyspnea",
                top_predicted_disease="Asthma",
                confidence=89.0,
            )
        assert "OpenAI API call failed with status 401" in str(excinfo.value)
        assert "Incorrect API key provided" in str(excinfo.value)

    # -------------------------------------------------------------------------
    # 5. ENDPOINT /api/v1/assistant/chat/ RETURNS 502 ON LLM FAILURE
    # -------------------------------------------------------------------------

    @patch("apps.assistant.services.llm_provider.requests.post")
    def test_chat_endpoint_returns_502_on_live_llm_failure(self, mock_post, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "invalid_key_triggering_error")
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = '{"error": {"message": "PERMISSION_DENIED: API key not valid"}}'
        mock_post.return_value = mock_resp

        self.client.force_authenticate(user=self.patient)
        payload = {
            "prompt": "Can you explain the clinical impression and diagnostic tests for this condition?",
            "user_symptoms_text": "RLQ pain, fever",
            "top_predicted_disease": "Acute Appendicitis",
            "confidence": 93.0,
            "shap_drivers": ["abdominal_pain", "fever"],
        }
        res = self.client.post("/api/v1/assistant/chat/", payload, format="json")
        assert res.status_code == status.HTTP_502_BAD_GATEWAY
        data = res.json()
        assert data["error"]["code"] == "LLM_PROVIDER_ERROR"
        assert "Gemini API call failed with status 403" in data["error"]["message"]
