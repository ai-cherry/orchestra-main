import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import { useNLPProcessor } from '@/hooks/useNLPProcessor';
import { useModelRouter } from '@/hooks/useModelRouter';
import { Mic, Search, X } from 'lucide-react';
import { ProcessedCommand, Suggestion } from '@/types/command';

interface EnhancedOmniSearchProps {
  onCommand: (command: ProcessedCommand) => void;
  className?: string;
}

/**
 * Enhanced OmniSearch component with NLP processing and voice input
 * Provides intelligent command routing and suggestion capabilities
 */
export const EnhancedOmniSearch: React.FC<EnhancedOmniSearchProps> = ({
  onCommand,
  className = ''
}) => {
  const [query, setQuery] = useState('');
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const debouncedQuery = useDebounce(query, 300);
  
  const { processQuery, generateSuggestions, isProcessing } = useNLPProcessor();
  const { routeQuery } = useModelRouter();
  
  // Generate suggestions based on debounced query
  const suggestions = debouncedQuery ? generateSuggestions(debouncedQuery) : [];
  
  /**
   * Handle command submission with error handling
   */
  const handleSubmit = useCallback(async () => {
    if (!debouncedQuery.trim()) return;
    
    try {
      const intent = await processQuery(debouncedQuery);
      const routing = await routeQuery(intent);
      
      onCommand({
        query: debouncedQuery,
        intent,
        routing,
        timestamp: new Date()
      });
      
      // Clear input after successful submission
      setQuery('');
      setSelectedSuggestionIndex(-1);
    } catch (error) {
      console.error('Failed to process command:', error);
      // TODO: Show user-friendly error notification
    }
  }, [debouncedQuery, processQuery, routeQuery, onCommand]);
  
  /**
   * Initialize and handle voice input with proper cleanup
   */
  const handleVoiceInput = useCallback(() => {
    if (!('webkitSpeechRecognition' in window)) {
      console.warn('Speech recognition not supported');
      return;
    }
    
    if (isVoiceActive && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsVoiceActive(false);
      return;
    }
    
    const recognition = new (window as any).webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
      setIsVoiceActive(true);
    };
    
    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0].transcript)
        .join('');
      
      setQuery(transcript);
      
      if (event.results[0].isFinal) {
        handleSubmit();
      }
    };
    
    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsVoiceActive(false);
    };
    
    recognition.onend = () => {
      setIsVoiceActive(false);
      recognitionRef.current = null;
    };
    
    recognitionRef.current = recognition;
    recognition.start();
  }, [isVoiceActive, handleSubmit]);
  
  /**
   * Handle keyboard navigation for suggestions
   */
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0 && suggestions[selectedSuggestionIndex]) {
          setQuery(suggestions[selectedSuggestionIndex].text);
          setSelectedSuggestionIndex(-1);
        }
        handleSubmit();
        break;
        
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => 
          Math.min(prev + 1, suggestions.length - 1)
        );
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => Math.max(prev - 1, -1));
        break;
        
      case 'Escape':
        setSelectedSuggestionIndex(-1);
        inputRef.current?.blur();
        break;
    }
  }, [selectedSuggestionIndex, suggestions, handleSubmit]);
  
  /**
   * Handle suggestion selection
   */
  const handleSuggestionClick = useCallback((suggestion: Suggestion) => {
    setQuery(suggestion.text);
    setSelectedSuggestionIndex(-1);
    handleSubmit();
  }, [handleSubmit]);
  
  /**
   * Clean up voice recognition on unmount
   */
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);
  
  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setTimeout(() => setIsFocused(false), 200)}
            placeholder="Ask anything or type a command..."
            className="w-full pl-10 pr-10 py-2 bg-gray-800 border border-gray-700 rounded-lg 
                     text-white placeholder-gray-400 focus:outline-none focus:border-purple-500
                     transition-colors duration-200"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 
                       text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        
        <button
          onClick={handleVoiceInput}
          className={`p-2 rounded-lg transition-all duration-200 ${
            isVoiceActive 
              ? 'bg-purple-600 shadow-lg shadow-purple-600/50 animate-pulse' 
              : 'bg-gray-700 hover:bg-gray-600'
          }`}
          title={isVoiceActive ? 'Stop recording' : 'Start voice input'}
        >
          <Mic className="w-5 h-5 text-white" />
        </button>
      </div>
      
      {/* Suggestions dropdown */}
      {isFocused && suggestions.length > 0 && (
        <div className="absolute top-full mt-2 w-full bg-gray-800 border border-gray-700 
                        rounded-lg shadow-xl z-50 overflow-hidden">
          {suggestions.map((suggestion, idx) => {
            const Icon = suggestion.icon;
            return (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion)}
                onMouseEnter={() => setSelectedSuggestionIndex(idx)}
                className={`w-full px-4 py-3 text-left hover:bg-gray-700 
                           flex items-center justify-between transition-colors
                           ${selectedSuggestionIndex === idx ? 'bg-gray-700' : ''}`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className="w-5 h-5 text-purple-500" />
                  <span className="text-white">{suggestion.text}</span>
                </div>
                <span className="text-xs text-gray-400">{suggestion.type}</span>
              </button>
            );
          })}
        </div>
      )}
      
      {/* Processing indicator */}
      {isProcessing && (
        <div className="absolute top-full mt-2 left-0 text-sm text-gray-400">
          Processing...
        </div>
      )}
    </div>
  );
};