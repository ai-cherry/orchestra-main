// CSS imports must be at the top to ensure they're included in the build
// CRITICAL: This import is required for Tailwind CSS to work properly
import './index.css';

// Additional CSS imports for the application (if any)
// Import any component-specific CSS here

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
