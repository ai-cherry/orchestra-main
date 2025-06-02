import React from 'react';
import { SearchInput } from './SearchInput';
import { InputModeSelector } from './InputModeSelector';
import { SearchModeSelector } from './SearchModeSelector';
import { Card } from '../../ui/card';

export type SearchMode = 'creative' | 'deep' | 'super_deep';
export type InputMode = 'text' | 'voice' | 'file';

interface SearchInterfaceProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  searchMode: SearchMode;
  setSearchMode: (mode: SearchMode) => void;
  inputMode: InputMode;
  setInputMode: (mode: InputMode) => void;
  onSearch: () => void;
  suggestions: string[];
  onSuggestionClick: (suggestion: string) => void;
}

export const SearchInterface: React.FC<SearchInterfaceProps> = ({
  searchQuery,
  setSearchQuery,
  searchMode,
  setSearchMode,
  inputMode,
  setInputMode,
  onSearch,
  suggestions,
  onSuggestionClick,
}) => {
  return (
    <Card className="orchestrator-card p-6">
      {/* Search Mode Selector */}
      <SearchModeSelector
        searchMode={searchMode}
        setSearchMode={setSearchMode}
      />

      {/* Search Input Area */}
      <div className="mt-6">
        <div className="flex gap-2">
          {/* Input Mode Selector */}
          <InputModeSelector
            inputMode={inputMode}
            setInputMode={setInputMode}
          />

          {/* Search Input */}
          <SearchInput
            inputMode={inputMode}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            onSearch={onSearch}
          />
        </div>
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-medium mb-3" style={{ color: '#b89d9d' }}>
            Suggestions
          </h3>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="orchestrator-suggestion"
                onClick={() => onSuggestionClick(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};