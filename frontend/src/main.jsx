// ==============================================================================
// FILE: frontend/src/main.jsx
// PURPOSE: Application bootstrap entry point rendering the root React component into the DOM.
// VIVA EXPLANATION: The client-side entry point of the MediCare Single Page Application (SPA). Mounts the React 18 component tree onto document element #root, wrapping it in React StrictMode and ThemeProvider for application-wide light/dark themes.
// ==============================================================================

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";

import App from "./App.jsx";

// Theme
import { ThemeProvider } from "./pages/public/ThemeContext.jsx";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error(
    "The client root element was not found."
  );
}

// --- createRoot render ---
// What it does: Mounts the top-level React component hierarchy into the browser DOM.
// Why it's structured this way: Uses React 18 Concurrent Root API with StrictMode for lifecycle highlighting.
// Parameters & Returns: rootElement (DOM element) -> Rendered React tree.
// ------------------------------------------------------------------------------
createRoot(rootElement).render(
  <StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </StrictMode>
);