"use client";

import React, { memo } from 'react';
import { UserIcon, CpuChipIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import type { Message as MessageType } from '@/types/conversation';

interface MessageProps {
  message: MessageType;
}

/**
 * Message Component
 * 
 * Renders individual messages with appropriate styling based on role.
 * Memoized for performance optimization in long conversations.
 */
export const Message: React.FC<MessageProps> = memo(({ message }) => {
  /**
   * Get icon based on message role
   */
  const getIcon = () => {
    if (message.isError) {
      return <ExclamationTriangleIcon className="h-6 w-6 text-red-500" />;
    }
    
    switch (message.role) {
      case 'user':
        return <UserIcon className="h-6 w-6 text-blue-500" />;
      case 'assistant':
        return <CpuChipIcon className="h-6 w-6 text-green-500" />;
      default:
        return <CpuChipIcon className="h-6 w-6 text-gray-500" />;
    }
  };

  /**
   * Get background color based on role
   */
  const getBackgroundColor = () => {
    if (message.isError) return 'bg-red-900/20 border-red-800';
    
    switch (message.role) {
      case 'user':
        return 'bg-blue-900/20 border-blue-800';
      case 'assistant':
        return 'bg-gray-800 border-gray-700';
      default:
        return 'bg-gray-800 border-gray-700';
    }
  };

  /**
   * Format timestamp for display
   */
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  /**
   * Render message content with markdown support
   */
  const renderContent = () => {
    // Simple markdown rendering (can be enhanced with a proper markdown library)
    const lines = message.content.split('\n');
    
    return lines.map((line, index) => {
      // Code blocks
      if (line.startsWith('```')) {
        return null; // Skip code fence markers
      }
      
      // Bold text
      line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      
      // Italic text
      line = line.replace(/\*(.*?)\*/g, '<em>$1</em>');
      
      // Inline code
      line = line.replace(/`(.*?)`/g, '<code class="bg-gray-700 px-1 py-0.5 rounded text-sm">$1</code>');
      
      return (
        <p 
          key={index} 
          className="mb-2 last:mb-0"
          dangerouslySetInnerHTML={{ __html: line }}
        />
      );
    });
  };

  return (
    <div className={`
      flex space-x-4 p-4 rounded-lg border
      ${getBackgroundColor()}
      transition-all duration-200
    `}>
      {/* Icon */}
      <div className="flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center">
          {getIcon()}
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium text-white capitalize">
            {message.role}
          </span>
          <span className="text-xs text-gray-400">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>
        
        {/* Message Content */}
        <div className="text-gray-200 prose prose-invert max-w-none">
          {renderContent()}
        </div>
        
        {/* Metadata */}
        {message.metadata && (
          <div className="mt-3 flex items-center space-x-4 text-xs text-gray-400">
            {message.metadata.agent_id && (
              <span>Agent: {message.metadata.agent_id}</span>
            )}
            {message.metadata.tokens_used && (
              <span>Tokens: {message.metadata.tokens_used}</span>
            )}
            {message.metadata.execution_time && (
              <span>Time: {message.metadata.execution_time}ms</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

Message.displayName = 'Message';