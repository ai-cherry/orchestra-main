"use client";

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { OmniSearch } from '../OmniSearch/OmniSearch';
import { QuickActions } from '../QuickActions/QuickActions';
import { MessageList } from './MessageList';
import { ContextPanel } from './ContextPanel';
import type { Message, ConversationContext } from '@/types/conversation';

/**
 * ConversationalInterface Component
 * 
 * Main dashboard interface implementing a conversational AI-first design.
 * Replaces the traditional admin panel with an intuitive chat interface.
 */
export const ConversationalInterface: React.FC = () => {
  // State management
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hi Cherry! What can I help you orchestrate today?',
      timestamp: new Date().toISOString()
    }
  ]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [context, setContext] = useState<ConversationContext>({
    activeAgents: [],
    recentActions: [],
    systemStatus: 'ready'
  });
  
  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // API configuration
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  /**
   * Scroll to bottom of messages
   */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  /**
   * Handle new message from user
   */
  const handleNewMessage = useCallback(async (content: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);
    
    try {
      // Send to backend
      const response = await fetch(`${apiUrl}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || ''
        },
        body: JSON.stringify({
          query: content,
          context: context
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to process message');
      }
      
      const data = await response.json();
      
      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toISOString(),
        metadata: {
          agent_id: data.agent_id,
          tokens_used: data.tokens_used
        }
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
      // Update context if needed
      if (data.context_update) {
        setContext(prev => ({ ...prev, ...data.context_update }));
      }
    } catch (error) {
      console.error('Message processing error:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsProcessing(false);
    }
  }, [apiUrl, context]);

  /**
   * Handle quick action execution
   */
  const handleQuickAction = useCallback((action: string) => {
    // Quick actions can trigger specific behaviors
    switch (action) {
      case 'clear':
        setMessages([{
          id: Date.now().toString(),
          role: 'assistant',
          content: 'Conversation cleared. How can I help you?',
          timestamp: new Date().toISOString()
        }]);
        break;
      case 'export':
        exportConversation();
        break;
      default:
        // console.log('Unknown action:', action);
    }
  }, []);

  /**
   * Export conversation as JSON
   */
  const exportConversation = () => {
    const data = {
      messages,
      context,
      exportedAt: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  /**
   * Auto-scroll on new messages
   */
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  /**
   * Keyboard shortcuts
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + L to clear conversation
      if ((e.metaKey || e.ctrlKey) && e.key === 'l') {
        e.preventDefault();
        handleQuickAction('clear');
      }
      
      // Cmd/Ctrl + E to export
      if ((e.metaKey || e.ctrlKey) && e.key === 'e') {
        e.preventDefault();
        handleQuickAction('export');
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleQuickAction]);

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">AI Orchestrator</h1>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => handleQuickAction('clear')}
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Clear conversation"
              >
                Clear
              </button>
              <button
                onClick={() => handleQuickAction('export')}
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Export conversation"
              >
                Export
              </button>
            </div>
          </div>
        </header>
        
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-4" ref={containerRef}>
          <MessageList 
            messages={messages} 
            isProcessing={isProcessing}
          />
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input Area */}
        <div className="border-t border-gray-700 bg-gray-800 px-6 py-4">
          <OmniSearch />
        </div>
        
        {/* Quick Actions */}
        <div className="bg-gray-800 px-6 py-6 border-t border-gray-700">
          <QuickActions />
        </div>
      </div>
      
      {/* Context Panel */}
      <aside className="w-80 bg-gray-800 border-l border-gray-700 overflow-y-auto">
        <ContextPanel context={context} />
      </aside>
    </div>
  );
};