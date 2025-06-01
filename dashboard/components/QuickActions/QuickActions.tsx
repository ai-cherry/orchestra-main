"use client";

import React, { useMemo } from 'react';
import { 
  UserPlusIcon, 
  CogIcon, 
  MagnifyingGlassIcon,
  SparklesIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  CloudArrowUpIcon
} from '@heroicons/react/24/outline';

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  onClick: () => void;
}

/**
 * QuickActions Component
 * 
 * Displays a grid of context-aware quick action buttons.
 * Optimized for performance with memoization and lazy loading.
 */
export const QuickActions: React.FC = () => {
  /**
   * Define available quick actions
   * Memoized to prevent recreation on every render
   */
  const actions = useMemo<QuickAction[]>(() => [
    {
      id: 'create-agent',
      title: 'Create Agent',
      description: 'Build a new AI agent',
      icon: <UserPlusIcon className="h-6 w-6" />,
      color: 'from-purple-500 to-pink-500',
      onClick: () => {
        window.location.href = '/agents/create';
      }
    },
    {
      id: 'new-workflow',
      title: 'New Workflow',
      description: 'Design automation flow',
      icon: <CogIcon className="h-6 w-6" />,
      color: 'from-blue-500 to-cyan-500',
      onClick: () => {
        window.location.href = '/workflows/new';
      }
    },
    {
      id: 'deep-search',
      title: 'Deep Search',
      description: 'Search across all data',
      icon: <MagnifyingGlassIcon className="h-6 w-6" />,
      color: 'from-green-500 to-emerald-500',
      onClick: () => {
        // Focus search bar with deep search mode
        const searchInput = document.querySelector('input[aria-label="Omnisearch input"]') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
          searchInput.value = '/search ';
        }
      }
    },
    {
      id: 'generate-content',
      title: 'Generate',
      description: 'Create content with AI',
      icon: <SparklesIcon className="h-6 w-6" />,
      color: 'from-yellow-500 to-orange-500',
      onClick: () => {
        window.location.href = '/generate';
      }
    },
    {
      id: 'chat-assistant',
      title: 'Chat',
      description: 'Talk with AI assistant',
      icon: <ChatBubbleLeftRightIcon className="h-6 w-6" />,
      color: 'from-indigo-500 to-purple-500',
      onClick: () => {
        window.location.href = '/chat';
      }
    },
    {
      id: 'view-analytics',
      title: 'Analytics',
      description: 'View system metrics',
      icon: <ChartBarIcon className="h-6 w-6" />,
      color: 'from-red-500 to-pink-500',
      onClick: () => {
        window.location.href = '/analytics';
      }
    },
    {
      id: 'manage-docs',
      title: 'Documents',
      description: 'Manage knowledge base',
      icon: <DocumentTextIcon className="h-6 w-6" />,
      color: 'from-teal-500 to-green-500',
      onClick: () => {
        window.location.href = '/documents';
      }
    },
    {
      id: 'upload-data',
      title: 'Upload',
      description: 'Import data sources',
      icon: <CloudArrowUpIcon className="h-6 w-6" />,
      color: 'from-gray-500 to-gray-600',
      onClick: () => {
        window.location.href = '/upload';
      }
    }
  ], []);

  /**
   * Handle keyboard navigation
   */
  const handleKeyDown = (e: React.KeyboardEvent, action: QuickAction) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      action.onClick();
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold text-white mb-6">Quick Actions</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {actions.map((action) => (
          <button
            key={action.id}
            onClick={action.onClick}
            onKeyDown={(e) => handleKeyDown(e, action)}
            className="
              relative group
              p-6 rounded-xl
              bg-gray-800 hover:bg-gray-750
              border-2 border-gray-700 hover:border-gray-600
              transition-all duration-200
              transform hover:scale-105
              focus:outline-none focus:ring-2 focus:ring-sky-500
              overflow-hidden
            "
            aria-label={`${action.title}: ${action.description}`}
          >
            {/* Gradient Background */}
            <div 
              className={`
                absolute inset-0 opacity-0 group-hover:opacity-10
                bg-gradient-to-br ${action.color}
                transition-opacity duration-300
              `}
            />
            
            {/* Content */}
            <div className="relative z-10">
              {/* Icon */}
              <div className={`
                inline-flex p-3 rounded-lg mb-4
                bg-gradient-to-br ${action.color}
                text-white
              `}>
                {action.icon}
              </div>
              
              {/* Text */}
              <h3 className="text-lg font-semibold text-white mb-1">
                {action.title}
              </h3>
              <p className="text-sm text-gray-400">
                {action.description}
              </p>
            </div>
            
            {/* Hover Effect */}
            <div className="
              absolute bottom-0 left-0 right-0 h-1
              bg-gradient-to-r opacity-0 group-hover:opacity-100
              transition-opacity duration-300
            " style={{
              backgroundImage: `linear-gradient(to right, var(--tw-gradient-stops))`,
              '--tw-gradient-from': action.color.split(' ')[1],
              '--tw-gradient-to': action.color.split(' ')[3]
            } as React.CSSProperties} />
          </button>
        ))}
      </div>
    </div>
  );
};