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
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem(storageKey) as Theme) || defaultTheme);
  const [mode, setMode] = useState<'light' | 'dark'>(() => (localStorage.getItem(`${storageKey}-mode`) as 'light' | 'dark') || defaultMode);
  
  // Use activePersonaId instead of currentPersonaId
  const activePersonaId = usePersonaStore((state) => state.activePersonaId);
  
  // Watch for persona changes
  useEffect(() => {
    if (activePersonaId) {
      const persona = usePersonaStore.getState().getPersonaById(activePersonaId);
      if (persona) {
        // Map persona to theme (using valid theme names)
        const personaThemeMap: Record<string, Theme> = {
          'cherry': 'cherry',
          'sophia': 'sophia',
          'karen': 'gordon'  // Using gordon as a green theme for karen
        };
        const newTheme = personaThemeMap[persona.id] || 'neutral';
        setTheme(newTheme);
      }
    }
  }, [activePersonaId]);

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
      localStorage.setItem(storageKey, theme);
    } catch (e) {
      console.warn("Failed to save app theme to localStorage", e);
    }

  }, [theme, mode, storageKey]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, mode, setMode }}>
      {children}
    </ThemeContext.Provider>
  );
};

export { ThemeContext, ThemeProvider };
