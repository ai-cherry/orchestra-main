import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, MoreVertical, Search, Sparkles } from 'lucide-react';
import { usePersona } from '../../contexts/PersonaContext';

interface Message {
  id: string;
  content: string;
  persona: 'sophia' | 'karen' | 'cherry';
  timestamp: Date;
  type: 'user' | 'assistant';
  metadata?: {
    searchResults?: any[];
    createdContent?: any;
    actions?: ActionButton[];
  };
}

interface ActionButton {
  id: string;
  label: string;
  icon: string;
  action: () => void;
}

const ChatInterface: React.FC = () => {
  const { currentPersona, switchPersona } = usePersona();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [searchMode, setSearchMode] = useState<'normal' | 'deep' | 'super_deep'>('normal');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      persona: currentPersona.id,
      timestamp: new Date(),
      type: 'user'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Simulate AI response with persona-specific behavior
      const response = await simulateAIResponse(inputValue, currentPersona.id, searchMode);
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.content,
        persona: currentPersona.id,
        timestamp: new Date(),
        type: 'assistant',
        metadata: response.metadata
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const simulateAIResponse = async (input: string, persona: string, mode: string) => {
    // This will be replaced with actual Portkey integration
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const personaResponses = {
      sophia: {
        content: `As your business intelligence assistant, I've analyzed "${input}" from a market perspective. Here are the key insights...`,
        metadata: {
          actions: [
            { id: '1', label: 'Create Presentation', icon: '📊', action: () => console.log('Creating presentation...') },
            { id: '2', label: 'Market Report', icon: '📈', action: () => console.log('Generating report...') }
          ]
        }
      },
      karen: {
        content: `From a clinical research standpoint, "${input}" presents several important considerations for pharmaceutical development...`,
        metadata: {
          actions: [
            { id: '1', label: 'Research Report', icon: '📋', action: () => console.log('Creating research report...') },
            { id: '2', label: 'Study Protocol', icon: '🔬', action: () => console.log('Generating protocol...') }
          ]
        }
      },
      cherry: {
        content: `Let me help you explore "${input}" creatively! I can generate various content types to bring your ideas to life...`,
        metadata: {
          actions: [
            { id: '1', label: 'Create Song', icon: '🎵', action: () => console.log('Creating song...') },
            { id: '2', label: 'Generate Image', icon: '🖼️', action: () => console.log('Generating image...') },
            { id: '3', label: 'Write Story', icon: '📚', action: () => console.log('Writing story...') },
            { id: '4', label: 'Create Video', icon: '🎬', action: () => console.log('Creating video...') }
          ]
        }
      }
    };

    return personaResponses[persona] || personaResponses.cherry;
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getPersonaActions = () => {
    switch (currentPersona.id) {
      case 'sophia':
        return [
          { icon: '📊', label: 'Presentation', action: () => console.log('Create presentation') },
          { icon: '📈', label: 'Report', action: () => console.log('Generate report') },
          { icon: '💼', label: 'Proposal', action: () => console.log('Create proposal') }
        ];
      case 'karen':
        return [
          { icon: '📋', label: 'Research', action: () => console.log('Research report') },
          { icon: '🔬', label: 'Protocol', action: () => console.log('Study protocol') },
          { icon: '📊', label: 'Analysis', action: () => console.log('Data analysis') }
        ];
      case 'cherry':
        return [
          { icon: '🎵', label: 'Song', action: () => console.log('Create song') },
          { icon: '🖼️', label: 'Image', action: () => console.log('Generate image') },
          { icon: '🎬', label: 'Video', action: () => console.log('Create video') },
          { icon: '📚', label: 'Story', action: () => console.log('Write story') }
        ];
      default:
        return [];
    }
  };

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Main Chat Area (80%) */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div 
          className="p-4 border-b border-gray-700 flex items-center justify-between"
          style={{ backgroundColor: currentPersona.theme.background }}
        >
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{currentPersona.icon}</span>
            <div>
              <h2 className="text-lg font-semibold text-white">{currentPersona.name}</h2>
              <p className="text-sm text-gray-300">{currentPersona.role}</p>
            </div>
          </div>
          
          {/* Search Mode Selector */}
          <div className="flex items-center space-x-2">
            <select
              value={searchMode}
              onChange={(e) => setSearchMode(e.target.value as any)}
              className="bg-gray-800 text-white px-3 py-1 rounded border border-gray-600"
            >
              <option value="normal">⚡ Normal</option>
              <option value="deep">🔍 Deep</option>
              <option value="super_deep">🚀 Super Deep</option>
            </select>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-400 mt-20">
              <div className="text-6xl mb-4">{currentPersona.icon}</div>
              <h3 className="text-xl font-semibold mb-2">Chat with {currentPersona.name}</h3>
              <p className="text-gray-500">{currentPersona.description}</p>
              
              {/* Quick Action Buttons */}
              <div className="flex justify-center space-x-2 mt-6">
                {getPersonaActions().map((action, index) => (
                  <button
                    key={index}
                    onClick={action.action}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <span>{action.icon}</span>
                    <span className="text-sm">{action.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-white'
                }`}
              >
                <p className="text-sm">{message.content}</p>
                
                {/* Action Buttons */}
                {message.metadata?.actions && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {message.metadata.actions.map((action) => (
                      <button
                        key={action.id}
                        onClick={action.action}
                        className="flex items-center space-x-1 px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs transition-colors"
                      >
                        <span>{action.icon}</span>
                        <span>{action.label}</span>
                      </button>
                    ))}
                  </div>
                )}
                
                <p className="text-xs text-gray-400 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 text-white px-4 py-2 rounded-lg">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span className="text-sm">{currentPersona.name} is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center space-x-2">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Message ${currentPersona.name}...`}
                className="w-full px-4 py-3 bg-gray-800 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
                disabled={isLoading}
              />
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
                <button className="text-gray-400 hover:text-white">
                  <Paperclip size={18} />
                </button>
                <button className="text-gray-400 hover:text-white">
                  <Mic size={18} />
                </button>
              </div>
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Notion Sidebar (20%) - Collapsible */}
      <div className="w-80 bg-gray-100 border-l border-gray-300">
        <div className="p-4 border-b border-gray-300">
          <h3 className="font-semibold text-gray-800">Notion Workspace</h3>
        </div>
        <div className="p-4 text-gray-600">
          <p className="text-sm">Notion integration coming soon...</p>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

