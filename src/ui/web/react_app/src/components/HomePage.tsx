import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { setActivePersona, addMessage, clearHistory } from '../store/slices/chatSlice';
import { PersonaSelector } from './PersonaSelector';
import { SearchModeSelector } from './SearchModeSelector';
import { FileUploadPanel } from './FileUploadPanel';
import { MultimediaPanel } from './MultimediaPanel';
import { AnalyticsWidget } from './AnalyticsWidget';
import { ChatInterface } from './ChatInterface';
import { ChatBubbleLeftRightIcon, DocumentIcon, PhotoIcon, VideoCameraIcon } from '@heroicons/react/24/outline';

export interface SearchMode {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface Persona {
  id: string;
  name: string;
  icon: string;
  color: string;
  description: string;
}

const SEARCH_MODES: SearchMode[] = [
  { id: 'normal', name: 'Normal', description: 'Standard AI responses', icon: '🔍' },
  { id: 'creative', name: 'Creative', description: 'Imaginative and artistic', icon: '🎨' },
  { id: 'deep', name: 'Deep', description: 'Thorough analysis', icon: '🧠' },
  { id: 'super-deep', name: 'Super-Deep', description: 'Comprehensive research', icon: '🔬' },
  { id: 'uncensored', name: 'Uncensored', description: 'Unrestricted responses', icon: '🚀' },
];

const PERSONAS: Persona[] = [
  {
    id: 'cherry',
    name: 'Cherry',
    icon: '🍒',
    color: 'cherry',
    description: 'Sweet, playful, and flirty life companion'
  },
  {
    id: 'sophia',
    name: 'Sophia',
    icon: '💼',
    color: 'sophia',
    description: 'Analytical, strategic, payment & debt recovery'
  },
  {
    id: 'karen',
    name: 'Karen',
    icon: '🏥',
    color: 'karen',
    description: 'Precise, compliant, patient recruitment & trials'
  }
];

export const HomePage: React.FC = () => {
  const dispatch = useDispatch();
  const { activePersona, messages, isLoading } = useSelector((state: RootState) => state.chat);
  const [searchMode, setSearchMode] = useState<string>('normal');
  const [searchInput, setSearchInput] = useState<string>('');
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [showFileUpload, setShowFileUpload] = useState<boolean>(false);
  const [showMultimedia, setShowMultimedia] = useState<boolean>(false);

  const handlePersonaChange = (personaId: string) => {
    dispatch(setActivePersona(personaId));
  };

  const handleSendMessage = async () => {
    if (!searchInput.trim()) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: searchInput,
      timestamp: new Date().toISOString(),
      persona: activePersona,
      searchMode
    };

    dispatch(addMessage(userMessage));
    setSearchInput('');

    try {
      // API call to backend
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: searchInput,
          persona: activePersona,
          searchMode,
          history: messages.slice(-5) // Last 5 messages for context
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: data.response || 'Sorry, I encountered an error processing your request.',
        timestamp: new Date().toISOString(),
        persona: activePersona,
        searchMode
      };

      dispatch(addMessage(assistantMessage));
    } catch (error) {
      console.error('Chat error:', error);
      
      // Fallback response
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: `Hi! I'm ${PERSONAS.find(p => p.id === activePersona)?.name}. I'm currently working on connecting to the backend, but I received your message: "${searchInput}". How can I help you today?`,
        timestamp: new Date().toISOString(),
        persona: activePersona,
        searchMode
      };

      dispatch(addMessage(errorMessage));
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const getPersonaAccentClass = (personaId: string) => {
    switch (personaId) {
      case 'cherry': return 'border-cherry-500 ring-cherry-500/20';
      case 'sophia': return 'border-sophia-500 ring-sophia-500/20';
      case 'karen': return 'border-karen-500 ring-karen-500/20';
      default: return 'border-blue-500 ring-blue-500/20';
    }
  };

