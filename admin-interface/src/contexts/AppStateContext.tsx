'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface AppState {
  currentDomain: 'cherry' | 'sophia' | 'karen' | null;
  isLoading: boolean;
  notifications: Notification[];
  preferences: UserPreferences;
}

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  timestamp: Date;
  read: boolean;
}

interface UserPreferences {
  theme: 'light' | 'dark';
  language: string;
  notifications: boolean;
  autoSave: boolean;
}

interface AppStateContextType {
  state: AppState;
  setCurrentDomain: (domain: 'cherry' | 'sophia' | 'karen' | null) => void;
  setLoading: (loading: boolean) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markNotificationRead: (id: string) => void;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
}

const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

const defaultPreferences: UserPreferences = {
  theme: 'light',
  language: 'en',
  notifications: true,
  autoSave: true,
};

export function AppStateProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AppState>({
    currentDomain: null,
    isLoading: false,
    notifications: [],
    preferences: defaultPreferences,
  });

  useEffect(() => {
    // Load preferences from localStorage
    const savedPreferences = localStorage.getItem('cherry-ai-preferences');
    if (savedPreferences) {
      try {
        const preferences = JSON.parse(savedPreferences);
        setState(prev => ({ ...prev, preferences: { ...defaultPreferences, ...preferences } }));
      } catch (error) {
        console.error('Error loading preferences:', error);
      }
    }
  }, []);

  const setCurrentDomain = (domain: 'cherry' | 'sophia' | 'karen' | null) => {
    setState(prev => ({ ...prev, currentDomain: domain }));
  };

  const setLoading = (loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  };

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false,
    };

    setState(prev => ({
      ...prev,
      notifications: [newNotification, ...prev.notifications].slice(0, 50), // Keep only last 50
    }));
  };

  const markNotificationRead = (id: string) => {
    setState(prev => ({
      ...prev,
      notifications: prev.notifications.map(notif =>
        notif.id === id ? { ...notif, read: true } : notif
      ),
    }));
  };

  const updatePreferences = (newPreferences: Partial<UserPreferences>) => {
    const updatedPreferences = { ...state.preferences, ...newPreferences };
    setState(prev => ({ ...prev, preferences: updatedPreferences }));
    localStorage.setItem('cherry-ai-preferences', JSON.stringify(updatedPreferences));
  };

  const value = {
    state,
    setCurrentDomain,
    setLoading,
    addNotification,
    markNotificationRead,
    updatePreferences,
  };

  return (
    <AppStateContext.Provider value={value}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppStateProvider');
  }
  return context;
}

