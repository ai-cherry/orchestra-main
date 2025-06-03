import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import { AuthProvider } from './contexts/AuthContext';
import { PersonaProvider } from './contexts/PersonaContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { Layout } from './components/layout/Layout';
import { HomePage } from './pages/HomePage';
import { SearchPage } from './pages/SearchPage';
import { AgentLabPage } from './pages/AgentLabPage';
import { OrchestratorsPage } from './pages/OrchestratorsPage';
import { MonitoringPage } from './pages/MonitoringPage';
import { SettingsPage } from './pages/SettingsPage';
import './styles/globals.css';

function App() {
  return (
    <Provider store={store}>
      <AuthProvider>
        <PersonaProvider>
          <ThemeProvider>
            <Router>
              <Layout>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/search" element={<SearchPage />} />
                  <Route path="/agent-lab" element={<AgentLabPage />} />
                  <Route path="/orchestrators" element={<OrchestratorsPage />} />
                  <Route path="/monitoring" element={<MonitoringPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </Layout>
            </Router>
          </ThemeProvider>
        </PersonaProvider>
      </AuthProvider>
    </Provider>
  );
}

export default App;
