# 🚀 Orchestra AI Next Phase Implementation Plan
*Comprehensive roadmap for Enhanced Animations, Voice Recognition, LLM Integration, Natural Language Commands, and Advanced Context*

## 📋 Executive Summary

Based on the comprehensive feature mapping analysis, this implementation plan provides concrete steps to integrate the five next phase features into the existing Orchestra AI architecture:

1. **Enhanced Animations** - Framer Motion integration with persona-specific animations
2. **Voice Recognition** - Web Speech API with MCP tool integration  
3. **LLM Integration** - OpenRouter + direct provider connections with intelligent routing
4. **Natural Language Commands** - Command parsing with UI action execution
5. **Advanced Context** - Enhanced memory system access with cross-persona collaboration

## 🏗️ Current Architecture Assessment

### ✅ Existing Infrastructure Ready for Integration
- **MCP Server**: `mcp_unified_server.py` with 7 tools and persona integration
- **Admin Interface**: React + Vite with persona selection and routing
- **API Backend**: Running on port 8010 with persona support
- **Memory Architecture**: 5-tier system with compression and cross-domain queries
- **Persona System**: Cherry, Sophia, Karen with specialized domains

### 🔧 Integration Points Identified
- MCP tool registration system for new capabilities
- React component structure for UI enhancements
- Existing persona routing for intelligent feature selection
- Memory system for context management
- Notion integration for logging and analytics

## 🎯 Phase 1: Enhanced Animations (Week 1-2)

### Implementation Strategy
Leverage Framer Motion to create persona-specific animations that enhance user experience without impacting performance.

### Step 1.1: Install and Configure Framer Motion
```bash
cd admin-interface
npm install framer-motion
```

### Step 1.2: Create Animation System
```javascript
// src/hooks/usePersonaAnimations.js
import { useAnimation } from 'framer-motion';

export const usePersonaAnimations = (persona) => {
  const controls = useAnimation();
  
  const animations = {
    cherry: {
      initial: { opacity: 0, y: 20, scale: 0.9 },
      animate: { 
        opacity: 1, 
        y: 0, 
        scale: 1,
        transition: { 
          type: "spring", 
          stiffness: 300, 
          damping: 20,
          duration: 0.6
        }
      },
      exit: { opacity: 0, y: -20, transition: { duration: 0.3 } },
      hover: { scale: 1.02, transition: { duration: 0.2 } },
      tap: { scale: 0.98 }
    },
    sophia: {
      initial: { opacity: 0, x: -20 },
      animate: { 
        opacity: 1, 
        x: 0,
        transition: { 
          type: "tween", 
          ease: "easeOut", 
          duration: 0.4 
        }
      },
      exit: { opacity: 0, x: 20, transition: { duration: 0.3 } },
      hover: { x: 2, transition: { duration: 0.2 } },
      tap: { x: -2 }
    },
    karen: {
      initial: { opacity: 0, scale: 0.95 },
      animate: { 
        opacity: 1, 
        scale: 1,
        transition: { 
          type: "spring", 
          stiffness: 400, 
          damping: 25,
          duration: 0.5
        }
      },
      exit: { opacity: 0, scale: 0.9, transition: { duration: 0.2 } },
      hover: { scale: 1.01, transition: { duration: 0.15 } },
      tap: { scale: 0.99 }
    }
  };
  
  return animations[persona] || animations.cherry;
};
```

### Step 1.3: Create Animated Components
```javascript
// src/components/ui/AnimatedCard.jsx
import { motion } from 'framer-motion';
import { usePersonaAnimations } from '../../hooks/usePersonaAnimations';

export const AnimatedCard = ({ children, persona, className = "" }) => {
  const animations = usePersonaAnimations(persona);
  
  return (
    <motion.div
      className={`animated-card ${persona} ${className}`}
      initial={animations.initial}
      animate={animations.animate}
      exit={animations.exit}
      whileHover={animations.hover}
      whileTap={animations.tap}
    >
      {children}
    </motion.div>
  );
};
```

### Step 1.4: Integrate with Existing Components
Update `PersonaSelection.jsx`, `SearchInterface.jsx`, and other key components to use animated versions.

## 🎤 Phase 2: Voice Recognition (Week 3-4)

