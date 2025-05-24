import React from "react";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Agents from "./pages/Agents";
import Resources from "./pages/Resources";
import Integrations from "./pages/Integrations";
import Workflows from "./pages/Workflows";
import Personas from "./pages/Personas";
import Logs from "./pages/Logs";
import Settings from "./pages/Settings";
import FloatingChat from "./components/FloatingChat";
import TopBar from "./components/TopBar";
import useThemeMode from "./hooks/useThemeMode";

const App: React.FC = () => {
  const { mode, toggleMode } = useThemeMode();
  const theme = React.useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: { main: "#d72660" }, // Cherry color
          secondary: { main: "#1b1b3a" },
        },
        shape: { borderRadius: 12 },
        typography: { fontFamily: "Inter, sans-serif" },
      }),
    [mode],
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div style={{ display: "flex", minHeight: "100vh" }}>
          <Sidebar />
          <main
            style={{ flex: 1, background: theme.palette.background.default }}
          >
            <TopBar toggleMode={toggleMode} />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/resources" element={<Resources />} />
              <Route path="/integrations" element={<Integrations />} />
              <Route path="/workflows" element={<Workflows />} />
              <Route path="/personas" element={<Personas />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
          <FloatingChat />
        </div>
      </Router>
    </ThemeProvider>
  );
};

export default App;
