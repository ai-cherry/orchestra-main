import React from 'react';
import { Link } from '@tanstack/react-router';
import { Home, Brain, Workflow, Settings, MessageSquare, FileText, Zap } from 'lucide-react'; // Example icons
import DomainSwitcher from './DomainSwitcher'; // Step 1: Import DomainSwitcher
import usePersonaStore from '../../store/personaStore'; // Step 2: Import usePersonaStore

interface SidebarProps {
  open: boolean;
  setOpen: (open: boolean) => void;
}

// Step 5 (part 1): Add isDomainAdaptive flag
const navItemsConfig = [
  { href: '/', label: 'Dashboard', icon: Home, isDomainAdaptive: false },
  { href: '/agents', label: 'Agents', icon: MessageSquare, isDomainAdaptive: true },
  { href: '/personas', label: 'Personas', icon: Brain, isDomainAdaptive: false },
  { href: '/workflows', label: 'Workflows', icon: Workflow, isDomainAdaptive: true },
  { href: '/integrations', label: 'Integrations', icon: Zap, isDomainAdaptive: false },
  { href: '/resources', label: 'Resources', icon: FileText, isDomainAdaptive: true },
  { href: '/logs', label: 'Logs', icon: FileText, isDomainAdaptive: false },
  { href: '/settings', label: 'Settings', icon: Settings, isDomainAdaptive: false },
];

const Sidebar: React.FC<SidebarProps> = ({ open, setOpen }) => {
  // Step 3: Get currentDomain from usePersonaStore
  const currentDomainName = usePersonaStore((state) => state.getCurrentDomain());

  const sidebarBaseStyle = "bg-[#1F2937] text-gray-200 flex flex-col transition-all duration-300 ease-in-out";
  const openStyle = "w-64 p-4";
  const closedStyle = "w-16 p-4 items-center"; // Icon-only view

  return (
    <div className={`${sidebarBaseStyle} ${open ? openStyle : closedStyle}`}>
      <div className="flex items-center mb-8">
        {/* Placeholder for Logo, will be part of TopBar or here if sidebar is persistent */}
        {open && <h1 className="text-xl font-bold text-[var(--theme-accent-primary)]">Orchestra</h1>}
      </div>

      {/* Step 4: Render DomainSwitcher */}
      {open && (
        <div className="mb-4">
          <DomainSwitcher />
        </div>
      )}

      <nav className="flex-1 space-y-2">
        {/* Step 5 (part 2): Modify navItems rendering for adaptive labels */}
        {navItemsConfig.map((item) => {
          let displayLabel = item.label;
          if (open && item.isDomainAdaptive && currentDomainName && currentDomainName.toLowerCase() !== 'all' /* Assuming 'all' might be a general domain name */) {
            // Capitalize first letter of domainName
            const capitalizedDomain = currentDomainName.charAt(0).toUpperCase() + currentDomainName.slice(1);
            displayLabel = `${capitalizedDomain} ${item.label}`;
          }

          return (
            <Link
              key={item.label} // Using original label as key for stability
              to={item.href}
              className="flex items-center p-2 rounded-md hover:bg-gray-700 hover:text-[var(--theme-accent-primary)] aria-[current=page]:bg-[var(--theme-accent-primary)] aria-[current=page]:text-[var(--theme-accent-text)]"
              activeProps={{ className: "bg-[var(--theme-accent-primary)] text-[var(--theme-accent-text)]" }}
              activeOptions={{ exact: item.href === '/' }}
              title={open ? displayLabel : item.label} // Show full label on hover when closed
            >
              <item.icon className={`mr-3 h-6 w-6 ${!open && "mx-auto"}`} />
              {open && <span>{displayLabel}</span>}
            </Link>
          );
        })}
      </nav>
      <button
        onClick={() => setOpen(!open)}
        className="mt-auto p-2 text-gray-400 hover:text-white focus:outline-none md:hidden" // Only show toggle on smaller screens for now
      >
        {open ? "Collapse" : "Expand"}
      </button>
    </div>
  );
};

export default Sidebar;
