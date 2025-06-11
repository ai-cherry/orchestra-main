import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { usePersona } from '../../contexts/PersonaContext';
import { Home, MessageSquare, Users, Building, Database, Search, Menu, X, ChevronDown } from 'lucide-react';

// Persona-specific configurations
const personas = {
  cherry: {
    name: 'Cherry',
    icon: '🍒',
    theme: {
      primary: '#D92626', // A real red
      secondary: '#F15A5A',
      background: 'rgba(217, 38, 38, 0.1)',
      border: 'rgba(217, 38, 38, 0.3)',
      text: '#F15A5A'
    }
  },
  sophia: {
    name: 'Sophia',
    icon: '💼',
    theme: {
      primary: '#3B82F6',
      secondary: '#60A5FA',
      background: 'rgba(59, 130, 246, 0.1)',
      border: 'rgba(59, 130, 246, 0.3)',
      text: '#60A5FA'
    }
  },
  karen: {
    name: 'Karen',
    icon: '🔬',
    theme: {
      primary: '#10B981',
      secondary: '#34D399',
      background: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.3)',
      text: '#34D399'
    }
  },
  master: {
    name: 'Master',
    icon: '⚡',
    theme: {
      primary: '#F59E0B',
      secondary: '#FBBF24',
      background: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.3)',
      text: '#FBBF24'
    }
  }
};

const navItems = [
  { path: '/', label: 'Search', icon: Search },
  { path: '/intelligence-hub', label: 'Intelligence Hub', icon: MessageSquare },
  { path: '/agent-swarm', label: 'Agent Swarm', icon: Users },
  { path: '/agent-factory', label: 'Agent Factory', icon: Building },
  { path: '/business-tools', label: 'Business Tools', icon: Database },
];

const MainLayout = ({ children }) => {
  const { personas: personaContext, currentPersona, setActivePersona } = usePersona();
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isPersonaDropdownOpen, setPersonaDropdownOpen] = useState(false);
  const location = useLocation();

  const theme = currentPersona.theme;

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)',
      color: '#ffffff',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      <div style={{ display: 'flex' }}>
        {/* Sidebar */}
        <aside style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '280px',
          height: '100vh',
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(10px)',
          borderRight: `1px solid ${theme.border}`,
          transition: 'left 0.3s ease-in-out',
          zIndex: 100
          // Add logic for mobile sidebar if needed
        }}>
          <div style={{ padding: '1.5rem', borderBottom: `1px solid ${theme.border}` }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ fontSize: '2.5rem' }}>🍒</span>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0, color: theme.primary }}>
                  Cherry AI
                </h2>
                <p style={{ fontSize: '0.875rem', color: '#888', margin: 0 }}>Orchestrator</p>
              </div>
            </div>
          </div>
          <nav style={{ padding: '1.5rem' }}>
            {navItems.map(item => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    textDecoration: 'none',
                    marginBottom: '0.5rem',
                    color: isActive ? '#fff' : '#888',
                    background: isActive ? theme.background : 'transparent',
                    border: isActive ? `1px solid ${theme.border}` : '1px solid transparent',
                    transition: 'all 0.2s ease-in-out'
                  }}
                  onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)'; }}
                  onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = 'transparent'; }}
                >
                  <item.icon size={20} />
                  <span style={{ fontWeight: 500 }}>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <div style={{ flex: 1, marginLeft: '280px', transition: 'margin-left 0.3s ease-in-out' }}>
          {/* Header */}
          <header style={{
            position: 'sticky',
            top: 0,
            padding: '1.5rem',
            background: 'rgba(10, 10, 10, 0.5)',
            backdropFilter: 'blur(10px)',
            zIndex: 50,
            borderBottom: `1px solid ${theme.border}`
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1.5rem' }}>
              {/* Universal Search Bar */}
              <div style={{ position: 'relative', flex: 1 }}>
                <Search
                  size={20}
                  style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: '#888' }}
                />
                <input
                  type="text"
                  placeholder={`Search everything with ${currentPersona.name}...`}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem 1rem 0.75rem 3rem',
                    borderRadius: '8px',
                    border: `1px solid rgba(255, 255, 255, 0.1)`,
                    background: 'rgba(255, 255, 255, 0.05)',
                    color: '#fff',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={(e) => e.target.style.borderColor = theme.primary}
                  onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)'}
                />
              </div>

              {/* Persona Switcher */}
              <div style={{ position: 'relative' }}>
                <button
                  onClick={() => setPersonaDropdownOpen(!isPersonaDropdownOpen)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    border: `1px solid ${theme.border}`,
                    background: theme.background,
                    color: '#fff',
                    cursor: 'pointer'
                  }}
                >
                  <span style={{ fontSize: '1.25rem' }}>{currentPersona.icon}</span>
                  <span style={{ fontWeight: 600 }}>{currentPersona.name}</span>
                  <ChevronDown size={16} style={{ transform: isPersonaDropdownOpen ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }}/>
                </button>

                {/* Dropdown Menu */}
                {isPersonaDropdownOpen && (
                  <div style={{
                    position: 'absolute',
                    top: '100%',
                    right: 0,
                    marginTop: '0.5rem',
                    width: '250px',
                    background: 'rgba(20,20,20,0.9)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    padding: '0.5rem',
                    zIndex: 110,
                  }}>
                    {Object.values(personas).map(persona => (
                      <button
                        key={persona.id}
                        onClick={() => {
                          setActivePersona(persona.id);
                          setPersonaDropdownOpen(false);
                        }}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.75rem',
                          width: '100%',
                          padding: '0.75rem',
                          borderRadius: '6px',
                          border: 'none',
                          background: currentPersona.id === persona.id ? persona.theme.background : 'transparent',
                          color: '#fff',
                          cursor: 'pointer',
                          textAlign: 'left'
                        }}
                        onMouseEnter={(e) => { if(currentPersona.id !== persona.id) e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)' }}
                        onMouseLeave={(e) => { if(currentPersona.id !== persona.id) e.currentTarget.style.backgroundColor = 'transparent' }}
                      >
                        <span style={{ fontSize: '1.25rem' }}>{persona.icon}</span>
                        <span style={{ fontWeight: 600, color: persona.theme.text }}>{persona.name}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </header>

          <main style={{ padding: '1.5rem' }}>
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};

export default MainLayout; 