import api from "./api";

export const aiService = {
  /**
   * Maps free-text symptom description or symptom list to canonical clinical vocabulary
   * and suggests relevant related symptoms.
   * payload: { text: "..." } or { symptoms: ["fever", "cough"] }
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
   * Executes disease classification inference with SHAP explainability.
   * payload: { symptoms: [...], patient_id?: number }
   */
  async predictDisease(data) {
    const response = await api.post("/predictions/disease/", data, {
      timeout: 90000,
    });
    return response.data;
  },

  /**
   * Retrieves past disease predictions for the authenticated patient or authorized doctor.
   */
  async getPredictionHistory() {
    const response = await api.get("/predictions/");
    return response.data.results || response.data;
  },

  /**
   * Retrieves past symptom analysis history for the authenticated patient.
   */
  async getSymptomHistory() {
    const response = await api.get("/predictions/symptoms/");
    return response.data.results || response.data;
  },

  /**
   * Sends a prompt to the PubMed-grounded Medical RAG Assistant.
   * payload: { prompt: "...", conversation_id?: number, patient_id?: number }
   */
  async sendChatMessage(data) {
    const response = await api.post("/assistant/chat/", data, {
      timeout: 90000,
    });
    return response.data;
  },

  /**
   * Retrieves historical chat conversations for the authenticated user.
   */
  async getChatHistory(page = 1) {
    const response = await api.get("/assistant/history/", {
      params: { page },
    });
    return response.data.results || response.data;
  },
};

export default aiService;
