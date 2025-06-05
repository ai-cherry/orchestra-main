import React from 'react';
import { SearchMode } from './HomePage';

interface SearchModeSelectorProps {
  modes: SearchMode[];
  activeMode: string;
  onModeChange: (modeId: string) => void;
  accentColor: string;
}

export const SearchModeSelector: React.FC<SearchModeSelectorProps> = ({
  modes,
  activeMode,
  onModeChange,
  accentColor,
}) => {
  const getActiveModeClasses = (modeId: string) => {
    const isActive = activeMode === modeId;
    
    if (!isActive) {
      return "bg-white/10 text-white/70 hover:bg-white/20 hover:text-white border-white/20";
    }
    
    switch (accentColor) {
      case 'cherry':
        return "bg-gradient-to-r from-cherry-500 to-cherry-600 text-white border-cherry-400 shadow-glow-cherry";
      case 'sophia':
        return "bg-gradient-to-r from-sophia-500 to-sophia-600 text-white border-sophia-400 shadow-glow-sophia";
      case 'karen':
        return "bg-gradient-to-r from-karen-500 to-karen-600 text-white border-karen-400 shadow-glow-karen";
      default:
        return "bg-gradient-to-r from-blue-500 to-blue-600 text-white border-blue-400 shadow-glow";
    }
  };

  const getModeDescription = (mode: SearchMode) => {
    switch (mode.id) {
      case 'normal':
        return 'Balanced responses with standard AI guidelines';
      case 'creative':
        return 'Imaginative, artistic, and out-of-the-box thinking';
      case 'deep':
        return 'Thorough analysis with detailed explanations';
      case 'super-deep':
        return 'Comprehensive research with extensive context';
      case 'uncensored':
        return 'Unrestricted responses without content filtering';
      default:
        return mode.description;
    }
  };

  const getModeIcon = (mode: SearchMode) => {
    return (
      <span className="text-lg mr-2" role="img" aria-label={mode.name}>
        {mode.icon}
      </span>
    );
  };

  return (
    <div className="w-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white mb-2">Search Mode</h3>
        <p className="text-white/60 text-sm">
          Choose how deeply and creatively you want the AI to respond
        </p>
      </div>
      
      {/* Mode Buttons */}
      <div className="flex flex-wrap gap-3 mb-4">
        {modes.map((mode) => (
          <button
            key={mode.id}
            onClick={() => onModeChange(mode.id)}
            className={`
              flex items-center px-4 py-2 rounded-full border-2 font-medium text-sm
              transition-all duration-200 transform hover:scale-105 focus:outline-none
              focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent
              ${getActiveModeClasses(mode.id)}
            `}
            aria-pressed={activeMode === mode.id}
            aria-label={`Select ${mode.name} search mode`}
          >
            {getModeIcon(mode)}
            {mode.name}
            {activeMode === mode.id && (
              <span className="ml-2 text-xs">✓</span>
            )}
          </button>
        ))}
      </div>
      
      {/* Active Mode Description */}
      <div className="bg-white/5 rounded-xl p-4 border border-white/10">
        <div className="flex items-start gap-3">
          <div className="text-2xl">
            {getModeIcon(modes.find(m => m.id === activeMode) || modes[0])}
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-white mb-1">
              {modes.find(m => m.id === activeMode)?.name || 'Normal'} Mode
            </h4>
            <p className="text-white/70 text-sm">
              {getModeDescription(modes.find(m => m.id === activeMode) || modes[0])}
            </p>
          </div>
        </div>
        
        {/* Mode-specific features */}
        <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
          {activeMode === 'normal' && (
            <>
              <div className="flex items-center gap-2 text-white/60">
                <span>⚖️</span>
                <span>Balanced</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>🎯</span>
                <span>Focused</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>⚡</span>
                <span>Fast</span>
              </div>
            </>
          )}
          
          {activeMode === 'creative' && (
            <>
              <div className="flex items-center gap-2 text-white/60">
                <span>🎨</span>
                <span>Artistic</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>💭</span>
                <span>Imaginative</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>🌟</span>
                <span>Innovative</span>
              </div>
            </>
          )}
          
          {activeMode === 'deep' && (
            <>
              <div className="flex items-center gap-2 text-white/60">
                <span>🔍</span>
                <span>Analytical</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>📚</span>
                <span>Detailed</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>🧠</span>
                <span>Thoughtful</span>
              </div>
            </>
          )}
          
          {activeMode === 'super-deep' && (
            <>
              <div className="flex items-center gap-2 text-white/60">
                <span>🔬</span>
                <span>Research-level</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>📖</span>
                <span>Comprehensive</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>🎓</span>
                <span>Academic</span>
              </div>
            </>
          )}
          
          {activeMode === 'uncensored' && (
            <>
              <div className="flex items-center gap-2 text-white/60">
                <span>🚀</span>
                <span>Unrestricted</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>🔓</span>
                <span>Open</span>
              </div>
              <div className="flex items-center gap-2 text-white/60">
                <span>⚠️</span>
                <span>Unfiltered</span>
              </div>
            </>
          )}
        </div>
      </div>
      
      {/* Warning for uncensored mode */}
      {activeMode === 'uncensored' && (
        <div className="mt-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <div className="flex items-center gap-2 text-amber-400 text-sm">
            <span>⚠️</span>
            <span className="font-medium">Uncensored Mode Active</span>
          </div>
          <p className="text-amber-300/80 text-xs mt-1">
            Responses may include unfiltered content. Use responsibly.
          </p>
        </div>
      )}
    </div>
  );
}; 