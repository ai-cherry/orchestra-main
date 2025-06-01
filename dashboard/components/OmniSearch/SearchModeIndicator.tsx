"use client";

import React from 'react';
import { 
  MagnifyingGlassIcon, 
  SparklesIcon, 
  CommandLineIcon,
  DocumentTextIcon 
} from '@heroicons/react/24/outline';
import type { SearchMode, DetectedIntent } from '@/types/search';

interface SearchModeIndicatorProps {
  mode: SearchMode;
  detectedIntent?: DetectedIntent | null;
}

/**
 * SearchModeIndicator Component
 * 
 * Visual indicator showing the current search mode and detected intent.
 * Helps users understand how their query will be processed.
 */
export const SearchModeIndicator: React.FC<SearchModeIndicatorProps> = ({
  mode,
  detectedIntent
}) => {
  /**
   * Get display information based on mode or detected intent
   */
  const getModeInfo = () => {
    // If we have a detected intent, show that instead of mode
    if (detectedIntent) {
      switch (detectedIntent.type) {
        case 'agent_creation':
          return {
            icon: <SparklesIcon className="h-4 w-4" />,
            label: 'Create Agent',
            color: 'text-purple-400'
          };
        case 'search':
          return {
            icon: <MagnifyingGlassIcon className="h-4 w-4" />,
            label: 'Search',
            color: 'text-blue-400'
          };
        case 'generate':
          return {
            icon: <SparklesIcon className="h-4 w-4" />,
            label: 'Generate',
            color: 'text-green-400'
          };
        case 'command':
          return {
            icon: <CommandLineIcon className="h-4 w-4" />,
            label: 'Command',
            color: 'text-orange-400'
          };
        default:
          return {
            icon: <DocumentTextIcon className="h-4 w-4" />,
            label: 'Auto',
            color: 'text-gray-400'
          };
      }
    }
    
    // Default to showing the mode
    switch (mode) {
      case 'search':
        return {
          icon: <MagnifyingGlassIcon className="h-4 w-4" />,
          label: 'Search',
          color: 'text-blue-400'
        };
      case 'generate':
        return {
          icon: <SparklesIcon className="h-4 w-4" />,
          label: 'Generate',
          color: 'text-green-400'
        };
      case 'command':
        return {
          icon: <CommandLineIcon className="h-4 w-4" />,
          label: 'Command',
          color: 'text-orange-400'
        };
      default:
        return {
          icon: <DocumentTextIcon className="h-4 w-4" />,
          label: 'Auto',
          color: 'text-gray-400'
        };
    }
  };

  const modeInfo = getModeInfo();
  
  // Show confidence indicator if we have detected intent
  const showConfidence = detectedIntent && detectedIntent.confidence < 0.8;

  return (
    <div 
      id="search-mode-indicator"
      className={`
        flex items-center space-x-1 px-2 py-1
        rounded-lg bg-gray-700
        transition-all duration-200
        ${modeInfo.color}
      `}
      role="status"
      aria-live="polite"
    >
      {/* Icon */}
      <div className="flex-shrink-0">
        {modeInfo.icon}
      </div>
      
      {/* Label */}
      <span className="text-xs font-medium">
        {modeInfo.label}
      </span>
      
      {/* Confidence Indicator */}
      {showConfidence && (
        <span className="text-xs opacity-60">
          ({Math.round((detectedIntent?.confidence || 0) * 100)}%)
        </span>
      )}
    </div>
  );
};