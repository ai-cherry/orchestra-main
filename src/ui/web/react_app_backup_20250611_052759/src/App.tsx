import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import { HomePage } from './components/HomePage';
import { wsClient } from './services/websocketClient';
import './index.css';

// Initialize WebSocket connection
const initializeWebSocket = async () => {
  try {
    await wsClient.connect();
    // console.log('WebSocket connected successfully');
  } catch (error) {
    console.warn('WebSocket connection failed, will retry:', error);
  }
};

function App() {
  useEffect(() => {
    // Initialize WebSocket connection
    initializeWebSocket();

    // Cleanup on unmount
    return () => {
      wsClient.disconnect();
    };
  }, []);

  return (
    <Provider store={store}>
      <Router>
        <div className="App min-h-screen bg-gradient-to-br from-primary-surface via-primary-surface2 to-primary-surface3">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/home" element={<HomePage />} />
          </Routes>
        </div>
      </Router>
    </Provider>
  );
}

export default App;