### Implementation Strategy
Implement Web Speech API on frontend with MCP tool integration for voice command processing.

### Step 2.1: Create Voice Recognition Service
```javascript
// src/services/voiceRecognition.js
export class VoiceRecognitionService {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.isSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    this.initRecognition();
  }
  
  initRecognition() {
    if (!this.isSupported) return;
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US';
    this.recognition.maxAlternatives = 1;
  }
  
  async startListening(onResult, onError, onEnd) {
    if (!this.isSupported || !this.recognition) {
      onError('Speech recognition not supported');
      return false;
    }
    
    this.recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0])
        .map(result => result.transcript)
        .join('');
        
      if (event.results[0].isFinal) {
        onResult(transcript);
      }
    };
    
    this.recognition.onerror = (event) => onError(event.error);
    this.recognition.onend = () => {
      this.isListening = false;
      onEnd();
    };
    
    try {
      this.recognition.start();
      this.isListening = true;
      return true;
    } catch (error) {
      onError(error.message);
      return false;
    }
  }
  
  stop() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
  }
}
```

### Step 2.2: Add Voice MCP Tool
```python
# Add to mcp_unified_server.py in _setup_tools method
types.Tool(
    name="process_voice_command",
    description="Process voice input and convert to actions",
    inputSchema={
        "type": "object",
        "properties": {
            "transcript": {"type": "string"},
            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
            "context": {"type": "object"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["transcript"]
    }
)
```

### Step 2.3: Create Voice UI Component
```javascript
// src/components/ui/VoiceInput.jsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { VoiceRecognitionService } from '../../services/voiceRecognition';
import { callMcpTool } from '../../services/mcpService';

export const VoiceInput = ({ persona, onCommand, className = "" }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [voiceService] = useState(() => new VoiceRecognitionService());
  const [error, setError] = useState(null);
  
  const handleVoiceStart = async () => {
    if (!voiceService.isSupported) {
      setError('Voice recognition not supported in this browser');
      return;
    }
    
    setError(null);
    setTranscript('');
    
    const success = await voiceService.startListening(
      async (finalTranscript) => {
        setTranscript(finalTranscript);
        
        try {
          const result = await callMcpTool('process_voice_command', {
            transcript: finalTranscript,
            persona: persona,
            context: { 
              currentPath: window.location.pathname,
              timestamp: new Date().toISOString()
            }
          });
          
          if (onCommand) {
            onCommand(result);
          }
        } catch (error) {
          setError('Failed to process voice command');
        }
      },
      (error) => {
        setError(`Voice recognition error: ${error}`);
        setIsListening(false);
      },
      () => {
        setIsListening(false);
      }
    );
    
    if (success) {
      setIsListening(true);
    }
  };
  
  const handleVoiceStop = () => {
    voiceService.stop();
    setIsListening(false);
  };
  
  return (
    <div className={`voice-input ${className}`}>
      <motion.button
        className={`voice-button ${persona} ${isListening ? 'listening' : ''}`}
        onClick={isListening ? handleVoiceStop : handleVoiceStart}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        animate={isListening ? { 
          boxShadow: ["0 0 0 0 rgba(255, 0, 0, 0.7)", "0 0 0 10px rgba(255, 0, 0, 0)"],
          transition: { duration: 1, repeat: Infinity }
        } : {}}
      >
        {isListening ? '🎤 Listening...' : '🎤 Voice Input'}
      </motion.button>
      
      {transcript && (
        <motion.div 
          className="transcript"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          "{transcript}"
        </motion.div>
      )}
      
      {error && (
        <motion.div 
          className="error"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {error}
        </motion.div>
      )}
    </div>
  );
};
```

## 🤖 Phase 3: LLM Integration (Week 5-6)

### Implementation Strategy
Implement combined architecture with OpenRouter as primary and direct provider connections for specialized needs.

