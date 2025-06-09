import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.tsx'
import { PersonaProvider } from './contexts/PersonaContext'
import './index.css'

  <React.StrictMode>
    <BrowserRouter>
      <PersonaProvider>
        <App />
      </PersonaProvider>
    </BrowserRouter>
  </React.StrictMode>,
) 