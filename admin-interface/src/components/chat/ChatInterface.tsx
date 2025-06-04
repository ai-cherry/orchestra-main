'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Paperclip, MoreVertical, Cherry, Brain, Stethoscope } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  domain?: 'cherry' | 'sophia' | 'karen';
  attachments?: string[];
}

export function ChatInterface() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: `Hello ${user?.name || 'there'}! I'm your AI orchestrator. I can help you with personal tasks (Cherry 🍒), business intelligence (Sophia 🧠), or healthcare operations (Karen 🏥). What would you like to work on today?`,
      role: 'assistant',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState<'auto' | 'cherry' | 'sophia' | 'karen'>('auto');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      role: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const responses = [
        "I understand you'd like help with that. Let me process your request and provide you with the best assistance.",
        "That's an interesting question! Based on your request, I'll coordinate with the appropriate domain to give you a comprehensive answer.",
        "I'm analyzing your request across all available domains to provide you with the most relevant and helpful response.",
        "Let me gather the necessary information and insights to address your needs effectively.",
      ];

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: responses[Math.floor(Math.random() * responses.length)],
        role: 'assistant',
        timestamp: new Date(),
        domain: selectedDomain !== 'auto' ? selectedDomain : ['cherry', 'sophia', 'karen'][Math.floor(Math.random() * 3)] as any,
      };

      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // In a real implementation, this would start/stop voice recording
  };

  const getDomainIcon = (domain?: string) => {
    switch (domain) {
      case 'cherry':
        return <Cherry className="h-4 w-4 text-cherry-500" />;
      case 'sophia':
        return <Brain className="h-4 w-4 text-sophia-500" />;
      case 'karen':
        return <Stethoscope className="h-4 w-4 text-karen-500" />;
      default:
        return null;
    }
  };

  const getDomainColor = (domain?: string) => {
    switch (domain) {
      case 'cherry':
        return 'border-l-cherry-400 bg-cherry-50';
      case 'sophia':
        return 'border-l-sophia-400 bg-sophia-50';
      case 'karen':
        return 'border-l-karen-400 bg-karen-50';
      default:
        return 'border-l-gray-400 bg-gray-50';
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Chat header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Active Domain:</span>
            <select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value as any)}
              className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="auto">🤖 Auto-detect</option>
              <option value="cherry">🍒 Cherry (Personal)</option>
              <option value="sophia">🧠 Sophia (Business)</option>
              <option value="karen">🏥 Karen (Healthcare)</option>
            </select>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100">
            <MoreVertical className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : `bg-white border border-gray-200 ${message.domain ? getDomainColor(message.domain) : ''} border-l-4`
              }`}
            >
              {message.role === 'assistant' && message.domain && (
                <div className="flex items-center space-x-2 mb-2">
                  {getDomainIcon(message.domain)}
                  <span className="text-xs font-medium text-gray-600 capitalize">
                    {message.domain}
                  </span>
                </div>
              )}
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              <p className={`text-xs mt-1 ${
                message.role === 'user' ? 'text-indigo-200' : 'text-gray-500'
              }`}>
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-2 border-l-4 border-l-gray-400">
              <div className="flex items-center space-x-1">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-xs text-gray-500 ml-2">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <div className="flex items-end space-x-2">
          <button className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-600 rounded-md hover:bg-gray-100">
            <Paperclip className="h-5 w-5" />
          </button>
          
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here... (Shift+Enter for new line)"
              className="w-full px-3 py-2 border border-gray-300 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              rows={1}
              style={{ minHeight: '40px', maxHeight: '120px' }}
            />
          </div>
          
          <button
            onClick={toggleRecording}
            className={`flex-shrink-0 p-2 rounded-md transition-colors ${
              isRecording
                ? 'bg-red-100 text-red-600 hover:bg-red-200'
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
            }`}
          >
            {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
          </button>
          
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isTyping}
            className="flex-shrink-0 p-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        
        <div className="mt-2 text-xs text-gray-500 text-center">
          AI Orchestrator is ready to help with personal, business, and healthcare tasks
        </div>
      </div>
    </div>
  );
}