### Step 3.1: Create LLM Service Manager
```python
# llm_service_manager.py
import os
import json
import aiohttp
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str
    endpoint: str
    context_window: int
    fallback: Optional[Dict[str, str]] = None

class LLMServiceManager:
    def __init__(self):
        self.configs = {
            "cherry": LLMConfig(
                provider="openrouter",
                model="openai/gpt-4o",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                endpoint="https://openrouter.ai/api/v1/chat/completions",
                context_window=128000,
                fallback={"provider": "anthropic", "model": "claude-3-opus-20240229"}
            ),
            "sophia": LLMConfig(
                provider="openrouter", 
                model="anthropic/claude-3-opus-20240229",
                api_key=os.getenv("OPENROUTER_API_KEY"),
                endpoint="https://openrouter.ai/api/v1/chat/completions",
                context_window=200000,
                fallback={"provider": "openai", "model": "gpt-4-turbo"}
            ),
            "karen": LLMConfig(
                provider="openrouter",
                model="openai/gpt-4-turbo", 
                api_key=os.getenv("OPENROUTER_API_KEY"),
                endpoint="https://openrouter.ai/api/v1/chat/completions",
                context_window=128000,
                fallback={"provider": "anthropic", "model": "claude-3-sonnet-20240229"}
            )
        }
    
    async def generate_response(self, persona: str, messages: list, options: Dict[str, Any] = None):
        """Generate response using persona-specific LLM configuration"""
        if persona not in self.configs:
            raise ValueError(f"Unknown persona: {persona}")
        
        config = self.configs[persona]
        
        try:
            return await self._call_llm(config, messages, options)
        except Exception as e:
            # Try fallback if available
            if config.fallback:
                fallback_config = self._create_fallback_config(config.fallback)
                return await self._call_llm(fallback_config, messages, options)
            raise e
    
    async def _call_llm(self, config: LLMConfig, messages: list, options: Dict[str, Any] = None):
        """Make API call to LLM provider"""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": options.get("temperature", 0.7) if options else 0.7,
            "max_tokens": options.get("max_tokens", 1000) if options else 1000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(config.endpoint, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"LLM API error: {response.status} - {error_text}")
                
                result = await response.json()
                return {
                    "provider": config.provider,
                    "model": config.model,
                    "content": result["choices"][0]["message"]["content"],
                    "usage": result.get("usage", {})
                }
```

### Step 3.2: Add LLM MCP Tool
```python
# Add to mcp_unified_server.py
types.Tool(
    name="call_llm_service",
    description="Call LLM service with persona-specific model",
    inputSchema={
        "type": "object",
        "properties": {
            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
            "messages": {"type": "array", "items": {"type": "object"}},
            "options": {"type": "object"}
        },
        "required": ["persona", "messages"]
    }
)
```

### Step 3.3: Create LLM Chat Component
```javascript
// src/components/chat/LLMChat.jsx
import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { callMcpTool } from '../../services/mcpService';

export const LLMChat = ({ persona }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage = { role: 'user', content: input, timestamp: Date.now() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    
    try {
      const formattedMessages = messages.concat(userMessage).map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      const response = await callMcpTool('call_llm_service', {
        persona: persona,
        messages: formattedMessages
      });
      
      const assistantMessage = {
        role: 'assistant',
        content: response,
        timestamp: Date.now(),
        persona: persona
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error generating response:', error);
      const errorMessage = {
        role: 'system',
        content: 'Sorry, there was an error generating a response.',
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  };
  
  return (
    <div className="llm-chat">
      <div className="messages-container">
        <AnimatePresence>
          {messages.map((msg, index) => (
            <motion.div
              key={index}
              className={`message ${msg.role} ${msg.persona || ''}`}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="message-content">{msg.content}</div>
              <div className="message-timestamp">
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isLoading && (
          <motion.div
            className="loading-indicator"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="typing-dots">
              <span></span><span></span><span></span>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder={`Chat with ${persona}...`}
          disabled={isLoading}
          className={`chat-input ${persona}`}
        />
        <motion.button
          onClick={handleSendMessage}
          disabled={isLoading || !input.trim()}
          className={`send-button ${persona}`}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          Send
        </motion.button>
      </div>
    </div>
  );
};
```

## 💬 Phase 4: Natural Language Commands (Week 7-8)

### Implementation Strategy
Create command parsing system that maps natural language to UI actions.

