"use client"

import React from 'react';
import { usePersona } from '../../contexts/PersonaContext';
import { Plus, Brain, Save } from 'lucide-react';

const AgentFactoryPage = () => {
  const { currentPersona } = usePersona();
  const theme = currentPersona.theme;

  return (
    <div>
      <h1 style={{ fontSize: '2rem', fontWeight: 700, color: '#fff', marginBottom: '0.5rem' }}>
        Agent Factory
      </h1>
      <p style={{ fontSize: '1rem', color: '#888', marginBottom: '2rem' }}>
        Design, create, and manage your AI agents and personas.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem' }}>
        {/* Left Column: Create/Select */}
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#fff', marginBottom: '1rem', borderLeft: `3px solid ${theme.primary}`, paddingLeft: '0.75rem' }}>
            Manage Personas
          </h2>
          <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem' }}>
            <p style={{ color: '#888', fontSize: '0.875rem', marginTop: 0 }}>Persona management UI coming soon...</p>
            <button style={{
              width: '100%',
              marginTop: '1rem',
              padding: '0.75rem',
              borderRadius: '8px',
              border: `1px solid ${theme.border}`,
              background: theme.background,
              color: theme.text,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem'
            }}>
              <Plus size={16} />
              Create New Persona
            </button>
          </div>

          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: '#fff', marginBottom: '1rem', borderLeft: `3px solid ${theme.primary}`, paddingLeft: '0.75rem' }}>
            Manage Agents
          </h2>
          <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '1.5rem' }}>
            <p style={{ color: '#888', fontSize: '0.875rem', marginTop: 0 }}>Agent selection UI coming soon...</p>
            <button style={{
              width: '100%',
              marginTop: '1rem',
              padding: '0.75rem',
              borderRadius: '8px',
              border: `1px solid ${theme.border}`,
              background: theme.background,
              color: theme.text,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem'
            }}>
              <Plus size={16} />
              Create New Agent
            </button>
          </div>
        </div>

        {/* Right Column: Editor */}
        <div style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', padding: '2rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: '#fff', marginBottom: '0.5rem' }}>
            Agent Designer
          </h2>
          <p style={{ color: '#888', marginBottom: '2rem' }}>Configure the agent's properties and capabilities.</p>

          <form>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', color: '#888', marginBottom: '0.5rem', fontSize: '0.875rem' }}>Agent Name</label>
                <input type="text" placeholder="e.g., Financial Analyst" style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.05)', color: '#fff' }} />
              </div>
              <div>
                <label style={{ display: 'block', color: '#888', marginBottom: '0.5rem', fontSize: '0.875rem' }}>Assigned Persona</label>
                <select style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.05)', color: '#fff' }}>
                  <option>Cherry</option>
                  <option>Sophia</option>
                  <option>Karen</option>
                </select>
              </div>
            </div>

            <div style={{ marginTop: '1.5rem' }}>
              <label style={{ display: 'block', color: '#888', marginBottom: '0.5rem', fontSize: '0.875rem' }}>Description</label>
              <textarea placeholder="A brief description of the agent's role and function." style={{ width: '100%', minHeight: '80px', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(255,255,255,0.05)', color: '#fff' }}></textarea>
            </div>

            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#fff', marginBottom: '1rem' }}>Capabilities</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                {['Web Research', 'Data Analysis', 'Code Execution', 'Tool Usage', 'Self-Correction', 'Long-term Memory'].map(cap => (
                  <label key={cap} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: '8px' }}>
                    <input type="checkbox" style={{ accentColor: theme.primary }} />
                    <span>{cap}</span>
                  </label>
                ))}
              </div>
            </div>

            <div style={{ marginTop: '2rem' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#fff', marginBottom: '1rem' }}>Tools & Integrations</h3>
               <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '1.5rem' }}>
                 <p style={{ color: '#888', fontSize: '0.875rem', margin: '0 auto', textAlign: 'center' }}>Tool selection UI coming soon...</p>
               </div>
            </div>

            <div style={{ marginTop: '2.5rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
              <button type="submit" style={{
                padding: '0.75rem 1.5rem',
                borderRadius: '8px',
                border: 'none',
                background: `linear-gradient(135deg, ${theme.primary} 0%, ${theme.secondary} 100%)`,
                color: '#fff',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: 600
              }}>
                <Save size={16} />
                Save Agent
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AgentFactoryPage; 