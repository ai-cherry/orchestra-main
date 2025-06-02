import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Dialog } from '@headlessui/react';
import { Command } from '@/types/command';
import { 
  Search,
  Navigation,
  Settings,
  Plus,
  BarChart,
  FileText,
  Zap,
  Home,
  Users,
  Database,
  Cloud,
  Shield
} from 'lucide-react';

interface CommandPaletteProps {
  isOpen?: boolean;
  onClose?: () => void;
}

/**
 * Command Palette component for quick actions and navigation
 * Provides keyboard-driven interface for all major functions
 */
export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen: controlledIsOpen,
  onClose: controlledOnClose
}) => {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  
  // Use controlled state if provided, otherwise use internal state
  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen;
  const onClose = controlledOnClose || (() => setInternalIsOpen(false));
  
  /**
   * Available commands
   */
  const commands: Command[] = useMemo(() => [
    // Navigation commands
    {
      id: 'nav-dashboard',
      name: 'Go to Dashboard',
      description: 'Navigate to main dashboard',
      icon: Home,
      type: 'navigation' as any,
      shortcut: 'Cmd+D',
      handler: () => {
        window.location.href = '/dashboard';
        onClose();
      },
      category: 'Navigation'
    },
    {
      id: 'nav-research',
      name: 'Research & Analysis',
      description: 'Open research dashboard',
      icon: BarChart,
      type: 'navigation' as any,
      handler: () => {
        window.location.href = '/research';
        onClose();
      },
      category: 'Navigation'
    },
    {
      id: 'nav-agents',
      name: 'Manage Agents',
      description: 'View and configure AI agents',
      icon: Users,
      type: 'navigation' as any,
      handler: () => {
        window.location.href = '/agents';
        onClose();
      },
      category: 'Navigation'
    },
    
    // Creation commands
    {
      id: 'create-research',
      name: 'New Research Project',
      description: 'Start a new research project',
      icon: Plus,
      type: 'creation' as any,
      shortcut: 'Cmd+N',
      handler: () => {
        // TODO: Open new research modal
        console.log('Creating new research project');
        onClose();
      },
      category: 'Create'
    },
    {
      id: 'create-agent',
      name: 'Create Agent',
      description: 'Configure a new AI agent',
      icon: Plus,
      type: 'creation' as any,
      handler: () => {
        // TODO: Open agent creation modal
        console.log('Creating new agent');
        onClose();
      },
      category: 'Create'
    },
    
    // Action commands
    {
      id: 'run-optimization',
      name: 'Optimize Routing',
      description: 'Run LLM routing optimization',
      icon: Zap,
      type: 'action' as any,
      handler: async () => {
        console.log('Running optimization...');
        // TODO: Trigger optimization
        onClose();
      },
      category: 'Actions'
    },
    {
      id: 'generate-report',
      name: 'Generate Report',
      description: 'Create analytics report',
      icon: FileText,
      type: 'action' as any,
      handler: () => {
        console.log('Generating report...');
        // TODO: Generate report
        onClose();
      },
      category: 'Actions'
    },
    
    // Configuration commands
    {
      id: 'config-settings',
      name: 'Settings',
      description: 'Open application settings',
      icon: Settings,
      type: 'configuration' as any,
      shortcut: 'Cmd+,',
      handler: () => {
        window.location.href = '/settings';
        onClose();
      },
      category: 'Configuration'
    },
    {
      id: 'config-models',
      name: 'Configure Models',
      description: 'Manage LLM configurations',
      icon: Database,
      type: 'configuration' as any,
      handler: () => {
        window.location.href = '/settings/models';
        onClose();
      },
      category: 'Configuration'
    },
    {
      id: 'config-security',
      name: 'Security Settings',
      description: 'Manage security and permissions',
      icon: Shield,
      type: 'configuration' as any,
      handler: () => {
        window.location.href = '/settings/security';
        onClose();
      },
      category: 'Configuration'
    }
  ], [onClose]);
  
  /**
   * Filter commands based on search
   */
  const filteredCommands = useMemo(() => {
    if (!search) return commands;
    
    const lowerSearch = search.toLowerCase();
    return commands.filter(cmd =>
      cmd.name.toLowerCase().includes(lowerSearch) ||
      cmd.description.toLowerCase().includes(lowerSearch) ||
      cmd.category?.toLowerCase().includes(lowerSearch)
    );
  }, [commands, search]);
  
  /**
   * Group commands by category
   */
  const groupedCommands = useMemo(() => {
    const groups: Record<string, Command[]> = {};
    
    filteredCommands.forEach(cmd => {
      const category = cmd.category || 'Other';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(cmd);
    });
    
    return groups;
  }, [filteredCommands]);
  
  /**
   * Global keyboard shortcut
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setInternalIsOpen(true);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
  
  /**
   * Handle keyboard navigation
   */
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    const commandCount = filteredCommands.length;
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % commandCount);
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + commandCount) % commandCount);
        break;
        
      case 'Enter':
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].handler();
        }
        break;
        
      case 'Escape':
        onClose();
        break;
    }
  }, [filteredCommands, selectedIndex, onClose]);
  
  /**
   * Reset state when closing
   */
  useEffect(() => {
    if (!isOpen) {
      setSearch('');
      setSelectedIndex(0);
    }
  }, [isOpen]);
  
  return (
    <Dialog
      open={isOpen}
      onClose={onClose}
      className="fixed inset-0 z-50 overflow-y-auto"
    >
      <div className="flex items-center justify-center min-h-screen">
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        
        <div className="relative bg-gray-900 rounded-xl shadow-2xl w-full max-w-2xl 
                        mx-4 border border-gray-800 max-h-[80vh] flex flex-col">
          <div className="flex items-center border-b border-gray-800">
            <Search className="w-5 h-5 text-gray-400 ml-4" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setSelectedIndex(0);
              }}
              onKeyDown={handleKeyDown}
              placeholder="Type a command or search..."
              className="w-full px-4 py-4 bg-transparent text-white placeholder-gray-400 
                         focus:outline-none"
              autoFocus
            />
          </div>
          
          <div className="overflow-y-auto flex-1">
            {Object.entries(groupedCommands).map(([category, categoryCommands]) => (
              <div key={category}>
                <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase">
                  {category}
                </div>
                {categoryCommands.map((command, idx) => {
                  const Icon = command.icon;
                  const globalIndex = filteredCommands.indexOf(command);
                  const isSelected = globalIndex === selectedIndex;
                  
                  return (
                    <button
                      key={command.id}
                      onClick={() => command.handler()}
                      onMouseEnter={() => setSelectedIndex(globalIndex)}
                      className={`w-full px-4 py-3 flex items-center justify-between 
                                 transition-colors ${
                                   isSelected 
                                     ? 'bg-gray-800 text-white' 
                                     : 'hover:bg-gray-800/50 text-gray-300'
                                 }`}
                    >
                      <div className="flex items-center space-x-3">
                        <Icon className={`w-5 h-5 ${
                          isSelected ? 'text-purple-500' : 'text-gray-500'
                        }`} />
                        <div className="text-left">
                          <div className="font-medium">{command.name}</div>
                          <div className="text-sm text-gray-400">
                            {command.description}
                          </div>
                        </div>
                      </div>
                      {command.shortcut && (
                        <kbd className="px-2 py-1 text-xs bg-gray-800 rounded text-gray-400 
                                       border border-gray-700">
                          {command.shortcut}
                        </kbd>
                      )}
                    </button>
                  );
                })}
              </div>
            ))}
            
            {filteredCommands.length === 0 && (
              <div className="px-4 py-8 text-center text-gray-500">
                No commands found
              </div>
            )}
          </div>
          
          <div className="border-t border-gray-800 px-4 py-2 flex items-center 
                          justify-between text-xs text-gray-500">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded border border-gray-700">↑</kbd>
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded border border-gray-700">↓</kbd>
                <span>Navigate</span>
              </span>
              <span className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded border border-gray-700">↵</kbd>
                <span>Select</span>
              </span>
              <span className="flex items-center space-x-1">
                <kbd className="px-1.5 py-0.5 bg-gray-800 rounded border border-gray-700">esc</kbd>
                <span>Close</span>
              </span>
            </div>
            <span>
              {filteredCommands.length} command{filteredCommands.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </div>
    </Dialog>
  );
};