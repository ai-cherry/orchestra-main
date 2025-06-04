// CSS imports must be at the top to ensure they're included in the build
// CRITICAL: This import is required for Tailwind CSS to work properly
import './index.css';

// Additional CSS imports for the application (if any)
// Import any component-specific CSS here
import './styles/orchestrator.css';

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Add version identifier
const BUILD_VERSION = import.meta.env.VITE_BUILD_TIME || Date.now().toString();
const BUILD_DATE = new Date().toISOString();

// Log version info
console.log(`🎼 Orchestra AI v${BUILD_VERSION}`);
console.log(`📅 Built: ${BUILD_DATE}`);

// Add global error handlers
window.onerror = (message, source, lineno, colno, error) => {
  console.error('Global error:', { message, source, lineno, colno, error });
  return true; // Prevent default error handling
};

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  event.preventDefault();
});

// Render app with error boundary
try {
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    throw new Error('Root element not found');
  }
  
  // Add version as data attribute
  rootElement.setAttribute('data-version', BUILD_VERSION);
  rootElement.setAttribute('data-build-date', BUILD_DATE);
  
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} catch (error) {
  console.error('Failed to render app:', error);
  // Fallback UI
  const rootElement = document.getElementById('root');
  if (rootElement) {
    rootElement.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: center; min-height: 100vh; font-family: system-ui, -apple-system, sans-serif;">
        <div style="text-align: center; padding: 2rem;">
          <h1 style="color: #ef4444; font-size: 1.5rem; font-weight: bold; margin-bottom: 1rem;">
            Failed to Start Application
          </h1>
          <p style="color: #6b7280; margin-bottom: 1rem;">
            Please refresh the page or contact support if the problem persists.
          </p>
          <button onclick="window.location.reload()" style="background: #3b82f6; color: white; padding: 0.5rem 1rem; border: none; border-radius: 0.375rem; cursor: pointer;">
            Refresh Page
          </button>
          <div style="margin-top: 2rem; padding: 1rem; background: #f3f4f6; border-radius: 0.375rem; text-align: left;">
            <code style="font-size: 0.875rem; color: #374151;">
              Version: ${BUILD_VERSION}<br>
              Error: ${error instanceof Error ? error.message : 'Unknown error'}
            </code>
          </div>
        </div>
      </div>
    `;
  }
}
