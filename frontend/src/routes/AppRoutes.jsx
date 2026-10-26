// ==============================================================================
// FILE: frontend/src/routes/AppRoutes.jsx
// PURPOSE: Declarative client-side route manifest using React Router DOM.
// VIVA EXPLANATION: Configures client-side routing for public pages and nested patient portal paths. Maps URLs to views such as AI disease prediction, symptom analysis, lab test parser, and drug interactions within the DashboardLayout container.
// ==============================================================================

import { Routes, Route } from "react-router-dom";

import Landing from "../pages/public/Landing";
import Login from "../pages/public/Login";

// Common dashboard/layout
import DashboardLayout from "../components/layout/DashboardLayout";

// Patient pages
import PatientDashboard from "../pages/patient/patient_dashboard";
import HealthTrends from "../pages/patient/HealthTrends";
import Appointments from "../pages/patient/appointments";
import MedicalRecords from "../pages/patient/medical_records";
import LabTests from "../pages/patient/lab_test";
import Medications from "../pages/patient/medicine";
import SymptomAnalysis from "../pages/patient/symptom";
import Predictions from "../pages/patient/predictions";
import AIAssistant from "../pages/patient/ai_assistant";
import MedicineSearch from "../pages/patient/medicine_search";
import DrugInteractions from "../pages/patient/drug_interactions";
import Settings from "../pages/patient/settings";


// --- AppRoutes ---
// What it does: Renders declarative route branches for landing, login, and nested patient routes.
// Why it's structured this way: Uses nested routes inside /patient so child views share common navigation and layout.
// Parameters & Returns: Props (none) -> React Router Routes element hierarchy.
// ------------------------------------------------------------------------------
function AppRoutes() {
  return (
    <Routes>

      {/* Public Pages */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />

      {/* Dashboard Layout */}
      <Route path="/patient" element={<DashboardLayout />}>

        {/* Main */}
        <Route index element={<PatientDashboard />} />
        <Route path="dashboard" element={<PatientDashboard />} />

        {/* Health */}
        <Route path="health-trends" element={<HealthTrends />} />
        <Route path="appointments" element={<Appointments />} />

        {/* Medical */}
        <Route path="medical-records" element={<MedicalRecords />} />
        <Route path="lab-tests" element={<LabTests />} />
        <Route path="medications" element={<Medications />} />

        {/* AI Health */}
        <Route path="symptom-analysis" element={<SymptomAnalysis />} />
        <Route path="predictions" element={<Predictions />} />
        <Route path="ai-assistant" element={<AIAssistant />} />

        {/* Medicines */}
        <Route path="medicine-search" element={<MedicineSearch />} />
        <Route path="drug-interactions" element={<DrugInteractions />} />

        {/* Settings */}
        <Route path="settings" element={<Settings />} />

      </Route>

    </Routes>
  );
}

export default AppRoutes;