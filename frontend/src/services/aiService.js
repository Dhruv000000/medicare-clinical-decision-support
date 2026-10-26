// ==============================================================================
// FILE: frontend/src/services/aiService.js
// PURPOSE: Frontend API client service for symptom NLP parsing, ML disease prediction, TreeSHAP explainability, and PubMed RAG chat.
// VIVA EXPLANATION: This client service bridges the React frontend with backend AI microservices. It invokes symptom NLP canonicalization, calls dual-tier machine learning inference with SHAP feature attributions, and queries PubMed-grounded RAG assistant endpoints.
// ==============================================================================

import api from "./api";

export const aiService = {
  /**
   * --- 1. SYMPTOM NLP PARSER & VOCABULARY CANONICALIZATION ---
   * Sends raw user complaint (free text or array of tags) to the backend preprocessor.
   * 
   * @param {string | string[]} input - e.g. "I have a high fever and no chest pain"
   * @returns {Promise<object>} Returns { canonical_symptoms, negated_symptoms, feature_vector, suggested_symptoms, catalog }
   */
  async parseSymptoms(input) {
    const payload =
      typeof input === "string" ? { text: input } : { symptoms: input };
    const response = await api.post("/predictions/symptoms/", payload, {
      timeout: 90000,
    });
    return response.data;
  },

  /**
   * --- 2. DUAL-TIER DISEASE CLASSIFICATION & TreeSHAP EXPLAINABILITY ---
   * Invokes the primary clinical decision support inference pipeline.
   * 
   * @param {object} data - { symptoms: string[], vitals?: object, patient_id?: number }
   * @returns {Promise<object>} Returns full clinical payload:
   *   - predicted_condition: string
   *   - confidence: number (0.0 to 1.0)
   *   - triage_level / severity: string (LOW / MODERATE / HIGH / CRITICAL)
   *   - shap_analysis: { base_value, features: [{ feature, shap_value, contribution, direction }] }
   *   - differential_diagnoses / ranked_diagnoses: array of competing disease candidates
   *   - recommendation: evidence-based clinical guidance
   */
  async predictDisease(data) {
    const response = await api.post("/predictions/disease/", data, {
      timeout: 90000,
    });
    return response.data;
  },

  /**
   * --- 3. RETRIEVE HISTORICAL CLINICAL PREDICTIONS ---
   * Fetches past diagnostic consultations with role-based access filtering.
   * 
   * @returns {Promise<Array>} List of past DiseasePrediction records.
   */
  async getPredictionHistory() {
    const response = await api.get("/predictions/");
    return response.data.results || response.data;
  },

  /**
   * --- 4. RETRIEVE SYMPTOM ANALYSIS SESSIONS ---
   * Fetches historical symptom NLP checks.
   * 
   * @returns {Promise<Array>} List of past SymptomAnalysis records.
   */
  async getSymptomHistory() {
    const response = await api.get("/predictions/symptoms/");
    return response.data.results || response.data;
  },

  /**
   * --- 5. PUBMED-GROUNDED CLINICAL RAG ASSISTANT ---
   * Sends clinical query to the assistant; receives synthesized answer with PubMed PMIDs.
   * 
   * @param {object} data - { prompt: string, conversation_id?: number, patient_id?: number }
   * @returns {Promise<object>} Returns { response, citations, disclaimer, provider, grounded }
   */
  async sendChatMessage(data) {
    const response = await api.post("/assistant/chat/", data, {
      timeout: 90000,
    });
    return response.data;
  },

  /**
   * --- 6. RETRIEVE ASSISTANT CONVERSATION THREADS ---
   * Fetches paginated chat conversation history with literature citations.
   * 
   * @param {number} page - Page number (defaults to 1).
   * @returns {Promise<Array>} List of ChatConversation objects with messages.
   */
  async getChatHistory(page = 1) {
    const response = await api.get("/assistant/history/", {
      params: { page },
    });
    return response.data.results || response.data;
  },
};

export default aiService;
