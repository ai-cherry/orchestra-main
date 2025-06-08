import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import ServiceManager from '../services/ServiceManager';

interface WebSocketContextType {
  socket: WebSocket | null;
  isConnected: boolean;
  sendMessage: (message: any) => void;
  subscribe: (event: string, callback: (data: any) => void) => void;
  unsubscribe: (event: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [eventListeners, setEventListeners] = useState<Map<string, Set<(data: any) => void>>>(new Map());

  useEffect(() => {
    const serviceManager = ServiceManager.getInstance();
    const config = serviceManager.getPortkeyService(); // Get config through service manager
    const wsUrl = process.env.NODE_ENV === 'production' 
      ? 'wss://ws.orchestra-ai.com'
      : 'ws://localhost:3001';

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setSocket(ws);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setSocket(null);
      
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        console.log('Attempting to reconnect...');
        // Recursive call to re-establish connection
      }, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const { type, payload } = data;
        
        // Notify all listeners for this event type
        const listeners = eventListeners.get(type);
        if (listeners) {
          listeners.forEach(callback => callback(payload));
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = (message: any) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  };

  const subscribe = (event: string, callback: (data: any) => void) => {
    setEventListeners(prev => {
      const newListeners = new Map(prev);
      if (!newListeners.has(event)) {
        newListeners.set(event, new Set());
      }
      newListeners.get(event)!.add(callback);
      return newListeners;
    });
  };

  const unsubscribe = (event: string) => {
    setEventListeners(prev => {
      const newListeners = new Map(prev);
      newListeners.delete(event);
      return newListeners;
    });
  };

  const value = {
    socket,
    isConnected,
    sendMessage,
    subscribe,
    unsubscribe
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
};

