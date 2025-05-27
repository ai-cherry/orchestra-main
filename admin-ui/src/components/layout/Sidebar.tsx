import React from 'react';
import { Link } from '@tanstack/react-router';
import { Home, Brain, Workflow, Settings, BotMessageSquare, FileText, Zap } from 'lucide-react'; // Example icons

interface SidebarProps {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const navItems = [
  { href: '/', label: 'Dashboard', icon: Home },
  { href: '/agents', label: 'Agents', icon: BotMessageSquare },
  { href: '/personas', label: 'Personas', icon: Brain },
  { href: '/workflows', label: 'Workflows', icon: Workflow },
  { href: '/integrations', label: 'Integrations', icon: Zap },
  { href: '/resources', label: 'Resources', icon: FileText },
  { href: '/logs', label: 'Logs', icon: FileText },
  { href: '/settings', label: 'Settings', icon: Settings },
];

const Sidebar: React.FC<SidebarProps> = ({ open, setOpen }) => {
  // Basic styling for now, "tech command center aesthetic" will be refined
  const sidebarBaseStyle = "bg-[#1F2937] text-gray-200 flex flex-col transition-all duration-300 ease-in-out";
  const openStyle = "w-64 p-4";
  const closedStyle = "w-16 p-4 items-center"; // Icon-only view

  return (
    <div className={`${sidebarBaseStyle} ${open ? openStyle : closedStyle}`}>
      <div className="flex items-center mb-8">
        {/* Placeholder for Logo, will be part of TopBar or here if sidebar is persistent */}
        {open && <h1 className="text-xl font-bold text-theme-accent-primary">Orchestra</h1>}
      </div>
      <nav className="flex-1 space-y-2">
        {navItems.map((item) => (
          <Link
            key={item.label}
            to={item.href}
            className="flex items-center p-2 rounded-md hover:bg-gray-700 hover:text-theme-accent-primary aria-[current=page]:bg-theme-accent-primary aria-[current=page]:text-theme-accent-text"
            activeProps={{ className: "bg-theme-accent-primary text-theme-accent-text" }}
            activeOptions={{ exact: item.href === '/' }}
          >
            <item.icon className={`mr-3 h-6 w-6 ${!open && "mx-auto"}`} />
            {open && <span>{item.label}</span>}
          </Link>
        ))}
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
