import React from "react";

import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider } from "./context/AuthContext";
import { useAuth } from "./_core/hooks/useAuth";

// =========================================================
// PUBLIC PAGES
// =========================================================

import LandingPage from "./pages/public/Landing";
import Login from "./pages/public/login";
import Register from "./pages/public/register";

// =========================================================
// PATIENT PAGES
// =========================================================

import PatientDashboard from "./pages/public/patient/patient_dashboard";
import HealthTrends from "./pages/public/patient/HealthTrends";
import Appointments from "./pages/public/patient/appointments";
import MedicalRecords from "./pages/public/patient/medical_records";
import LabTests from "./pages/public/patient/lab_test";
import Medications from "./pages/public/patient/medicine";
import SymptomAnalysis from "./pages/public/patient/symptom";
import Predictions from "./pages/public/patient/predictions";
import AIAssistant from "./pages/public/patient/ai_assistant";
import MedicineSearch from "./pages/public/patient/medicine_search";
import DrugInteractions from "./pages/public/patient/drug_interactions";
import Settings from "./pages/public/patient/settings";

// =========================================================
// DOCTOR PAGES
// =========================================================

import DoctorDashboard from "./pages/public/doctor/doctor_dashboard";
import ClinicalNotes from "./pages/public/doctor/clinicalnotes";
import DoctorInsights from "./pages/public/doctor/insights";
import DoctorMedications from "./pages/public/doctor/appointmentss";
import MedKnowledge from "./pages/public/doctor/medknowledge";
import DoctorPatients from "./pages/public/doctor/patients";
import DoctorReports from "./pages/public/doctor/reports";

// =========================================================
// ADMIN PAGES
// =========================================================

import AdminDashboard from "./pages/public/admin/admin_dashboard";
import AdminLogin from "./pages/public/admin-login";

// =========================================================
// PROTECTED ROUTE
// =========================================================

function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading, role } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f8faf9] text-emerald-900 font-medium">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
          <span>Loading your secure workspace…</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    const currentRole = role || user.role;
    if (!allowedRoles.includes(currentRole)) {
      if (currentRole === "doctor") {
        return <Navigate to="/doctor/dashboard" replace />;
      }
      if (currentRole === "admin") {
        return <Navigate to="/admin/dashboard" replace />;
      }
      return <Navigate to="/patient/dashboard" replace />;
    }
  }

  return children;
}

// =========================================================
// APP
// =========================================================

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ThemeProvider>
          <Routes>

          {/* =================================================
              PUBLIC ROUTES
          ================================================= */}

          <Route
            path="/"
            element={<LandingPage />}
          />

          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/register"
            element={<Register />}
          />

          <Route
            path="/admin/login"
            element={<AdminLogin />}
          />

          {/* =================================================
              PATIENT ROUTES
          ================================================= */}

          <Route
            path="/patient/dashboard"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <PatientDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/health-trends"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <HealthTrends />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/appointments"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <Appointments />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/medical-records"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <MedicalRecords />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/reports-lab-tests"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <LabTests />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/lab-tests"
            element={<Navigate to="/patient/reports-lab-tests" replace />}
          />

          <Route
            path="/patient/medications"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <Medications />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/symptom-analysis"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <SymptomAnalysis />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/predictions"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <Predictions />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/ai-assistant"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <AIAssistant />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/medicine-search"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <MedicineSearch />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/drug-interactions"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <DrugInteractions />
              </ProtectedRoute>
            }
          />

          <Route
            path="/patient/settings"
            element={
              <ProtectedRoute allowedRoles={["patient"]}>
                <Settings />
              </ProtectedRoute>
            }
          />

          {/* =================================================
              DOCTOR ROUTES
          ================================================= */}

          {/* Doctor Dashboard */}
          <Route
            path="/doctor/dashboard"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <DoctorDashboard />
              </ProtectedRoute>
            }
          />

          {/* Clinical Notes */}
          <Route
            path="/doctor/clinical-notes"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <ClinicalNotes />
              </ProtectedRoute>
            }
          />

          {/* Doctor Insights */}
          <Route
            path="/doctor/insights"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <DoctorInsights />
              </ProtectedRoute>
            }
          />

          {/* Doctor Medications */}
          <Route
            path="/doctor/medications"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <DoctorMedications />
              </ProtectedRoute>
            }
          />

          {/* Doctor Appointments */}
          <Route
            path="/doctor/appointments"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <DoctorMedications />
              </ProtectedRoute>
            }
          />

          {/* Medical Knowledge */}
          <Route
            path="/doctor/medical-knowledge"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <MedKnowledge />
              </ProtectedRoute>
            }
          />

          {/* Doctor Settings */}
          <Route
            path="/doctor/settings"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <Settings />
              </ProtectedRoute>
            }
          />

          {/* Patients */}
          <Route
            path="/doctor/patients"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <DoctorPatients />
              </ProtectedRoute>
            }
          />

          {/* Reports */}
          <Route
            path="/doctor/reports"
            element={
              <ProtectedRoute allowedRoles={["doctor"]}>
                <DoctorReports />
              </ProtectedRoute>
            }
          />

          {/* =================================================
              ADMIN ROUTES
          ================================================= */}

          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          {/* =================================================
              FALLBACK
          ================================================= */}

          <Route
            path="*"
            element={<Navigate to="/" replace />}
          />

        </Routes>
      </ThemeProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;