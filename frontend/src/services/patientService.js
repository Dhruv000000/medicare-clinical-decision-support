// ==============================================================================
// FILE: frontend/src/services/patientService.js
// PURPOSE: Client-side HTTP service facilitating patient operations, appointment booking, lab tests, and medications.
// VIVA EXPLANATION: Centralizes all API communications for patient users. Encapsulates endpoints for dashboard metrics, doctor discovery, appointment requests, multipart lab report uploads, and OpenFDA drug-interaction safety queries.
// ==============================================================================

import api from "./api";

export const patientService = {
  // --- getDashboardSummary ---
  // What it does: Fetches aggregated database metrics for the logged-in patient's dashboard.
  // Why it's structured this way: Direct call to consolidated endpoint to reduce client-side latency.
  // Parameters & Returns: None -> Dashboard metrics object (appointments, med counts, records).
  // ------------------------------------------------------------------------------
  async getDashboardSummary() {
    const response = await api.get("/patient/dashboard/");
    return response.data;
  },

  // --- getAppointments ---
  // What it does: Retrieves paginated consultation appointments filtered optionally by status.
  // Why it's structured this way: Unpacks paginated DRF responses to provide convenient array access to React components.
  // Parameters & Returns: status (string|null) -> Array of appointment objects.
  // ------------------------------------------------------------------------------
  async getAppointments(status) {
    const params = status ? { status } : {};
    const response = await api.get("/patient/appointments/", { params });
    return response.data.results || response.data;
  },

  // --- getDoctors ---
  // What it does: Queries public directory of active verified physicians available for consultations.
  // Why it's structured this way: Populates doctor selector dropdowns in appointment booking modal.
  // Parameters & Returns: None -> Array of doctor profiles with IDs, specializations, and names.
  // ------------------------------------------------------------------------------
  async getDoctors() {
    const response = await api.get("/doctor/list/");
    return response.data;
  },

  // --- bookAppointment ---
  // What it does: Sends HTTP POST request to schedule a new consultation with a chosen physician.
  // Why it's structured this way: Enforces structured payload containing doctor ID, ISO start time, and reason.
  // Parameters & Returns: data (object) -> Created appointment entity.
  // ------------------------------------------------------------------------------
  async bookAppointment(data) {
    const response = await api.post("/patient/appointments/", data);
    return response.data;
  },

  // --- getMedicalRecords ---
  // What it does: Retrieves patient's longitudinal electronic medical history records.
  // Why it's structured this way: Supports patient-side auditing of clinical notes and past visit logs.
  // Parameters & Returns: None -> Array of MedicalRecord items.
  // ------------------------------------------------------------------------------
  async getMedicalRecords() {
    const response = await api.get("/patient/medical-records/");
    return response.data.results || response.data;
  },

  // --- getLabReports ---
  // What it does: Retrieves laboratory test reports and parsed biomarker values.
  // Why it's structured this way: Gives patients access to historical lab trends and abnormal metric flags.
  // Parameters & Returns: None -> Array of LabReport items with associated results.
  // ------------------------------------------------------------------------------
  async getLabReports() {
    const response = await api.get("/patient/lab-tests/");
    return response.data.results || response.data;
  },

  // --- uploadMedicalRecord ---
  // What it does: Uploads laboratory diagnostic reports (PDF/Image) using multipart/form-data.
  // Why it's structured this way: Uses multipart headers to support binary file transport alongside metadata.
  // Parameters & Returns: formData (FormData instance) -> Created LabReport object.
  // ------------------------------------------------------------------------------
  async uploadMedicalRecord(formData) {
    const response = await api.post("/patient/reports/upload/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  // --- analyzeLabReport ---
  // What it does: Triggers NLP/regex biomarker extraction pipeline on an uploaded lab report.
  // Why it's structured this way: Allows on-demand re-analysis of documents into structured numerical metrics.
  // Parameters & Returns: reportId (number) -> Parsed biomarker results with reference range status.
  // ------------------------------------------------------------------------------
  async analyzeLabReport(reportId) {
    const response = await api.post(`/records/${reportId}/analyze/`);
    return response.data;
  },

  // --- getMedications ---
  // What it does: Queries patient prescriptions, optionally filtering active versus inactive medications.
  // Why it's structured this way: Feeds medication schedule cards and drug interaction checking tools.
  // Parameters & Returns: isActive (boolean|null) -> Array of Medication records.
  // ------------------------------------------------------------------------------
  async getMedications(isActive) {
    const params = typeof isActive === "boolean" ? { is_active: isActive } : {};
    const response = await api.get("/medicines/", { params });
    return response.data.results || response.data;
  },

  // --- addMedication ---
  // What it does: Records a new self-reported or prescribed medication in the patient profile.
  // Why it's structured this way: Ensures drug name, dosage, and frequency are saved to the clinical DB.
  // Parameters & Returns: data (object) -> Created medication record.
  // ------------------------------------------------------------------------------
  async addMedication(data) {
    const response = await api.post("/medicines/", data);
    return response.data;
  },

  // --- getDrugReactions ---
  // What it does: Queries OpenFDA drug safety endpoints for adverse drug reactions and warnings.
  // Why it's structured this way: Connects patient UI directly to official regulatory safety data.
  // Parameters & Returns: drugName (string), limit (number=5) -> Adverse reaction list and warnings.
  // ------------------------------------------------------------------------------
  async getDrugReactions(drugName, limit = 5) {
    const response = await api.get("/medicines/openfda/reactions/", {
      params: {
        drug: drugName,
        limit,
      },
    });
    return response.data;
  },

  // --- checkInteractions ---
  // What it does: Submits medication combinations to verify pharmacological safety and contraindications.
  // Why it's structured this way: Proactively protects patients against adverse multi-drug interactions.
  // Parameters & Returns: data ({ drugs: string[] }) -> Drug interaction report with severity classifications.
  // ------------------------------------------------------------------------------
  async checkInteractions(data) {
    const response = await api.post("/medicines/interactions/", data);
    return response.data;
  },

  // --- getProfile ---
  // What it does: Retrieves patient demographics, emergency contacts, and baseline medical summary.
  // Why it's structured this way: Loads profile settings and personal information forms.
  // Parameters & Returns: None -> Patient profile dictionary.
  // ------------------------------------------------------------------------------
  async getProfile() {
    const response = await api.get("/patient/profile/");
    return response.data;
  },

  // --- updateProfile ---
  // What it does: Submits PATCH request to update demographic details, blood group, or emergency contact.
  // Why it's structured this way: Performs partial updates without requiring complete object resubmission.
  // Parameters & Returns: data (object) -> Updated patient profile.
  // ------------------------------------------------------------------------------
  async updateProfile(data) {
    const response = await api.patch("/patient/profile/", data);
    return response.data;
  },
};

export default patientService;


