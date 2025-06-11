import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  persona: string;
  searchMode?: string;
  attachments?: string[];
  metadata?: {
    tokens?: number;
    model?: string;
    responseTime?: number;
  };
}

export interface ChatSession {
  id: string;
  name: string;
  persona: string;
  messages: ChatMessage[];
  createdAt: string;
  lastActivity: string;
}

interface ChatState {
  activePersona: string;
  messages: ChatMessage[];
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  error: string | null;
  searchMode: string;
  lastApiCall: string | null;
  totalMessages: number;
  totalSessions: number;
  analytics: {
    messagesThisHour: number;
    averageResponseTime: number;
    preferredPersona: string;
    mostUsedSearchMode: string;
  };
}

const initialState: ChatState = {
  activePersona: 'cherry',
  messages: [
    {
      id: 'welcome-1',
      role: 'assistant',
      content: "Hi! I'm Cherry, your creative AI assistant. How can I help you today? 🍒",
      timestamp: new Date().toISOString(),
      persona: 'cherry',
      searchMode: 'normal'
    }
  ],
  sessions: [],
  currentSessionId: null,
  isLoading: false,
  error: null,
  searchMode: 'normal',
  lastApiCall: null,
  totalMessages: 1,
  totalSessions: 0,
  analytics: {
    messagesThisHour: 0,
    averageResponseTime: 0,
    preferredPersona: 'cherry',
    mostUsedSearchMode: 'normal'
  }
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setActivePersona: (state, action: PayloadAction<string>) => {
      const previousPersona = state.activePersona;
      state.activePersona = action.payload;
      
      // Add welcome message from new persona if switching
      if (previousPersona !== action.payload) {
        const welcomeMessages = {
          cherry: "Hi! I'm Cherry, your creative AI assistant. Ready to get creative? 🍒",
          sophia: "Hello! I'm Sophia, your business strategist. Let's tackle your professional challenges. 💼",
          karen: "Greetings! I'm Karen, your healthcare specialist. How can I assist with your medical needs? 🏥"
        };
        
        const welcomeMessage: ChatMessage = {
          id: `welcome-${Date.now()}`,
          role: 'assistant',
          content: welcomeMessages[action.payload as keyof typeof welcomeMessages] || 'Hello! How can I help you?',
          timestamp: new Date().toISOString(),
          persona: action.payload,
          searchMode: state.searchMode
        };
        
        state.messages.push(welcomeMessage);
        state.totalMessages += 1;
      }
    },
    
    addMessage: (state, action: PayloadAction<ChatMessage>) => {
      state.messages.push(action.payload);
      state.totalMessages += 1;
      state.lastApiCall = new Date().toISOString();
      
      // Update analytics
      if (action.payload.role === 'user') {
        state.analytics.messagesThisHour += 1;
      }
      
      if (action.payload.metadata?.responseTime) {
        const currentAvg = state.analytics.averageResponseTime;
        const newResponseTime = action.payload.metadata.responseTime;
        state.analytics.averageResponseTime = currentAvg > 0 
          ? (currentAvg + newResponseTime) / 2 
          : newResponseTime;
      }
    },
    
    updateMessage: (state, action: PayloadAction<{ id: string; updates: Partial<ChatMessage> }>) => {
      const messageIndex = state.messages.findIndex(msg => msg.id === action.payload.id);
      if (messageIndex !== -1) {
        state.messages[messageIndex] = { ...state.messages[messageIndex], ...action.payload.updates };
      }
    },
    
    removeMessage: (state, action: PayloadAction<string>) => {
      state.messages = state.messages.filter(msg => msg.id !== action.payload);
      state.totalMessages = state.messages.length;
    },
    
    clearHistory: (state) => {
      const welcomeMessages = {
        cherry: "Hi! I'm Cherry, your creative AI assistant. How can I help you today? 🍒",
        sophia: "Hello! I'm Sophia, your business strategist. Let's tackle your professional challenges. 💼",
        karen: "Greetings! I'm Karen, your healthcare specialist. How can I assist with your medical needs? 🏥"
      };
      
      state.messages = [{
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: welcomeMessages[state.activePersona as keyof typeof welcomeMessages] || 'Hello! How can I help you?',
        timestamp: new Date().toISOString(),
        persona: state.activePersona,
        searchMode: state.searchMode
      }];
      state.totalMessages = 1;
    },
    
    setSearchMode: (state, action: PayloadAction<string>) => {
      state.searchMode = action.payload;
      state.analytics.mostUsedSearchMode = action.payload;
    },
    
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    
    createSession: (state, action: PayloadAction<{ name: string; persona: string }>) => {
      const newSession: ChatSession = {
        id: `session-${Date.now()}`,
        name: action.payload.name,
        persona: action.payload.persona,
        messages: [],
        createdAt: new Date().toISOString(),
        lastActivity: new Date().toISOString()
      };
      
      state.sessions.push(newSession);
      state.currentSessionId = newSession.id;
      state.totalSessions += 1;
    },
    
    switchSession: (state, action: PayloadAction<string>) => {
      const session = state.sessions.find(s => s.id === action.payload);
      if (session) {
        state.currentSessionId = action.payload;
        state.messages = [...session.messages];
        state.activePersona = session.persona;
      }
    },
    
    saveCurrentSession: (state) => {
      if (state.currentSessionId) {
        const sessionIndex = state.sessions.findIndex(s => s.id === state.currentSessionId);
        if (sessionIndex !== -1) {
          state.sessions[sessionIndex].messages = [...state.messages];
          state.sessions[sessionIndex].lastActivity = new Date().toISOString();
        }
      }
    },
    
    deleteSession: (state, action: PayloadAction<string>) => {
      state.sessions = state.sessions.filter(s => s.id !== action.payload);
      if (state.currentSessionId === action.payload) {
        state.currentSessionId = null;
      }
      state.totalSessions = state.sessions.length;
    },
    
    updateAnalytics: (state, action: PayloadAction<Partial<ChatState['analytics']>>) => {
      state.analytics = { ...state.analytics, ...action.payload };
    },
    
    resetAnalytics: (state) => {
      state.analytics = {
        messagesThisHour: 0,
        averageResponseTime: 0,
        preferredPersona: state.activePersona,
        mostUsedSearchMode: state.searchMode
      };
    }
  }
});

export const {
  setActivePersona,
  addMessage,
  updateMessage,
  removeMessage,
  clearHistory,
  setSearchMode,
  setLoading,
  setError,
  createSession,
  switchSession,
  saveCurrentSession,
  deleteSession,
  updateAnalytics,
  resetAnalytics
} = chatSlice.actions;

export default chatSlice.reducer; 