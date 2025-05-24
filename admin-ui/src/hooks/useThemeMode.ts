import { useState } from "react";

const useThemeMode = () => {
  const [mode, setMode] = useState<"light" | "dark">("light");
  const toggleMode = () => setMode((prev) => (prev === "light" ? "dark" : "light"));
  return { mode, toggleMode };
};

export default useThemeMode;