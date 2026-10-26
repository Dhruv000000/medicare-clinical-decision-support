// ==============================================================================
// FILE: frontend/src/pages/public/doctor/doctor_routes.jsx
// PURPOSE: Sub-router defining physician client-side SPA routing tree and navigation guards.
// VIVA EXPLANATION: This routing manifest maps URL endpoints under /doctor/* to their corresponding clinical views (Dashboard, Patients, Reports, AI Insights, Appointments, Clinical Notes, Medical Knowledge, Settings, Logout).
// ==============================================================================

import React from "react";
import { Route, Routes, Navigate } from "react-router-dom";

import DoctorDashboard from "./doctor_dashboard";
import Patients from "./patients";
import Reports from "./reports";
import Insights from "./insights";
import ClinicalNotes from "./clinicalnotes";
import MedicalKnowledge from "./medknowledge";
import Settings from "./settings";
import Logout from "./logout";
import Appointments from "./appointmentss";

// --- DoctorRoutes ---
// What it does: Central React Router configuration declaring all nested doctor paths.
// Why it's structured this way: Encapsulates doctor domain routes in a dedicated module, decoupling practitioner navigation from patient and admin route trees.
// Parameters & Returns: None. Returns Route/Routes JSX configuration.
// ------------------------------------------------------------------------------
export default function DoctorRoutes() {
  return (
    <Routes>
      <Route path="/doctor" element={<Navigate to="/doctor/dashboard" replace />} />
      <Route path="/doctor/dashboard" element={<DoctorDashboard />} />
      <Route path="/doctor/patients" element={<Patients />} />
      <Route path="/doctor/reports" element={<Reports />} />
      <Route path="/doctor/insights" element={<Insights />} />
      <Route path="/doctor/appointments" element={<Appointments />} />
      <Route path="/doctor/clinical-notes" element={<ClinicalNotes />} />
      <Route path="/doctor/medical-knowledge" element={<MedicalKnowledge />} />
      <Route path="/doctor/settings" element={<Settings />} />
      <Route path="/doctor/logout" element={<Logout />} />
    </Routes>
  );
}
