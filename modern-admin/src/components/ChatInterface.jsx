import { useState, useRef, useEffect } from 'react'
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
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const aiResponse = {
        id: Date.now() + 1,
        type: 'ai',
        persona: activePersona,
        content: generateAIResponse(inputValue, activePersona),
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiResponse])
      setIsTyping(false)
    }, 1500)
  }

  const generateAIResponse = (input, persona) => {
    const responses = {
      cherry: [
        "I love creative challenges! Let me help you design something amazing.",
        "That's an interesting creative problem. Here's my artistic perspective...",
        "Let's think outside the box and create something innovative!"
      ],
      sophia: [
        "Let me analyze this strategically and provide you with a comprehensive solution.",
        "Based on my analysis, here's the optimal approach to your challenge.",
        "I'll help you break this down into manageable strategic components."
      ],
      karen: [
        "I'll help you execute this efficiently. Here's the step-by-step process.",
        "Let me streamline this workflow for maximum productivity.",
        "I can automate this process to save you time and effort."
      ]
    }
    
    const personaResponses = responses[persona] || responses.sophia
    return personaResponses[Math.floor(Math.random() * personaResponses.length)]
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-border bg-card">
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-semibold ${personas[activePersona].gradient}`}>
            {personas[activePersona].name[0]}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-foreground">
              {personas[activePersona].name}
            </h2>
            <p className="text-sm text-muted-foreground">
              {activePersona === 'cherry' && 'Creative AI focused on design and innovation'}
              {activePersona === 'sophia' && 'Strategic AI focused on analysis and planning'}
              {activePersona === 'karen' && 'Operational AI focused on execution and automation'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button className="p-2 rounded-lg hover:bg-accent transition-colors">
            <History className="w-5 h-5 text-muted-foreground" />
          </button>
          <button className="p-2 rounded-lg hover:bg-accent transition-colors">
            <Settings className="w-5 h-5 text-muted-foreground" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.type === 'ai' && (
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold flex-shrink-0 ${personas[message.persona].gradient}`}>
                <Bot className="w-5 h-5" />
              </div>
            )}
            
            <div className={`max-w-2xl ${message.type === 'user' ? 'order-first' : ''}`}>
              <div className={`rounded-2xl px-4 py-3 ${
                message.type === 'user'
                  ? 'bg-primary text-primary-foreground ml-auto'
                  : `${personas[message.persona || activePersona].bgColor} ${personas[message.persona || activePersona].borderColor} border`
              }`}>
                <p className="text-sm leading-relaxed">{message.content}</p>
              </div>
              <p className="text-xs text-muted-foreground mt-1 px-2">
                {formatTime(message.timestamp)}
              </p>
            </div>
            
            {message.type === 'user' && (
              <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-accent-foreground" />
              </div>
            )}
          </div>
        ))}
        
        {isTyping && (
          <div className="flex gap-4 justify-start">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold ${personas[activePersona].gradient}`}>
              <Bot className="w-5 h-5" />
            </div>
            <div className={`rounded-2xl px-4 py-3 ${personas[activePersona].bgColor} ${personas[activePersona].borderColor} border`}>
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-6 border-t border-border bg-card">
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <div className="relative">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message or command..."
                className="w-full px-4 py-3 pr-12 bg-input border border-border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-ring text-foreground placeholder:text-muted-foreground"
                rows={1}
                style={{ minHeight: '48px', maxHeight: '120px' }}
              />
              <button className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-lg hover:bg-accent transition-colors">
                <Paperclip className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>
            
            <div className="flex items-center justify-between mt-2 px-2">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Sparkles className="w-3 h-3" />
                <span>AI-powered commands available</span>
              </div>
              <div className="text-xs text-muted-foreground">
                Press Enter to send, Shift+Enter for new line
              </div>
            </div>
          </div>
          
          <div className="flex gap-2">
            <button className="p-3 rounded-xl bg-accent hover:bg-accent/80 transition-colors">
              <Mic className="w-5 h-5 text-accent-foreground" />
            </button>
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className="p-3 rounded-xl bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5 text-primary-foreground" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

