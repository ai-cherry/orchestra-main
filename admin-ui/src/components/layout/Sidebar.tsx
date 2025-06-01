import React from 'react';
import { Link } from '@tanstack/react-router';
import { Home, Brain, Workflow, Settings, MessageSquare, FileText, Zap, 
  Heart, Activity, Users, DollarSign, CreditCard, FileCheck, 
  Pill, TestTube, Shield } from 'lucide-react';
import usePersonaStore from '../../store/personaStore';

interface SidebarProps {
  open: boolean;
  setOpen: (open: boolean) => void;
}

// Base navigation items available for all personas
const baseNavItems = [
  { href: '/', label: 'Dashboard', icon: Home },
  { href: '/agents', label: 'Agents', icon: MessageSquare },
  { href: '/workflows', label: 'Workflows', icon: Workflow },
  { href: '/settings', label: 'Settings', icon: Settings },
];

// Persona-specific navigation items
const personaNavItems = {
  cherry: [
    { href: '/health', label: 'Health Tracker', icon: Heart },
    { href: '/habits', label: 'Habit Coach', icon: Activity },
    { href: '/social', label: 'Social Circle', icon: Users },
  ],
  sophia: [
    { href: '/transactions', label: 'Transactions', icon: DollarSign },
    { href: '/compliance', label: 'Compliance', icon: FileCheck },
    { href: '/payments', label: 'Payment Systems', icon: CreditCard },
  ],
  karen: [
    { href: '/clinical', label: 'Clinical Trials', icon: TestTube },
    { href: '/pharmacy', label: 'Pharmacy Ops', icon: Pill },
    { href: '/regulatory', label: 'Regulatory', icon: Shield },
  ],
};

const Sidebar: React.FC<SidebarProps> = ({ open, setOpen }) => {
  const { personas, activePersonaId, setActivePersona, getCurrentPersona } = usePersonaStore();
  const currentPersona = getCurrentPersona();

  // Get navigation items based on active persona
  const getNavItems = () => {
    const items = [...baseNavItems];
    
    if (currentPersona && personaNavItems[currentPersona.id as keyof typeof personaNavItems]) {
      // Insert persona-specific items after Dashboard but before Settings
      const settingsIndex = items.findIndex(item => item.href === '/settings');
      items.splice(settingsIndex, 0, ...personaNavItems[currentPersona.id as keyof typeof personaNavItems]);
    }
    
    return items;
  };

  const navItems = getNavItems();

  const sidebarBaseStyle = "bg-background dark:bg-gray-900 text-foreground dark:text-gray-200 flex flex-col transition-all duration-300 ease-in-out border-r border-border dark:border-gray-800";
  const openStyle = "w-64 p-4";
  const closedStyle = "w-16 p-4 items-center";

  return (
    <div className={`${sidebarBaseStyle} ${open ? openStyle : closedStyle}`}>
      <div className="flex items-center mb-4">
        {open && <h1 className="text-xl font-bold text-[var(--theme-accent-primary)]">Orchestra</h1>}
      </div>

      {/* Persona Switcher */}
      <div className={`mb-6 ${!open && 'hidden'}`}>
        <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 block">
          Active Persona
        </label>
        <select
          value={activePersonaId || ''}
          onChange={(e) => setActivePersona(e.target.value)}
          className="w-full px-3 py-2 bg-secondary dark:bg-gray-800 text-foreground dark:text-gray-200 rounded-md border border-border dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-[var(--theme-accent-primary)] focus:border-transparent text-sm"
        >
          <option value="">Select Persona</option>
          {personas.map((persona) => (
            <option key={persona.id} value={persona.id}>
              {persona.icon} {persona.name} ({persona.domain})
            </option>
          ))}
        </select>
        {currentPersona && (
          <div className="mt-2 p-2 bg-secondary/50 dark:bg-gray-800/50 rounded-md">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">{currentPersona.icon}</span>
              <div className="flex-1">
                <p className="text-sm font-medium" style={{ color: currentPersona.color }}>
                  {currentPersona.name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {currentPersona.role}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.label}
            to={item.href}
            className="flex items-center p-2 rounded-md hover:bg-secondary dark:hover:bg-gray-800 hover:text-[var(--theme-accent-primary)] transition-colors"
            activeProps={{ 
              className: "bg-[var(--theme-accent-primary)] text-[var(--theme-accent-text)] hover:bg-[var(--theme-accent-primary)] hover:text-[var(--theme-accent-text)]" 
            }}
            activeOptions={{ exact: item.href === '/' }}
          >
            <item.icon className={`h-5 w-5 ${open ? 'mr-3' : 'mx-auto'}`} />
            {open && <span className="text-sm">{item.label}</span>}
          </Link>
        ))}
      </nav>

      {/* Additional nav items */}
      <div className="mt-4 pt-4 border-t border-border dark:border-gray-700 space-y-1">
        <Link
          to="/personas"
          className="flex items-center p-2 rounded-md hover:bg-secondary dark:hover:bg-gray-800 hover:text-[var(--theme-accent-primary)] transition-colors"
          activeProps={{ 
            className: "bg-[var(--theme-accent-primary)] text-[var(--theme-accent-text)] hover:bg-[var(--theme-accent-primary)] hover:text-[var(--theme-accent-text)]" 
          }}
        >
          <Brain className={`h-5 w-5 ${open ? 'mr-3' : 'mx-auto'}`} />
          {open && <span className="text-sm">Personas</span>}
        </Link>
        <Link
          to="/integrations"
          className="flex items-center p-2 rounded-md hover:bg-secondary dark:hover:bg-gray-800 hover:text-[var(--theme-accent-primary)] transition-colors"
          activeProps={{ 
            className: "bg-[var(--theme-accent-primary)] text-[var(--theme-accent-text)] hover:bg-[var(--theme-accent-primary)] hover:text-[var(--theme-accent-text)]" 
          }}
        >
          <Zap className={`h-5 w-5 ${open ? 'mr-3' : 'mx-auto'}`} />
          {open && <span className="text-sm">Integrations</span>}
        </Link>
        <Link
          to="/logs"
          className="flex items-center p-2 rounded-md hover:bg-secondary dark:hover:bg-gray-800 hover:text-[var(--theme-accent-primary)] transition-colors"
          activeProps={{ 
            className: "bg-[var(--theme-accent-primary)] text-[var(--theme-accent-text)] hover:bg-[var(--theme-accent-primary)] hover:text-[var(--theme-accent-text)]" 
          }}
        >
          <FileText className={`h-5 w-5 ${open ? 'mr-3' : 'mx-auto'}`} />
          {open && <span className="text-sm">Logs</span>}
        </Link>
      </div>

      {/* Sidebar toggle */}
      <button
        onClick={() => setOpen(!open)}
        className="mt-4 p-2 text-gray-500 dark:text-gray-400 hover:text-foreground dark:hover:text-gray-200 focus:outline-none transition-colors"
      >
        {open ? "Collapse" : "Expand"}
      </button>
    </div>
  );
};

export default Sidebar;
