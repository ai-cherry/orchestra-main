import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './globals.css'
import { AppProvider } from './contexts/AppContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { PersonaProvider } from './contexts/PersonaContext';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppProvider>
      <WebSocketProvider>
        <PersonaProvider>
          <App />
        </PersonaProvider>
      </WebSocketProvider>
    </AppProvider>
  </React.StrictMode>,
)