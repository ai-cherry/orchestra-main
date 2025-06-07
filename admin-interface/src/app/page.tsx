"use client"

import React, { useState } from 'react'
import { usePersona } from '../contexts/PersonaContext'
import {
  Search,
  MessageSquare,
  Brain,
  Zap,
  Shield,
  BarChart3,
  FileText,
  Play,
  Sparkles
} from 'lucide-react'

const SearchPage = () => {
  const { currentPersona } = usePersona()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedMode, setSelectedMode] = useState('normal')

  const theme = currentPersona.theme;

  const searchModes = [
    { id: 'normal', name: 'Normal', icon: Search, time: '~2s', cost: 'Low', color: '#3b82f6', description: "Fast, balanced search for general queries." },
    { id: 'deep', name: 'Deep', icon: Brain, time: '~15s', cost: 'Medium', color: '#8b5cf6', description: "More thorough analysis with re-ranking." },
    { id: 'super', name: 'Super Deep', icon: Zap, time: '~45s', cost: 'High', color: '#f59e0b', description: "Multi-stage reasoning for complex questions." },
    { id: 'creative', name: 'Creative', icon: Sparkles, time: '~8s', cost: 'Medium', color: '#ec4899', description: "Generates novel ideas and connections." },
    { id: 'private', name: 'Private', icon: Shield, time: '~3s', cost: 'Low', color: '#10b981', description: "Secure, isolated search on your local data." },
    { id: 'analytical', name: 'Analytical', icon: BarChart3, time: '~20s', cost: 'High', color: '#06b6d4', description: "Focuses on data, trends, and statistics." },
    { id: 'research', name: 'Research', icon: FileText, time: '~60s', cost: 'Premium', color: '#d92626', description: "Comprehensive academic and paper search." }
  ]

  const currentMode = searchModes.find(mode => mode.id === selectedMode) || searchModes[0];

  return (
    <div style={{ display: 'flex', gap: '2rem' }}>
      {/* Left Column: Search Modes */}
      <div style={{ width: '250px' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#888', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Search Modes
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {searchModes.map((mode) => (
            <button
              key={mode.id}
              onClick={() => setSelectedMode(mode.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem',
                borderRadius: '8px',
                border: selectedMode === mode.id ? `1px solid ${mode.color}` : '1px solid transparent',
                background: selectedMode === mode.id ? `${mode.color}20` : 'transparent',
                cursor: 'pointer',
                textAlign: 'left',
                color: selectedMode === mode.id ? mode.color : '#888',
                transition: 'all 0.2s ease-in-out'
              }}
              onMouseEnter={(e) => { if (selectedMode !== mode.id) e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)'; }}
              onMouseLeave={(e) => { if (selectedMode !== mode.id) e.currentTarget.style.backgroundColor = 'transparent'; }}
            >
              <mode.icon size={18} />
              <span style={{ fontWeight: 500 }}>{mode.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Right Column: Search Results & Info */}
      <div style={{ flex: 1 }}>
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          padding: '2rem',
          borderRadius: '12px',
          border: '1px solid rgba(255,255,255,0.1)'
        }}>
          <div style={{ marginBottom: '1.5rem', borderLeft: `3px solid ${currentMode.color}`, paddingLeft: '1rem' }}>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff', margin: 0 }}>
              {currentMode.name} Search
            </h1>
            <p style={{ fontSize: '1rem', color: '#888', margin: '0.25rem 0 0 0' }}>
              {currentMode.description}
            </p>
            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#888' }}>
              Speed: <span style={{ color: '#fff' }}>{currentMode.time}</span> | Cost: <span style={{ color: '#fff' }}>{currentMode.cost}</span>
            </div>
          </div>
          
          {/* Placeholder for search results */}
          <div style={{ minHeight: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
            <p style={{ color: '#888' }}>Search results will appear here...</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SearchPage; 