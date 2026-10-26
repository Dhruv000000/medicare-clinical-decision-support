// ==============================================================================
// FILE: frontend/vite.config.js
// PURPOSE: Vite build system configuration, React plugin registration, and path alias mapping.
// VIVA EXPLANATION: Configures frontend development server and bundling toolchain. Sets up Tailwind v4 integration and establishes path aliases (@ and @shared) for clean modular imports.
// ==============================================================================

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(process.cwd(), "src"),
      "@shared": path.resolve(process.cwd(), "src/shared"),
    },
  },
});