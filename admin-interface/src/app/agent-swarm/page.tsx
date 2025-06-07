"use client"

import React from 'react';
import { usePersona } from '../../contexts/PersonaContext';

const AgentSwarmPage = () => {
  const { currentPersona } = usePersona();
  const theme = currentPersona.theme;

  return (
    <div>
      <h1 style={{ fontSize: '2rem', fontWeight: 700, color: '#fff', marginBottom: '0.5rem' }}>
        Agent Swarm
      </h1>
      <p style={{ fontSize: '1rem', color: '#888', marginBottom: '2rem' }}>
        Monitor and manage your active AI agents, filtered by the <span style={{ color: theme.primary, fontWeight: 500 }}>{currentPersona.name}</span> persona.
      </p>
      <div style={{
        height: '60vh',
        background: 'rgba(0,0,0,0.2)',
        borderRadius: '12px',
        border: `1px solid ${theme.border}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <p style={{ color: '#888' }}>Agent Swarm management interface coming soon...</p>
      </div>
    </div>
  );
};

export default AgentSwarmPage; 