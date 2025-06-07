import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, MessageSquare, Users, Building, Database, Search } from 'lucide-react';

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/intelligence-hub', label: 'Intelligence Hub', icon: MessageSquare },
    { path: '/agent-swarm', label: 'Agent Swarm', icon: Users },
    { path: '/business-tools', label: 'Business Tools', icon: Building },
    { path: '/data-pipeline', label: 'Data Pipeline', icon: Database },
    { path: '/search-orchestrator', label: 'Search Orchestrator', icon: Search }
  ];

  return (
    <nav style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      zIndex: 100,
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(220, 38, 127, 0.3)',
      borderRadius: '12px',
      padding: '8px'
    }}>
      <div style={{ display: 'flex', gap: '4px' }}>
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              style={{
                textDecoration: 'none',
                background: isActive 
                  ? 'linear-gradient(135deg, #dc267f 0%, #ff6b9d 100%)'
                  : 'rgba(255, 255, 255, 0.05)',
                border: isActive 
                  ? 'none'
                  : '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '8px',
                padding: '8px 12px',
                color: isActive ? '#ffffff' : '#888',
                fontSize: '12px',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                minWidth: '120px',
                justifyContent: 'center'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)';
                  e.currentTarget.style.color = '#ffffff';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                  e.currentTarget.style.color = '#888';
                }
              }}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default Navigation; 