  const getPersonaGradient = (personaId: string) => {
    switch (personaId) {
      case 'cherry': return 'from-cherry-500 to-cherry-600';
      case 'sophia': return 'from-sophia-500 to-sophia-600';
      case 'karen': return 'from-karen-500 to-karen-600';
      default: return 'from-blue-500 to-blue-600';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-surface via-primary-surface2 to-primary-surface3">
      {/* Header */}
      <header className="text-center py-8 px-4">
        <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-cherry-400 via-sophia-400 to-karen-400 bg-clip-text text-transparent">
          🍒 Cherry AI Orchestrator
        </h1>
        <p className="text-xl text-white/80 max-w-2xl mx-auto">
          Advanced AI Interface - Performance & Intelligence Focused
        </p>
      </header>

      {/* Persona Selector */}
      <div className="max-w-7xl mx-auto px-4 mb-8">
        <PersonaSelector
          personas={PERSONAS}
          activePersona={activePersona}
          onPersonaChange={handlePersonaChange}
        />
      </div>

      {/* Main Chat Interface */}
      <div className="max-w-7xl mx-auto px-4 mb-8">
        <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 shadow-card">
          {/* Search Mode Selector */}
          <div className="mb-6">
            <SearchModeSelector
              modes={SEARCH_MODES}
              activeMode={searchMode}
              onModeChange={setSearchMode}
              accentColor={activePersona}
            />
          </div>

          {/* Main Input */}
          <div className="relative mb-6">
            <div className="flex items-center gap-4 p-2 bg-white/5 rounded-2xl border border-white/20 focus-within:border-white/40 transition-colors">
              <ChatBubbleLeftRightIcon className="w-6 h-6 text-white/60" />
              <input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Ask ${PERSONAS.find(p => p.id === activePersona)?.name} anything...`}
                className="flex-1 bg-transparent text-white placeholder-white/60 text-lg focus:outline-none"
              />
              <button
                onClick={handleSendMessage}
                disabled={!searchInput.trim() || isLoading}
                className={`px-6 py-3 rounded-xl font-semibold transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r ${getPersonaGradient(activePersona)} text-white shadow-lg hover:shadow-xl`}
              >
                {isLoading ? 'Thinking...' : 'Send'}
              </button>
            </div>
          </div>

          {/* Advanced Options */}
          <div className="mb-6">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-white/80 hover:text-white transition-colors text-sm font-medium"
            >
              Advanced Options {showAdvanced ? '▼' : '▶'}
            </button>
            
            {showAdvanced && (
              <div className="mt-4 p-4 bg-white/5 rounded-xl border border-white/10">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    onClick={() => setShowFileUpload(!showFileUpload)}
                    className="flex items-center gap-3 p-3 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                  >
                    <DocumentIcon className="w-5 h-5" />
                    Upload & Ingest File
                  </button>
                  
                  <button
                    onClick={() => setShowMultimedia(!showMultimedia)}
                    className="flex items-center gap-3 p-3 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                  >
                    <PhotoIcon className="w-5 h-5" />
                    Generate Image
                  </button>
                  
                  <button
                    onClick={() => setShowMultimedia(!showMultimedia)}
                    className="flex items-center gap-3 p-3 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
                  >
                    <VideoCameraIcon className="w-5 h-5" />
                    Generate Video
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* File Upload Panel */}
          {showFileUpload && (
            <div className="mb-6">
              <FileUploadPanel onClose={() => setShowFileUpload(false)} />
            </div>
          )}

          {/* Multimedia Panel */}
          {showMultimedia && (
            <div className="mb-6">
              <MultimediaPanel onClose={() => setShowMultimedia(false)} />
            </div>
          )}

          {/* Chat History */}
          <ChatInterface
            messages={messages}
            activePersona={activePersona}
            isLoading={isLoading}
            onClearHistory={() => dispatch(clearHistory())}
          />
        </div>
      </div>

      {/* Analytics Widget */}
      <div className="max-w-7xl mx-auto px-4 mb-8">
        <AnalyticsWidget />
      </div>

      {/* Footer */}
      <footer className="bg-white/5 backdrop-blur-lg border-t border-white/10 py-8 mt-16">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <div className="flex flex-wrap justify-center gap-6 text-white/80">
            <a href="/agent-lab" className="hover:text-white transition-colors">Agent Lab</a>
            <a href="/orchestrators" className="hover:text-white transition-colors">Orchestrators</a>
            <a href="/todo" className="hover:text-white transition-colors">To-Do</a>
            <a href="/project-mgmt" className="hover:text-white transition-colors">Project Mgmt</a>
            <a href="/monitoring" className="hover:text-white transition-colors">Monitoring</a>
            <a href="/settings" className="hover:text-white transition-colors">Settings</a>
          </div>
        </div>
      </footer>
    </div>
  );
}; 