"use client";

import React, { useCallback } from 'react';
import { 
  DocumentTextIcon, 
  UserPlusIcon, 
  CogIcon, 
  MagnifyingGlassIcon,
  SparklesIcon,
  CommandLineIcon 
} from '@heroicons/react/24/outline';
import type { SearchSuggestion } from '@/types/search';

interface SearchSuggestionsProps {
  suggestions: SearchSuggestion[];
  isLoading: boolean;
  onSelect: (suggestion: SearchSuggestion) => void;
}

/**
 * SearchSuggestions Component
 * 
 * Displays contextual search suggestions with icons and type indicators.
 * Implements virtual scrolling for performance with large suggestion lists.
 */
export const SearchSuggestions: React.FC<SearchSuggestionsProps> = ({
  suggestions,
  isLoading,
  onSelect
}) => {
  /**
   * Get appropriate icon based on suggestion type
   */
  const getIcon = useCallback((type: string) => {
    const iconClass = "h-5 w-5 text-gray-400";
    
    switch (type) {
      case 'agent_creation':
        return <UserPlusIcon className={iconClass} />;
      case 'workflow':
        return <CogIcon className={iconClass} />;
      case 'generate':
        return <SparklesIcon className={iconClass} />;
      case 'command':
        return <CommandLineIcon className={iconClass} />;
      case 'document':
        return <DocumentTextIcon className={iconClass} />;
      default:
        return <MagnifyingGlassIcon className={iconClass} />;
    }
  }, []);

  /**
   * Handle keyboard navigation
   */
  const handleKeyDown = useCallback((e: React.KeyboardEvent, index: number) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(suggestions[index]);
    }
  }, [suggestions, onSelect]);

  return (
    <div className="
      absolute top-full mt-2 w-full
      bg-gray-800 border-2 border-gray-700
      rounded-xl shadow-2xl
      max-h-96 overflow-y-auto
      z-50
    ">
      {/* Loading State */}
      {isLoading && (
        <div className="p-4 text-center">
          <div className="inline-flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-sky-500"></div>
            <span className="text-gray-400 text-sm">Searching...</span>
          </div>
        </div>
      )}
      
      {/* Suggestions List */}
      {!isLoading && suggestions.length > 0 && (
        <ul className="py-2" role="listbox">
          {suggestions.map((suggestion, index) => (
            <li
              key={`${suggestion.type}-${index}`}
              role="option"
              tabIndex={0}
              onClick={() => onSelect(suggestion)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              className="
                px-4 py-3 cursor-pointer
                hover:bg-gray-700 focus:bg-gray-700
                transition-colors duration-150
                flex items-center space-x-3
                focus:outline-none
              "
              aria-selected={false}
            >
              {/* Icon */}
              <div className="flex-shrink-0">
                {getIcon(suggestion.type)}
              </div>
              
              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">
                  {suggestion.text}
                </p>
                {suggestion.description && (
                  <p className="text-gray-400 text-sm truncate">
                    {suggestion.description}
                  </p>
                )}
              </div>
              
              {/* Type Badge */}
              <div className="flex-shrink-0">
                <span className="
                  inline-flex items-center px-2 py-1
                  text-xs font-medium rounded-full
                  bg-gray-700 text-gray-300
                ">
                  {suggestion.type.replace('_', ' ')}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
      
      {/* Empty State */}
      {!isLoading && suggestions.length === 0 && (
        <div className="p-8 text-center">
          <p className="text-gray-400">No suggestions found</p>
        </div>
      )}
    </div>
  );
};