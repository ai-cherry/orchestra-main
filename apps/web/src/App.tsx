import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import { HomePage } from './components/HomePage';
import { wsClient } from './services/websocketClient';
import { AIProvider } from './contexts/AIContext';
import PerformanceMonitor from './components/PerformanceMonitor';
import './index.css';

// Initialize WebSocket connection
const initializeWebSocket = async () => {
  try {
    await wsClient.connect();
    console.log('🔌 WebSocket connected successfully');
  } catch (error) {
    console.warn('⚠️ WebSocket connection failed, will retry:', error);
  }
};

// AI Development startup message
const logAIFeatures = () => {
  if (process.env.NODE_ENV === 'development') {
    console.log('🤖 AI-First Development Mode Enabled');
    console.log('⚡ Performance monitoring active');
    console.log('🎯 Near-term enhancements loaded');
    console.log('🚀 Ready for AI-driven development');
  }
};

function App() {
  useEffect(() => {
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // Log AI features
    logAIFeatures();

    // Cleanup on unmount
    return () => {
      wsClient.disconnect();
    };
  }, []);

  return (
    <Provider store={store}>
      <AIProvider>
        <Router>
          <div className="App min-h-screen bg-gradient-to-br from-primary-surface via-primary-surface2 to-primary-surface3">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/home" element={<HomePage />} />
            </Routes>
            
            {/* Performance Monitor - only visible in development or when AI features are enabled */}
            <PerformanceMonitor />
          </div>
        </Router>
      </AIProvider>
    </Provider>
  );
}

export default App;
