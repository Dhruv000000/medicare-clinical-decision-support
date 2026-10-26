// ==============================================================================
// FILE: frontend/src/pages/public/patient/patient_routes.js
// PURPOSE: Manifest and metadata registry mapping patient URLs to components and sidebar sections.
// VIVA EXPLANATION: Defines the programmatic route configuration for the patient portal, organizing paths into logical clinical domains (Main, Health, Medical, AI Health, Medicines) for dynamic navigation rendering.
// ==============================================================================

import PatientDashboard from "./patient_dashboard";
import HealthTrends from "./HealthTrends";
import Appointments from "./appointments";
import MedicalRecords from "./medical_records";
import LabTests from "./lab_test";
import Medications from "./medicine";
import SymptomAnalysis from "./symptom";
import Predictions from "./predictions";
import AIAssistant from "./ai_assistant";
import MedicineSearch from "./medicine_search";
import DrugInteractions from "./drug_interactions";
import Settings from "./settings";

export const patientRoutes = [
  { path: "/patient/dashboard", label: "Dashboard", component: PatientDashboard },
  { path: "/patient/health-trends", label: "Health Trends", component: HealthTrends },
  { path: "/patient/appointments", label: "Appointments", component: Appointments },
  { path: "/patient/medical-records", label: "Medical Records", component: MedicalRecords },
  { path: "/patient/lab-tests", label: "Reports & Lab Tests", component: LabTests },
  { path: "/patient/medications", label: "Medications", component: Medications },
  { path: "/patient/symptom-analysis", label: "Symptom Analysis", component: SymptomAnalysis },
  { path: "/patient/predictions", label: "Predictions", component: Predictions },
  { path: "/patient/ai-assistant", label: "AI Assistant", component: AIAssistant },
  { path: "/patient/medicine-search", label: "Medicine Search", component: MedicineSearch },
  { path: "/patient/drug-interactions", label: "Drug Interactions", component: DrugInteractions },
  { path: "/patient/settings", label: "Settings", component: Settings },
];

export const patientSidebarSections = [
  { title: "MAIN", items: patientRoutes.slice(0, 1) },
  { title: "HEALTH", items: patientRoutes.slice(1, 3) },
  { title: "MEDICAL", items: patientRoutes.slice(3, 6) },
  { title: "AI HEALTH", items: patientRoutes.slice(6, 9) },
  { title: "MEDICINES", items: patientRoutes.slice(9, 11) },
];
