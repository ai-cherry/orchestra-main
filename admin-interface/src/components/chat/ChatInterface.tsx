import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Mic, MicOff, Paperclip, Settings, Menu, Wifi, WifiOff } from 'lucide-react';
import PersonaSelector from './PersonaSelector';
import MessageBubble from './MessageBubble';
import VoiceInput from './VoiceInput';
import ContextPanel from './ContextPanel';

// Import API services
import { 
  initializeOrchestralAPI, 
  sendPersonaMessage, 
  setupWebSocketHandlers,
  websocketService,
  apiClient,
  checkSystemHealth
} from '../../services/api';

export type Persona = 'cherry' | 'sophia' | 'karen';

export interface Message {
  id: string;
  content: string;
  persona: Persona | 'user';
  timestamp: Date;
  type: 'text' | 'image' | 'file' | 'code' | 'command';
  metadata?: {
    command?: string;
    result?: any;
    attachments?: string[];
    processing_time_ms?: number;
    cross_domain_data?: Record<string, any>;
    error?: boolean;
  };
}

interface ChatInterfaceProps {
  className?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [activePersona, setActivePersona] = useState<Persona>('cherry');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [isContextPanelOpen, setIsContextPanelOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize API services on component mount
  useEffect(() => {
    const initializeServices = async () => {
      try {
        setIsInitializing(true);
        setConnectionError(null);

        // Initialize API services
        await initializeOrchestralAPI();

        // Setup WebSocket handlers
        setupWebSocketHandlers({
          onMessage: (message) => {
            setMessages(prev => [...prev, {
              id: message.id,
              content: message.content,
              persona: message.persona,
              timestamp: message.timestamp,
              type: message.type,
              metadata: message.metadata
            }]);
            setIsTyping(false);
          },
          onTyping: (persona, isTyping) => {
            if (persona === activePersona) {
              setIsTyping(isTyping);
            }
          },
          onPersonaSwitch: (persona) => {
            setActivePersona(persona);
          },
          onConnectionChange: (connected) => {
            setIsConnected(connected);
            if (connected) {
              setConnectionError(null);
            }
          },
          onError: (error) => {
            setConnectionError(error);
            console.error('WebSocket error:', error);
          }
        });

        // Check system health
        const isHealthy = await checkSystemHealth();
        if (!isHealthy) {
          setConnectionError('Backend services are not responding');
        }

        // Add welcome message from Cherry
        setMessages([{
          id: '1',
          content: "Hello! I'm Cherry, your personal AI overseer. I'm here to help you coordinate across all domains and manage your Orchestra AI system. What would you like to work on today?",
          persona: 'cherry',
          timestamp: new Date(),
          type: 'text'
        }]);

        setIsInitializing(false);
      } catch (error) {
        console.error('Failed to initialize Orchestra AI services:', error);
        setConnectionError('Failed to connect to Orchestra AI services');
        setIsInitializing(false);
      }
    };

    initializeServices();

    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
    };
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    if (!isInitializing) {
      inputRef.current?.focus();
    }
  }, [isInitializing]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isInitializing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      persona: 'user',
      timestamp: new Date(),
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    const messageContent = inputValue;
    setInputValue('');
    setIsTyping(true);

    try {
      // Send message to the active persona via API
      const response = await sendPersonaMessage(activePersona, messageContent);
      
      // Add AI response to messages
      setMessages(prev => [...prev, {
        id: response.id,
        content: response.content,
        persona: response.persona,
        timestamp: response.timestamp,
        type: response.type,
        metadata: response.metadata
      }]);
      
      setIsTyping(false);
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsTyping(false);
      
      // Add error message
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        content: "I'm sorry, I'm having trouble connecting to the AI services right now. Please try again in a moment.",
        persona: activePersona,
        timestamp: new Date(),
        type: 'text',
        metadata: { error: true }
      }]);
    }
  };

  const handlePersonaChange = async (persona: Persona) => {
    setActivePersona(persona);
    
    try {
      // Notify backend of persona switch
      if (websocketService.isConnected()) {
        websocketService.switchPersona(persona);
      }
      
      // Add a persona switch message
      const switchMessage: Message = {
        id: Date.now().toString(),
        content: `Switched to ${persona.charAt(0).toUpperCase() + persona.slice(1)}. How can I help you?`,
        persona: persona,
        timestamp: new Date(),
        type: 'text'
      };
      
      setMessages(prev => [...prev, switchMessage]);
    } catch (error) {
      console.error('Failed to switch persona:', error);
    }
  };

  const handleVoiceTranscript = (transcript: string) => {
    setInputValue(transcript);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCommand = async (command: string) => {
    console.log('Processing command:', command);
    
    try {
      // Send command to backend for processing
      const result = await apiClient.executeCommand({
        command,
        target: 'ui'
      });
      
      if (result.success && result.ui_actions) {
        // Execute UI actions returned by the command processor
        result.ui_actions.forEach(action => {
          switch (action.type) {
            case 'navigate':
              // Handle navigation
              break;
            case 'open_panel':
              if (action.target === 'context') {
                setIsContextPanelOpen(true);
              }
              break;
            case 'show_modal':
              // Handle modal display
              break;
          }
        });
      }
    } catch (error) {
      console.error('Command processing failed:', error);
    }
  };

  // Show loading state while initializing
  if (isInitializing) {
    return (
      <div className={`chat-container ${className} flex items-center justify-center`}>
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-midnight-white mb-2">
            Initializing Orchestra AI
          </h2>
          <p className="text-midnight-silver">
            Connecting to personas and backend services...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`chat-container ${className}`}>
      {/* Connection Status Bar */}
      {connectionError && (
        <div className="bg-midnight-error/20 border-b border-midnight-error/30 px-4 py-2">
          <div className="flex items-center gap-2 text-midnight-error text-sm">
            <WifiOff size={16} />
            <span>{connectionError}</span>
            <button 
              onClick={() => window.location.reload()}
              className="ml-auto text-xs underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between p-4 bg-midnight-dark-slate border-b border-midnight-electric-blue/20">
        <button
          onClick={() => setIsSidebarOpen(true)}
          className="p-2 text-midnight-silver hover:text-midnight-white transition-colors"
        >
          <Menu size={24} />
        </button>
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold text-midnight-white">Orchestra AI</h1>
          {isConnected ? (
            <Wifi size={16} className="text-midnight-success" />
          ) : (
            <WifiOff size={16} className="text-midnight-error" />
          )}
        </div>
        <button
          onClick={() => setIsContextPanelOpen(!isContextPanelOpen)}
          className="p-2 text-midnight-silver hover:text-midnight-white transition-colors"
        >
          <Settings size={24} />
        </button>
      </div>

      {/* Persona Selector */}
      <PersonaSelector
        activePersona={activePersona}
        onPersonaChange={handlePersonaChange}
        className="persona-selector"
      />

      {/* Main Chat Area */}
      <div className="flex flex-1 relative">
        {/* Messages Area */}
        <div className="flex-1 flex flex-col">
          <div className="chat-messages">
            <AnimatePresence>
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  className="slide-up"
                />
              ))}
            </AnimatePresence>
            
            {/* Typing Indicator */}
            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`message-bubble ${activePersona} max-w-xs`}
              >
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-sm opacity-70">
                    {activePersona.charAt(0).toUpperCase() + activePersona.slice(1)} is thinking...
                  </span>
                </div>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="chat-input-container">
            <div className="flex items-end gap-3">
              {/* Voice Input Button */}
              <VoiceInput
                onTranscript={handleVoiceTranscript}
                onCommand={handleCommand}
                isActive={isVoiceActive}
                onActiveChange={setIsVoiceActive}
              />

              {/* Text Input */}
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={`Message ${activePersona.charAt(0).toUpperCase() + activePersona.slice(1)}...`}
                  className="form-input w-full pr-12"
                  disabled={isVoiceActive || !isConnected}
                />
                
                {/* Attachment Button */}
                <button
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-midnight-silver hover:text-midnight-white transition-colors"
                  onClick={() => {/* Handle file attachment */}}
                >
                  <Paperclip size={18} />
                </button>
              </div>

              {/* Send Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isVoiceActive || !isConnected}
                className={`btn-midnight p-3 rounded-full ${
                  !inputValue.trim() || isVoiceActive || !isConnected
                    ? 'opacity-50 cursor-not-allowed' 
                    : 'hover:glow-blue'
                }`}
              >
                <Send size={20} />
              </motion.button>
            </div>

            {/* Quick Actions */}
            <div className="flex gap-2 mt-3">
              <button
                onClick={() => setInputValue('Show me the dashboard')}
                className="px-3 py-1 text-sm bg-midnight-navy text-midnight-silver hover:text-midnight-white rounded-full transition-colors"
                disabled={!isConnected}
              >
                Dashboard
              </button>
              <button
                onClick={() => setInputValue('Open agent factory')}
                className="px-3 py-1 text-sm bg-midnight-navy text-midnight-silver hover:text-midnight-white rounded-full transition-colors"
                disabled={!isConnected}
              >
                Agent Factory
              </button>
              <button
                onClick={() => setInputValue('Check system status')}
                className="px-3 py-1 text-sm bg-midnight-navy text-midnight-silver hover:text-midnight-white rounded-full transition-colors"
                disabled={!isConnected}
              >
                System Status
              </button>
            </div>

            {/* Connection Status */}
            <div className="flex items-center justify-between mt-2 text-xs text-midnight-silver">
              <div className="flex items-center gap-2">
                {isConnected ? (
                  <>
                    <Wifi size={12} className="text-midnight-success" />
                    <span>Connected to Orchestra AI</span>
                  </>
                ) : (
                  <>
                    <WifiOff size={12} className="text-midnight-error" />
                    <span>Disconnected</span>
                  </>
                )}
              </div>
              <div>
                Active: <span className={`${activePersona}-text font-medium`}>
                  {activePersona.charAt(0).toUpperCase() + activePersona.slice(1)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Context Panel */}
        <ContextPanel
          isOpen={isContextPanelOpen}
          onClose={() => setIsContextPanelOpen(false)}
          activePersona={activePersona}
          messages={messages}
        />
      </div>
    </div>
  );
};

export default ChatInterface;

