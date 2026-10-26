// ==============================================================================
// FILE: frontend/src/services/doctorService.js
// PURPOSE: Client-side HTTP service facilitating clinician operations, patient charts, and clinical notes.
// VIVA EXPLANATION: Manages all REST communication for doctors. Strictly conforms to access control rules, providing functions to fetch authorized patient rosters, EHR histories, diagnostic reports, post clinical SOAP notes, prescribe medications, and update appointment statuses.
// ==============================================================================

import api from "./api";

export const doctorService = {
  // --- getDashboard ---
  // What it does: Retrieves live aggregated clinical insights, patient volume, and appointment metrics.
  // Why it's structured this way: Powers the KPI cards on the physician portal dashboard.
  // Parameters & Returns: None -> Dashboard metrics object (total_patients, today_appointments, etc.).
  // ------------------------------------------------------------------------------
  async getDashboard() {
    const response = await api.get("/doctor/dashboard/");
    return response.data;
  },

  // --- getPatients ---
  // What it does: Fetches list of patients clinically authorized for this physician.
  // Why it's structured this way: Enforces role boundaries; clinicians only see patients with established care links.
  // Parameters & Returns: None -> Array of patient summary objects.
  // ------------------------------------------------------------------------------
  async getPatients() {
    const response = await api.get("/doctor/patients/");
    return response.data.results || response.data;
  },

  // --- getPatientDetails ---
  // What it does: Retrieves comprehensive demographic and baseline clinical data for a specific patient.
  // Why it's structured this way: Populates individual patient chart view headers and summaries.
  // Parameters & Returns: patientId (number) -> Patient detail object or throws 403 if unauthorized.
  // ------------------------------------------------------------------------------
  async getPatientDetails(patientId) {
    const response = await api.get(`/doctor/patients/${patientId}/`);
    return response.data;
  },

  // --- getPatientRecords ---
  // What it does: Retrieves longitudinal electronic medical records for an authorized patient.
  // Why it's structured this way: Supplies the patient chart timeline with clinical visit histories.
  // Parameters & Returns: patientId (number) -> Array of MedicalRecord objects.
  // ------------------------------------------------------------------------------
  async getPatientRecords(patientId) {
    const response = await api.get(`/doctor/patients/${patientId}/records/`);
    return response.data.results || response.data;
  },

  // --- getPatientReports ---
  // What it does: Fetches laboratory test reports and parsed biomarker results for an authorized patient.
  // Why it's structured this way: Supplies structured lab panels to assist diagnostic decision-making.
  // Parameters & Returns: patientId (number) -> Array of LabReport objects.
  // ------------------------------------------------------------------------------
  async getPatientReports(patientId) {
    const response = await api.get(`/doctor/patients/${patientId}/reports/`);
    return response.data.results || response.data;
  },

  // --- getPatientNotes ---
  // What it does: Retrieves historical clinical consultation notes filed for this patient.
  // Why it's structured this way: Gives attending clinicians continuity of care across prior visits.
  // Parameters & Returns: patientId (number) -> Array of ClinicalNote objects.
  // ------------------------------------------------------------------------------
  async getPatientNotes(patientId) {
    const response = await api.get(`/doctor/patients/${patientId}/clinical-notes/`);
    return response.data;
  },

  // --- createClinicalNote ---
  // What it does: Submits a new SOAP clinical note and preliminary diagnosis for an authorized patient.
  // Why it's structured this way: Logs consultation observations to both the database and audit trail.
  // Parameters & Returns: patientId (number), payload ({ note, diagnosis }) -> Created ClinicalNote.
  // ------------------------------------------------------------------------------
  async createClinicalNote(patientId, payload) {
    const response = await api.post(
      `/doctor/patients/${patientId}/clinical-notes/`,
      payload
    );
    return response.data;
  },

  // --- prescribeMedication ---
  // What it does: Submits a new prescription order for an authorized patient.
  // Why it's structured this way: Attaches the prescribing doctor's ID and updates patient medication list.
  // Parameters & Returns: payload ({ patient_id, name, dosage, frequency }) -> Created Medication record.
  // ------------------------------------------------------------------------------
  async prescribeMedication(payload) {
    const response = await api.post("/medicines/", payload);
    return response.data;
  },

  // --- getAppointments ---
  // What it does: Retrieves all appointments scheduled with this physician.
  // Why it's structured this way: Powers the doctor's appointment calendar and daily consultation schedule.
  // Parameters & Returns: None -> Array of Appointment objects.
  // ------------------------------------------------------------------------------
  async getAppointments() {
    const response = await api.get("/doctor/appointments/");
    return response.data.results || response.data;
  },

  // --- updateAppointmentStatus ---
  // What it does: Transitions an appointment's status (e.g. confirmed, completed, cancelled).
  // Why it's structured this way: Allows physicians to confirm bookings or conclude consultations.
  // Parameters & Returns: appointmentId (number), status (string) -> Updated Appointment record.
  // ------------------------------------------------------------------------------
  async updateAppointmentStatus(appointmentId, status) {
    const response = await api.patch(`/appointments/${appointmentId}/`, {
      status,
    });
    return response.data;
  },

  // --- getProfile ---
  // What it does: Retrieves physician credentials, hospital affiliation, and medical license info.
  // Why it's structured this way: Loads doctor profile and settings screen.
  // Parameters & Returns: None -> DoctorProfile dictionary.
  // ------------------------------------------------------------------------------
  async getProfile() {
    const response = await api.get("/doctor/profile/");
    return response.data;
  },

  // --- updateProfile ---
  // What it does: Updates doctor bio, hospital affiliation, and clinical specialization.
  // Why it's structured this way: Allows physicians to manage their credentials and bio.
  // Parameters & Returns: payload (object) -> Updated DoctorProfile object.
  // ------------------------------------------------------------------------------
  async updateProfile(payload) {
    const response = await api.patch("/doctor/profile/", payload);
    return response.data;
  },
};

export default doctorService;

