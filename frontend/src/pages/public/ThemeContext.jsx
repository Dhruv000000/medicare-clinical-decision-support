// ==============================================================================
// FILE: frontend/src/pages/public/ThemeContext.jsx
// PURPOSE: Backward compatibility re-export barrel for the central ThemeContext module.
// VIVA EXPLANATION: Re-exports ThemeProvider, useTheme, and design tokens from src/context/ThemeContext.jsx ensuring backward compatibility with legacy public page imports.
// ==============================================================================

export {
  ThemeProvider,
  useTheme,
  ThemeContext,
  THEME_VARIABLES,
} from "../../context/ThemeContext";

export { default } from "../../context/ThemeContext";