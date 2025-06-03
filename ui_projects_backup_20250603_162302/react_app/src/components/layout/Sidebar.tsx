import React from 'react';
import { NavLink } from 'react-router-dom';
import { usePersona } from '../../contexts/PersonaContext';
import {
  HomeIcon,
  MagnifyingGlassIcon,
  BeakerIcon,
  CpuChipIcon,
  ChartBarIcon,
  CogIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Home', href: '/', icon: HomeIcon },
  { name: 'Search', href: '/search', icon: MagnifyingGlassIcon },
  { name: 'Agent Lab', href: '/agent-lab', icon: BeakerIcon },
  { name: 'Orchestrators', href: '/orchestrators', icon: CpuChipIcon },
  { name: 'Monitoring', href: '/monitoring', icon: ChartBarIcon },
  { name: 'Settings', href: '/settings', icon: CogIcon },
];

export const Sidebar: React.FC = () => {
  const { accentColor } = usePersona();
  
  return (
    <div className="flex flex-col w-64 bg-background-secondary border-r border-background-input">
      <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
        <div className="flex items-center flex-shrink-0 px-4">
          <h2 className="text-2xl font-bold" style={{ color: accentColor }}>
            Orchestra AI
          </h2>
        </div>
        <nav className="mt-8 flex-1 px-2 space-y-1">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                  isActive
                    ? 'text-white'
                    : 'text-text-secondary hover:text-text-primary hover:bg-background-input'
                }`
              }
              style={({ isActive }) =>
                isActive ? { backgroundColor: accentColor } : {}
              }
            >
              <item.icon
                className="mr-3 flex-shrink-0 h-6 w-6"
                aria-hidden="true"
              />
              {item.name}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
};