### Step 4.1: Create Command Parser
```python
# command_parser.py
import re
from typing import Dict, List, Tuple, Any

class CommandParser:
    def __init__(self):
        self.command_patterns = {
            "navigate": [
                r"(?:go to|open|show|navigate to) (?:the )?(.*?)(?:\s|$)",
                r"take me to (?:the )?(.*?)(?:\s|$)"
            ],
            "search": [
                r"(?:search for|find|look up) (.*)",
                r"(?:show me|get|retrieve) (?:information about|data on|results for) (.*)"
            ],
            "create": [
                r"(?:create|make|add) (?:a |new )?(.*)",
                r"(?:start|begin) (?:a |new )?(.*)"
            ],
            "update": [
                r"(?:update|change|modify|edit) (?:the )?(.*)",
                r"(?:revise|alter) (?:the )?(.*)"
            ],
            "delete": [
                r"(?:delete|remove|eliminate) (?:the )?(.*)",
                r"(?:get rid of|trash) (?:the )?(.*)"
            ]
        }
        
        self.route_mapping = {
            "home": "/",
            "dashboard": "/search", 
            "search": "/search",
            "agents": "/agents",
            "supervisors": "/supervisors",
            "projects": "/projects",
            "health": "/health",
            "personas": "/personas"
        }
    
    async def parse_command(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Parse natural language command into structured intent and actions"""
        text = text.lower().strip()
        
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    entity = match.group(1).strip()
                    
                    ui_actions = self._generate_ui_actions(intent, entity, context)
                    confidence = self._calculate_confidence(text, intent, entity)
                    
                    return {
                        "intent": intent,
                        "entity": entity,
                        "confidence": confidence,
                        "ui_actions": ui_actions,
                        "original_text": text
                    }
        
        # Default to search if no pattern matches
        return {
            "intent": "search",
            "entity": text,
            "confidence": 0.5,
            "ui_actions": [{"type": "search", "query": text}],
            "original_text": text
        }
    
    def _generate_ui_actions(self, intent: str, entity: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate UI actions based on intent and entity"""
        if intent == "navigate":
            route = self.route_mapping.get(entity.lower(), f"/search?q={entity}")
            return [{"type": "navigate", "route": route}]
        
        elif intent == "search":
            return [{"type": "search", "query": entity}]
        
        elif intent == "create":
            if "agent" in entity:
                return [{"type": "navigate", "route": "/agents"}, {"type": "create_agent"}]
            elif "project" in entity:
                return [{"type": "navigate", "route": "/projects"}, {"type": "create_project"}]
            else:
                return [{"type": "search", "query": f"create {entity}"}]
        
        # Add more intent handlers as needed
        return [{"type": "search", "query": entity}]
    
    def _calculate_confidence(self, text: str, intent: str, entity: str) -> float:
        """Calculate confidence score for the parsed command"""
        # Simple confidence calculation based on pattern match quality
        if len(entity) > 0 and entity in text:
            return 0.8
        return 0.6
```

### Step 4.2: Add Command Parsing MCP Tool
```python
# Add to mcp_unified_server.py
types.Tool(
    name="parse_nl_command",
    description="Parse natural language command into UI actions",
    inputSchema={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
            "context": {"type": "object"}
        },
        "required": ["text"]
    }
)
```

