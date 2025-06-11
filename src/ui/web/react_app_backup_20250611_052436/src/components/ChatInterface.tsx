import React from 'react';
import { ChatMessage } from '../store/slices/chatSlice';
import { TrashIcon } from '@heroicons/react/24/outline';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  activePersona: string;
  isLoading: boolean;
  onClearHistory: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  activePersona,
  isLoading,
  onClearHistory,
}) => {
  const getPersonaColor = (persona: string) => {
    switch (persona) {
      case 'cherry': return 'border-cherry-500 bg-cherry-500/10';
      case 'sophia': return 'border-sophia-500 bg-sophia-500/10';
      case 'karen': return 'border-karen-500 bg-karen-500/10';
      default: return 'border-blue-500 bg-blue-500/10';
    }
  };

  const getPersonaIcon = (persona: string) => {
    switch (persona) {
      case 'cherry': return '🍒';
      case 'sophia': return '💼';
      case 'karen': return '🏥';
      default: return '🤖';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatSearchMode = (mode?: string) => {
    if (!mode) return '';
    return mode.charAt(0).toUpperCase() + mode.slice(1);
  };

  return (
    <div className="w-full">
      {/* Chat Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          💬 Conversation History
          {isLoading && (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
          )}
        </h3>
        
        {messages.length > 1 && (
          <button
            onClick={onClearHistory}
            className="flex items-center gap-2 px-3 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
          >
            <TrashIcon className="w-4 h-4" />
            Clear History
          </button>
        )}
      </div>

      {/* Chat Messages */}
      <div className="bg-black/20 rounded-xl p-4 max-h-96 overflow-y-auto space-y-4 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
        {messages.length === 0 ? (
          <div className="text-center text-white/60 py-8">
            <div className="text-4xl mb-2">💭</div>
            <p>No messages yet. Start a conversation!</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              {/* Avatar */}
              <div className={`
                flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm
                ${message.role === 'user' 
                  ? 'bg-white/20 text-white' 
                  : `${getPersonaColor(message.persona)} text-white`
                }
              `}>
                {message.role === 'user' ? '👤' : getPersonaIcon(message.persona)}
              </div>

              {/* Message Content */}
              <div className={`
                flex-1 max-w-[80%] p-3 rounded-xl border-l-4
                ${message.role === 'user'
                  ? 'bg-white/10 border-white/40 text-white'
                  : `${getPersonaColor(message.persona)} text-white`
                }
              `}>
                {/* Message Header */}
                <div className="flex items-center justify-between mb-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {message.role === 'user' ? 'You' : message.persona?.charAt(0).toUpperCase() + message.persona?.slice(1)}
                    </span>
                    {message.searchMode && (
                      <span className="px-2 py-1 bg-white/20 rounded-full text-xs">
                        {formatSearchMode(message.searchMode)}
                      </span>
                    )}
                  </div>
                  <span className="text-white/60">
                    {formatTimestamp(message.timestamp)}
                  </span>
                </div>

                {/* Message Text */}
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </div>

                {/* Message Metadata */}
                {message.metadata && (
                  <div className="mt-2 pt-2 border-t border-white/20 text-xs text-white/70">
                    <div className="flex items-center gap-4">
                      {message.metadata.responseTime && (
                        <span>⚡ {message.metadata.responseTime}ms</span>
                      )}
                      {message.metadata.model && (
                        <span>🤖 {message.metadata.model}</span>
                      )}
                      {message.metadata.tokens && (
                        <span>📊 {message.metadata.tokens} tokens</span>
                      )}
                    </div>
                  </div>
                )}

                {/* Attachments */}
                {message.attachments && message.attachments.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-white/20">
                    <div className="text-xs text-white/70 mb-1">Attachments:</div>
                    <div className="flex flex-wrap gap-1">
                      {message.attachments.map((attachment, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-white/10 rounded text-xs"
                        >
                          📎 {attachment}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex gap-3">
            <div className={`
              flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm
              ${getPersonaColor(activePersona)}
            `}>
              {getPersonaIcon(activePersona)}
            </div>
            <div className={`
              flex-1 max-w-[80%] p-3 rounded-xl border-l-4 ${getPersonaColor(activePersona)}
            `}>
              <div className="flex items-center gap-2 text-white/80">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-white/60 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chat Stats */}
      {messages.length > 0 && (
        <div className="mt-4 p-3 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center justify-between text-sm text-white/70">
            <span>{messages.length} messages in this conversation</span>
            <span>
              Last activity: {formatTimestamp(messages[messages.length - 1]?.timestamp || new Date().toISOString())}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}; 