import React from 'react';
import { Sparkles, Brain, Zap } from 'lucide-react';
import { Button } from '../../ui/button';
import { SearchMode } from './index';

interface SearchModeSelectorProps {
  searchMode: SearchMode;
  setSearchMode: (mode: SearchMode) => void;
}

export const SearchModeSelector: React.FC<SearchModeSelectorProps> = ({
  searchMode,
  setSearchMode,
}) => {
  const searchModes = [
    { 
      id: 'creative' as SearchMode, 
      label: 'Creative', 
      icon: Sparkles, 
      description: 'Fast, creative responses with innovative solutions' 
    },
    { 
      id: 'deep' as SearchMode, 
      label: 'Deep', 
      icon: Brain, 
      description: 'Thorough analysis with detailed insights' 
    },
    { 
      id: 'super_deep' as SearchMode, 
      label: 'Super Deep', 
      icon: Zap, 
      description: 'Comprehensive research with exhaustive coverage' 
    },
  ];

  return (
    <div>
      <div className="flex gap-2">
        {searchModes.map((mode) => (
          <Button
            key={mode.id}
            variant="outline"
            size="sm"
            onClick={() => setSearchMode(mode.id)}
            className={searchMode === mode.id ? 'orchestrator-btn-outline active' : 'orchestrator-btn-outline'}
          >
            <mode.icon className="w-4 h-4 mr-2" />
            {mode.label}
          </Button>
        ))}
      </div>
      
      {/* Mode Description */}
      <div className="mt-2">
        <p className="text-xs" style={{ color: '#b89d9d' }}>
          {searchModes.find(m => m.id === searchMode)?.description}
        </p>
      </div>
    </div>
  );
};