### Step 4.3: Create Command Bar Component
```javascript
// src/components/ui/CommandBar.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { callMcpTool } from '../../services/mcpService';

export const CommandBar = ({ persona, onCommand }) => {
  const [command, setCommand] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const navigate = useNavigate();
  
  const executeUIActions = async (actions) => {
    const results = [];
    
    for (const action of actions) {
      try {
        switch (action.type) {
          case 'navigate':
            navigate(action.route);
            results.push({ action, success: true });
            break;
          
          case 'search':
            // Trigger search in current component
            if (onCommand) {
              onCommand({ type: 'search', query: action.query });
            }
            results.push({ action, success: true });
            break;
          
          case 'create_agent':
            // Trigger agent creation flow
            if (onCommand) {
              onCommand({ type: 'create_agent' });
            }
            results.push({ action, success: true });
            break;
          
          default:
            results.push({ action, success: false, error: 'Unknown action type' });
        }
      } catch (error) {
        results.push({ action, success: false, error: error.message });
      }
    }
    
    return results;
  };
  
  const handleCommandSubmit = async (e) => {
    e.preventDefault();
    
    if (!command.trim()) return;
    
    setIsProcessing(true);
    setFeedback(null);
    
    try {
      const parseResult = await callMcpTool('parse_nl_command', {
        text: command,
        persona: persona,
        context: {
          currentPath: window.location.pathname,
          timestamp: new Date().toISOString()
        }
      });
      
      const parsedCommand = JSON.parse(parseResult);
      
      if (parsedCommand.ui_actions && parsedCommand.ui_actions.length > 0) {
        const executionResults = await executeUIActions(parsedCommand.ui_actions);
        
        const successCount = executionResults.filter(r => r.success).length;
        
        setFeedback({
          type: successCount === executionResults.length ? 'success' : 'warning',
          message: `Executed ${successCount}/${executionResults.length} actions for "${parsedCommand.intent}"`,
          confidence: parsedCommand.confidence
        });
      } else {
        setFeedback({
          type: 'info',
          message: `Understood as "${parsedCommand.intent}" but no actions available.`,
          confidence: parsedCommand.confidence
        });
      }
      
      setCommand('');
    } catch (error) {
      console.error('Error processing command:', error);
      setFeedback({
        type: 'error',
        message: 'Error processing command',
        confidence: 0
      });
    } finally {
      setIsProcessing(false);
    }
  };
  
  return (
    <motion.div 
      className="command-bar"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <form onSubmit={handleCommandSubmit} className="command-form">
        <input
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder={`Tell ${persona} what to do...`}
          disabled={isProcessing}
          className={`command-input ${persona}`}
        />
        <motion.button
          type="submit"
          disabled={isProcessing || !command.trim()}
          className={`command-button ${persona}`}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {isProcessing ? 'Processing...' : 'Execute'}
        </motion.button>
      </form>
      
      {feedback && (
        <motion.div
          className={`command-feedback ${feedback.type}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="feedback-message">{feedback.message}</div>
          <div className="feedback-confidence">
            Confidence: {Math.round(feedback.confidence * 100)}%
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};
```

## 🧠 Phase 5: Advanced Context (Week 9-10)

### Implementation Strategy
Enhance memory system access and create cross-persona collaboration interfaces.

### Step 5.1: Add Memory Context MCP Tool
```python
# Add to mcp_unified_server.py
types.Tool(
    name="get_memory_context",
    description="Get memory context for UI display",
    inputSchema={
        "type": "object",
        "properties": {
            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
            "context_type": {"type": "string", "enum": ["active", "shared", "long_term", "all"]},
            "detail_level": {"type": "string", "enum": ["summary", "detailed", "full"]}
        },
        "required": ["persona"]
    }
)
```

### Step 5.2: Create Context Visualizer Component
```javascript
// src/components/context/ContextVisualizer.jsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { callMcpTool } from '../../services/mcpService';

export const ContextVisualizer = ({ 
  persona, 
  contextType = 'active', 
  detailLevel = 'summary' 
}) => {
  const [contextData, setContextData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const fetchContext = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await callMcpTool('get_memory_context', {
        persona: persona,
        context_type: contextType,
        detail_level: detailLevel
      });
      
      setContextData(JSON.parse(result));
    } catch (error) {
      console.error('Error fetching context:', error);
      setError('Failed to load context data');
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    fetchContext();
  }, [persona, contextType, detailLevel]);
  
  const renderContextItem = (key, value, index) => (
    <motion.div
      key={key}
      className="context-item"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <div className="context-key">{key}</div>
      <div className="context-value">
        {typeof value === 'object' ? JSON.stringify(value, null, 2) : value}
      </div>
    </motion.div>
  );
  
  return (
    <div className={`context-visualizer ${persona}`}>
      <div className="context-header">
        <h3>Memory Context: {contextType}</h3>
        <motion.button
          onClick={fetchContext}
          disabled={isLoading}
          className="refresh-button"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {isLoading ? '⟳' : '↻'} Refresh
        </motion.button>
      </div>
      
      <div className="context-content">
        {isLoading ? (
          <motion.div
            className="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            Loading context data...
          </motion.div>
        ) : error ? (
          <motion.div
            className="error"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {error}
          </motion.div>
        ) : contextData ? (
          <motion.div
            className="context-data"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <AnimatePresence>
              {Object.entries(contextData).map(([key, value], index) =>
                renderContextItem(key, value, index)
              )}
            </AnimatePresence>
          </motion.div>
        ) : null}
      </div>
    </div>
  );
};
```

### Step 5.3: Create Cross-Persona Collaboration Panel
```javascript
// src/components/collaboration/CollaborationPanel.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { callMcpTool } from '../../services/mcpService';

