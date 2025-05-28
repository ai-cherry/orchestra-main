import React, { createContext, useState, useEffect, ReactNode } from 'react';

export type Theme = "neutral" | "cherry" | "sophia" | "gordon";
export type Mode = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  mode: Mode;
  setMode: (mode: Mode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const ThemeProvider: React.FC<{ children: ReactNode; defaultTheme?: Theme; defaultMode?: Mode, storageKey?: string }> = ({
  children,
  defaultTheme = "neutral",
  defaultMode = "light",
  storageKey = "vite-ui-theme",
}) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    try {
      return (localStorage.getItem(`${storageKey}-app`) as Theme) || defaultTheme;
    } catch (e) {
      console.warn("Failed to read app theme from localStorage", e);
      return defaultTheme;
    }
  });

  const [mode, setModeState] = useState<Mode>(() => {
    try {
      return (localStorage.getItem(`${storageKey}-mode`) as Mode) || defaultMode;
    } catch (e) {
      console.warn("Failed to read mode from localStorage", e);
      return defaultMode;
    }
  });

  useEffect(() => {
    const root = window.document.documentElement;
    // Apply mode (dark/light)
    root.classList.remove("light", "dark");
    root.classList.add(mode);
    try {
      localStorage.setItem(`${storageKey}-mode`, mode);
    } catch (e) {
       console.warn("Failed to save mode to localStorage", e);
    }

    // Apply theme class
    // Remove old theme classes
    const themeClassesToRemove = ["theme-neutral", "theme-cherry", "theme-sophia", "theme-gordon"];
    root.classList.remove(...themeClassesToRemove);
    // Add new theme class
    root.classList.add(`theme-${theme}`);
     try {
      localStorage.setItem(`${storageKey}-app`, theme);
    } catch (e) {
      console.warn("Failed to save app theme to localStorage", e);
    }
  }, [theme, mode, storageKey]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const setMode = (newMode: Mode) => {
    setModeState(newMode);
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, mode, setMode }}>
      {children}
    </ThemeContext.Provider>
  );
};

export { ThemeContext, ThemeProvider };
