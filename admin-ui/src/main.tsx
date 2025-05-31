// CSS imports must be at the top to ensure they're included in the build
// CRITICAL: This import is required for Tailwind CSS to work properly
import './index.css';

// Additional CSS imports for the application (if any)
// Import any component-specific CSS here

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';

console.log('Orchestra Admin UI: Starting application...');

const rootElement = document.getElementById('root');
if (!rootElement) {
  console.error('Root element not found!');
} else {
  console.log('Root element found, rendering app...');
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
  console.log('App rendered successfully');
}