export const CollaborationPanel = ({ primaryPersona }) => {
  const [query, setQuery] = useState('');
  const [domains, setDomains] = useState([]);
  const [collaborationType, setCollaborationType] = useState('consultation');
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const availableDomains = [
    { id: 'project_coordination', name: 'Project Coordination', persona: 'cherry' },
    { id: 'financial_services', name: 'Financial Services', persona: 'sophia' },
    { id: 'medical_coding', name: 'Medical Coding', persona: 'karen' },
    { id: 'technical', name: 'Technical Development', persona: 'system' },
    { id: 'creative', name: 'Creative Design', persona: 'system' }
  ];
  
  const handleDomainToggle = (domainId) => {
    setDomains(prev => 
      prev.includes(domainId) 
        ? prev.filter(d => d !== domainId)
        : [...prev, domainId]
    );
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim() || domains.length === 0) return;
    
    setIsLoading(true);
    setResult(null);
    
    try {
      const response = await callMcpTool('cross_domain_query', {
        primary_persona: primaryPersona,
        query: query,
        required_domains: domains,
        collaboration_type: collaborationType
      });
      
      setResult(JSON.parse(response));
    } catch (error) {
      console.error('Error in cross-domain query:', error);
      setResult({
        error: 'Failed to process cross-domain query',
        details: error.message
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <motion.div
      className="collaboration-panel"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h3>Cross-Persona Collaboration</h3>
      
      <form onSubmit={handleSubmit} className="collaboration-form">
        <div className="form-group">
          <label>Query:</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your cross-domain query..."
            rows={3}
            className="query-input"
          />
        </div>
        
        <div className="form-group">
          <label>Required Domains:</label>
          <div className="domain-toggles">
            {availableDomains.map(domain => (
              <motion.label
                key={domain.id}
                className={`domain-toggle ${domains.includes(domain.id) ? 'selected' : ''}`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <input
                  type="checkbox"
                  checked={domains.includes(domain.id)}
                  onChange={() => handleDomainToggle(domain.id)}
                />
                <span className={`domain-name ${domain.persona}`}>
                  {domain.name}
                </span>
              </motion.label>
            ))}
          </div>
        </div>
        
        <div className="form-group">
          <label>Collaboration Type:</label>
          <select
            value={collaborationType}
            onChange={(e) => setCollaborationType(e.target.value)}
            className="collaboration-type-select"
          >
            <option value="consultation">Consultation</option>
            <option value="coordination">Coordination</option>
            <option value="synthesis">Synthesis</option>
          </select>
        </div>
        
        <motion.button
          type="submit"
          disabled={isLoading || !query.trim() || domains.length === 0}
          className={`submit-button ${primaryPersona}`}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {isLoading ? 'Processing...' : 'Submit Query'}
        </motion.button>
      </form>
      
      {result && (
        <motion.div
          className="collaboration-result"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {result.error ? (
            <div className="error-result">
              <h4>Error</h4>
              <p>{result.error}</p>
              {result.details && <p className="error-details">{result.details}</p>}
            </div>
          ) : (
            <div className="success-result">
              <h4>Collaboration Result</h4>
              <div className="result-content">
                {result.response || result.content || JSON.stringify(result, null, 2)}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};
```

## 🔄 Phase 6: Integration & Testing (Week 11-12)

### Step 6.1: Create Feature Integration Component
```javascript
// src/components/integration/FeatureHub.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { VoiceInput } from '../ui/VoiceInput';
import { CommandBar } from '../ui/CommandBar';
import { LLMChat } from '../chat/LLMChat';
import { ContextVisualizer } from '../context/ContextVisualizer';
import { CollaborationPanel } from '../collaboration/CollaborationPanel';

export const FeatureHub = ({ persona }) => {
  const [activeFeature, setActiveFeature] = useState('chat');
  const [commandResult, setCommandResult] = useState(null);
  
  const features = [
    { id: 'chat', name: 'LLM Chat', icon: '💬' },
    { id: 'voice', name: 'Voice Input', icon: '🎤' },
    { id: 'commands', name: 'Natural Commands', icon: '⌨️' },
    { id: 'context', name: 'Memory Context', icon: '🧠' },
    { id: 'collaboration', name: 'Cross-Persona', icon: '🤝' }
  ];
  
  const handleCommand = (result) => {
    setCommandResult(result);
    // Handle command execution results
  };
  
  const renderActiveFeature = () => {
    switch (activeFeature) {
      case 'chat':
        return <LLMChat persona={persona} />;
      case 'voice':
        return <VoiceInput persona={persona} onCommand={handleCommand} />;
      case 'commands':
        return <CommandBar persona={persona} onCommand={handleCommand} />;
      case 'context':
        return <ContextVisualizer persona={persona} />;
      case 'collaboration':
        return <CollaborationPanel primaryPersona={persona} />;
      default:
        return <LLMChat persona={persona} />;
    }
  };
  
  return (
    <div className="feature-hub">
      <div className="feature-tabs">
        {features.map(feature => (
          <motion.button
            key={feature.id}
            className={`feature-tab ${activeFeature === feature.id ? 'active' : ''} ${persona}`}
            onClick={() => setActiveFeature(feature.id)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <span className="feature-icon">{feature.icon}</span>
            <span className="feature-name">{feature.name}</span>
          </motion.button>
        ))}
      </div>
      
      <motion.div
        className="feature-content"
        key={activeFeature}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {renderActiveFeature()}
      </motion.div>
      
      {commandResult && (
        <motion.div
          className="command-result"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          Command executed: {JSON.stringify(commandResult, null, 2)}
        </motion.div>
      )}
    </div>
  );
};
```

## 📊 Implementation Timeline

### Week 1-2: Enhanced Animations
- ✅ Install Framer Motion
- ✅ Create animation hooks and components
- ✅ Integrate with existing UI components
- ✅ Test performance and accessibility

### Week 3-4: Voice Recognition
- ✅ Implement Web Speech API service
- ✅ Add voice MCP tool
- ✅ Create voice UI components
- ✅ Test cross-browser compatibility

### Week 5-6: LLM Integration
- ✅ Create LLM service manager
- ✅ Add LLM MCP tools
- ✅ Implement chat components
- ✅ Test with multiple providers

### Week 7-8: Natural Language Commands
- ✅ Create command parser
- ✅ Add command parsing MCP tool
- ✅ Implement command bar UI
- ✅ Test command recognition accuracy

### Week 9-10: Advanced Context
- ✅ Add memory context MCP tools
- ✅ Create context visualization
- ✅ Implement collaboration panel
- ✅ Test cross-persona interactions

### Week 11-12: Integration & Testing
- ✅ Integrate all features
- ✅ Create unified feature hub
- ✅ Comprehensive testing
- ✅ Performance optimization

## 🎯 Success Metrics

### Performance Targets
- **Animation Performance**: 60fps on all interactions
- **Voice Recognition**: <2s response time
- **LLM Integration**: <3s average response time
- **Command Processing**: <1s parsing and execution
- **Context Loading**: <500ms for summary data

### User Experience Goals
- **Seamless Integration**: All features work together naturally
- **Persona Consistency**: Each persona maintains unique behavior
- **Accessibility**: Full keyboard and screen reader support
- **Mobile Compatibility**: Responsive design for all features

## 🚀 Getting Started

To begin implementation:

1. **Ensure Prerequisites**:
   ```bash
   # API running on port 8010 ✅
   # Admin interface running on port 5173/5174 ✅
   # MCP server operational ✅
   ```

2. **Start with Phase 1**:
   ```bash
   cd admin-interface
   npm install framer-motion
   ```

3. **Follow Implementation Steps**: Each phase builds on the previous one

4. **Test Incrementally**: Verify each feature before moving to the next

This implementation plan provides a clear roadmap for integrating all five next phase features into Orchestra AI while maintaining the existing architecture and ensuring optimal performance. 