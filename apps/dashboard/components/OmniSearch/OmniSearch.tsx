"use client";

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { debounce } from 'lodash';
import { SearchIcon, MicrophoneIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { useOmniSearch } from '@/hooks/useOmniSearch';
import { SearchSuggestions } from './SearchSuggestions';
import { SearchModeIndicator } from './SearchModeIndicator';
import type { SearchMode, SearchSuggestion } from '@/types/search';
import type { SpeechRecognitionEvent, SpeechRecognitionErrorEvent } from '@/types/speech';

/**
 * OmniSearch Component
 * 
 * Central search interface with intelligent intent detection, voice input,
 * and contextual suggestions. Optimized for performance with debounced
 * input and lazy-loaded suggestions.
 */
export const OmniSearch: React.FC = () => {
  // State management
  const [query, setQuery] = useState<string>('');
  const [isListening, setIsListening] = useState<boolean>(false);
  const [isFocused, setIsFocused] = useState<boolean>(false);
  const [searchMode, setSearchMode] = useState<SearchMode>('auto');
  
  // Refs for DOM manipulation and voice recognition
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  
  // Custom hook for search functionality
  const {
    suggestions,
    isLoading,
    detectedIntent,
    performSearch,
    clearSuggestions
  } = useOmniSearch();

  /**
   * Debounced search handler to reduce API calls
   * Waits 300ms after user stops typing
   */
  const debouncedSearch = useCallback(
    debounce((searchQuery: string) => {
      if (searchQuery.trim().length > 0) {
        performSearch(searchQuery, searchMode);
      } else {
        clearSuggestions();
      }
    }, 300),
    [searchMode, performSearch, clearSuggestions]
  );

  /**
   * Handle input changes with validation
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value;
    
    // Validate input length
    if (newQuery.length <= 500) {
      setQuery(newQuery);
      debouncedSearch(newQuery);
    }
  };

  /**
   * Handle form submission
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (query.trim()) {
      performSearch(query, searchMode, true); // true = execute search
    }
  };

  /**
   * Toggle voice input
   */
  const toggleVoiceInput = useCallback(() => {
    setIsListening(prev => !prev);
    
    if (!isListening) {
      // Start voice recognition
      startVoiceRecognition();
    } else {
      // Stop voice recognition
      stopVoiceRecognition();
    }
  }, [isListening]);

  /**
   * Start voice recognition using Web Speech API
   */
  const startVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = Array.from(event.results)
          .map(result => result[0])
          .map(result => result.transcript)
          .join('');
        
        setQuery(transcript);
        debouncedSearch(transcript);
      };
      
      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        recognitionRef.current = null;
      };
      
      recognition.onend = () => {
        setIsListening(false);
        recognitionRef.current = null;
      };
      
      // Store reference for cleanup
      recognitionRef.current = recognition;
      recognition.start();
    } else {
      console.warn('Speech recognition not supported');
      setIsListening(false);
    }
  };

  /**
   * Stop voice recognition
   */
  const stopVoiceRecognition = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
  };

  /**
   * Handle click outside to close suggestions
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  /**
   * Handle keyboard shortcuts
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K to focus search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
      
      // Escape to blur
      if (e.key === 'Escape' && isFocused) {
        inputRef.current?.blur();
        setIsFocused(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isFocused]);

  // Cleanup voice recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    };
  }, []);

  return (
    <div 
      ref={containerRef}
      className="relative w-full max-w-4xl mx-auto"
    >
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          {/* Search Icon */}
          <div className="absolute left-4 pointer-events-none">
            <SearchIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          {/* Input Field */}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={() => setIsFocused(true)}
            placeholder="Search, create, or ask anything..."
            className={`
              w-full pl-12 pr-32 py-4 
              text-lg font-medium
              bg-gray-800 text-white
              border-2 border-gray-700
              rounded-xl
              focus:outline-none focus:border-sky-500
              transition-all duration-200
              ${isListening ? 'border-red-500' : ''}
            `}
            aria-label="Omnisearch input"
            aria-describedby="search-mode-indicator"
            autoComplete="off"
            spellCheck="false"
          />
          
          {/* Action Buttons */}
          <div className="absolute right-2 flex items-center space-x-2">
            {/* Search Mode Indicator */}
            <SearchModeIndicator 
              mode={searchMode}
              detectedIntent={detectedIntent}
            />
            
            {/* Voice Input Button */}
            <button
              type="button"
              onClick={toggleVoiceInput}
              className={`
                p-2 rounded-lg
                transition-all duration-200
                ${isListening 
                  ? 'bg-red-500 text-white animate-pulse' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }
              `}
              aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
            >
              <MicrophoneIcon className="h-5 w-5" />
            </button>
            
            {/* Generate Button */}
            <button
              type="submit"
              className="
                p-2 rounded-lg
                bg-sky-600 text-white
                hover:bg-sky-700
                transition-all duration-200
                flex items-center space-x-1
              "
              aria-label="Execute search"
            >
              <SparklesIcon className="h-5 w-5" />
              <span className="text-sm font-medium">Generate</span>
            </button>
          </div>
        </div>
      </form>
      
      {/* Search Suggestions Dropdown */}
      {isFocused && (suggestions.length > 0 || isLoading) && (
        <SearchSuggestions
          suggestions={suggestions}
          isLoading={isLoading}
          onSelect={(suggestion) => {
            setQuery(suggestion.text);
            performSearch(suggestion.text, searchMode, true);
            setIsFocused(false);
          }}
        />
      )}
    </div>
  );
};