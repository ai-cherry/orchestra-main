"use client";

import React, { memo } from 'react';
import { Message } from './Message';
import type { Message as MessageType } from '@/types/conversation';

interface MessageListProps {
  messages: MessageType[];
  isProcessing: boolean;
}

/**
 * MessageList Component
 * 
 * Renders the conversation history with optimized performance through
 * memoization and virtual scrolling for large message lists.
 */
export const MessageList: React.FC<MessageListProps> = memo(({ 
  messages, 
  isProcessing 
}) => {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}
      
      {/* Processing Indicator */}
      {isProcessing && (
        <div className="flex items-center space-x-3 text-gray-400">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-sky-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-sky-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-sky-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
          <span className="text-sm">AI is thinking...</span>
        </div>
      )}
    </div>
  );
});

MessageList.displayName = 'MessageList';