import React, { createContext, useContext, useEffect, useState } from "react";

export const ThemeContext = createContext(null);

export const THEME_VARIABLES = {
  dark: {
    "--bg": "#0b1715",
    "--surface": "#0d1a18",
    "--card": "#10211e",
    "--card-soft": "#101f1d",
    "--card-hover": "#122723",
    "--border": "#173c36",
    "--border-soft": "#24413d",
    "--text": "#ffffff",
    "--text-secondary": "#b5c5c7",
    "--muted": "#718b91",
    "--muted-strong": "#91a6aa",
    "--accent": "#00c896",
    "--accent-soft": "#123b31",
    "--accent-surface": "#0d3b30",
    "--track": "#17342f",
    "--accent-medium": "#54d8b5",
    "--low-risk": "#5f7c80",
  },
  light: {
    "--bg": "#f2f7f5",
    "--surface": "#ffffff",
    "--card": "#ffffff",
    "--card-soft": "#f7faf9",
    "--card-hover": "#edf6f2",
    "--border": "#c7d9d4",
    "--border-soft": "#b7cec7",
    "--text": "#10231f",
    "--text-secondary": "#294841",
    "--muted": "#4f6962",
    "--muted-strong": "#3d5a53",
    "--accent": "#009f79",
    "--accent-soft": "#e2f5ef",
    "--accent-surface": "#d9f2eb",
    "--track": "#c9ddd7",
    "--accent-medium": "#35b795",
    "--low-risk": "#7a928e",
  },
};

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    if (typeof window === "undefined") return "light";
    const savedTheme = localStorage.getItem("medicare-theme");
    if (savedTheme === "dark" || savedTheme === "light") {
      return savedTheme;
    }
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    const root = document.documentElement;
    const variables = THEME_VARIABLES[theme] || THEME_VARIABLES.light;

    root.classList.toggle("dark", theme === "dark");
    root.setAttribute("data-theme", theme);
    root.style.colorScheme = theme;

    Object.entries(variables).forEach(([name, value]) => {
      root.style.setProperty(name, value);
    });

    if (document.body) {
      document.body.style.backgroundColor = variables["--bg"];
      document.body.style.color = variables["--text"];
    }

    localStorage.setItem("medicare-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"));
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        toggleTheme,
        isDark: theme === "dark",
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used inside a ThemeProvider");
  }
  return context;
}

export default ThemeProvider;