import React, { createContext, useState, useEffect, ReactNode } from 'react';
import usePersonaStore from '../store/personaStore'; // Step 1: Import usePersonaStore

export type Theme = "neutral" | "cherry" | "sophia" | "gordon"; // Kept for base styling for now
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

  // Step 2: Get currentPersonaId and accentColors from usePersonaStore
  const currentPersonaId = usePersonaStore((state) => state.currentPersonaId);
  const accentColors = usePersonaStore((state) => state.accentColors);

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

    // Apply base theme class (e.g., theme-neutral)
    // This can be simplified later if dynamic accent colors are sufficient
    const themeClassesToRemove = ["theme-neutral", "theme-cherry", "theme-sophia", "theme-gordon"];
    root.classList.remove(...themeClassesToRemove);
    root.classList.add(`theme-${theme}`);
     try {
      localStorage.setItem(`${storageKey}-app`, theme);
    } catch (e) {
      console.warn("Failed to save app theme to localStorage", e);
    }

    // Step 3a & 3b: Apply dynamic accent color based on current persona
    const currentAccentColor = accentColors[currentPersonaId];
    if (currentAccentColor) {
      root.style.setProperty('--theme-accent-primary', currentAccentColor);
    } else {
      // Fallback or remove if no specific accent color for the current persona
      // For now, let's remove it if not found, or you could set a default
      root.style.removeProperty('--theme-accent-primary');
    }

  }, [theme, mode, storageKey, currentPersonaId, accentColors]); // Step 3c: Add dependencies

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
