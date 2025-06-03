import React, { useState } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { SearchModeSelector } from './SearchModeSelector';
import { usePersona } from '../../contexts/PersonaContext';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: (query: string, mode: string) => void;
  placeholder?: string;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  onSearch,
  placeholder = 'Search...'
}) => {
  const { accentColor } = usePersona();
  const [selectedMode, setSelectedMode] = useState('normal');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) {
      onSearch(value, selectedMode);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full px-4 py-4 pr-12 bg-background-input border border-background-secondary rounded-lg text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 transition-all"
          style={{ '--tw-ring-color': `${accentColor}33` } as React.CSSProperties}
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded-full transition-colors"
          style={{ backgroundColor: accentColor }}
        >
          <MagnifyingGlassIcon className="w-5 h-5 text-white" />
        </button>
      </div>
      
      <SearchModeSelector
        selectedMode={selectedMode}
        onModeChange={setSelectedMode}
      />
    </form>
  );
};
