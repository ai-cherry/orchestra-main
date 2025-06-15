import { useState, useEffect, useRef } from 'react'
import { 
  Send, 
  Mic, 
  Paperclip, 
  Settings,
  History,
  Sparkles,
  Bot,
  User
} from 'lucide-react'
import { apiClient } from '../lib/api'

const personas = {
  cherry: {
    name: 'Cherry',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    gradient: 'cherry-gradient'
  },
  sophia: {
    name: 'Sophia',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/20',
    gradient: 'sophia-gradient'
  },
  karen: {
    name: 'Karen',
    color: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/20',
    gradient: 'karen-gradient'
  }
}

const sampleMessages = [
  {
    id: 1,
    type: 'ai',
    persona: 'sophia',
    content: "Hello! I'm Sophia, your strategic AI assistant. I can help you navigate the Orchestra AI admin system. Try commands like 'show dashboard', 'open agent factory', or 'system status'.",
    timestamp: new Date(Date.now() - 60000)
  },
  {
    id: 2,
    type: 'ai',
    persona: 'karen',
    content: "Greetings! I'm Karen, your operational AI assistant. I excel at execution, automation, and workflow management. How can I help streamline your processes today?",
    timestamp: new Date(Date.now() - 30000)
  }
]

export default function ChatInterface({ activePersona, onPersonaChange }) {
  const [messages, setMessages] = useState(sampleMessages)
  const [inputValue, setInputValue] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentInput = inputValue
    setInputValue('')
    setIsTyping(true)
    setIsLoading(true)

    try {
      // Call the real API
      console.log('Sending chat request:', { message: currentInput, persona: activePersona })
      
      const response = await apiClient.sendChatMessage(currentInput, activePersona)
      
      console.log('Chat response received:', response)
      
      const aiResponse = {
        id: Date.now() + 1,
        type: 'ai',
        persona: activePersona,
        content: response.response || 'I received your message but had trouble processing it.',
        sources: response.sources || [],
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, aiResponse])
      
    } catch (error) {
      console.error('Chat API error:', error)
      
      // Fallback response
      const errorResponse = {
        id: Date.now() + 1,
        type: 'ai',
        persona: activePersona,
        content: `I apologize, but I'm having trouble connecting to my AI services right now. Error: ${error.message}`,
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, errorResponse])
    } finally {
      setIsTyping(false)
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    })
  }

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Bot className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">Orchestra AI Chat</h2>
          </div>
          <div className="flex items-center space-x-1">
            <Sparkles className="w-4 h-4 text-yellow-400" />
            <span className="text-sm text-gray-400">AI-powered</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
            <History className="w-4 h-4" />
          </button>
          <button className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`max-w-[80%] ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
              {message.type === 'ai' && (
                <div className="flex items-center space-x-2 mb-1">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${personas[message.persona]?.bgColor || 'bg-gray-600'}`}>
                    {personas[message.persona]?.name?.[0] || 'A'}
                  </div>
                  <span className={`text-sm font-medium ${personas[message.persona]?.color || 'text-gray-400'}`}>
                    {personas[message.persona]?.name || 'AI'}
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatTime(message.timestamp)}
                  </span>
                </div>
              )}
              
              <div
                className={`p-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : `${personas[message.persona]?.bgColor || 'bg-gray-800'} ${personas[message.persona]?.borderColor || 'border-gray-700'} border text-gray-100`
                }`}
              >
                <p className="text-sm leading-relaxed">{message.content}</p>
                
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-600">
                    <p className="text-xs text-gray-400">Sources: {message.sources.join(', ')}</p>
                  </div>
                )}
              </div>
              
              {message.type === 'user' && (
                <div className="flex items-center justify-end space-x-2 mt-1">
                  <span className="text-xs text-gray-500">
                    {formatTime(message.timestamp)}
                  </span>
                  <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center">
                    <User className="w-3 h-3 text-white" />
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="max-w-[80%]">
              <div className="flex items-center space-x-2 mb-1">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${personas[activePersona]?.bgColor || 'bg-gray-600'}`}>
                  {personas[activePersona]?.name?.[0] || 'A'}
                </div>
                <span className={`text-sm font-medium ${personas[activePersona]?.color || 'text-gray-400'}`}>
                  {personas[activePersona]?.name || 'AI'}
                </span>
              </div>
              
              <div className={`p-3 rounded-lg ${personas[activePersona]?.bgColor || 'bg-gray-800'} ${personas[activePersona]?.borderColor || 'border-gray-700'} border`}>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex items-end space-x-2">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message or command..."
              className="w-full p-3 pr-12 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows="1"
              style={{ minHeight: '44px', maxHeight: '120px' }}
              disabled={isLoading}
            />
            
            <div className="absolute right-2 bottom-2 flex items-center space-x-1">
              <button 
                className="p-1 text-gray-400 hover:text-white transition-colors"
                disabled={isLoading}
              >
                <Paperclip className="w-4 h-4" />
              </button>
              <button 
                className="p-1 text-gray-400 hover:text-white transition-colors"
                disabled={isLoading}
              >
                <Mic className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        
        <div className="flex items-center justify-between mt-2">
          <p className="text-xs text-gray-500">
            AI-powered commands available • Press Enter to send, Shift+Enter for new line
          </p>
          
          {isLoading && (
            <p className="text-xs text-blue-400">
              Connecting to AI services...
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

