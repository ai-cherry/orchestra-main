import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { ServiceManager } from '../services/ServiceManager';
import CryptoJS from 'crypto-js';

interface AuthUser {
  id: string;
  email: string;
  name: string;
  preferences: Record<string, any>;
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updatePreferences: (preferences: Record<string, any>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const ENCRYPTION_KEY = process.env.VITE_ENCRYPTION_KEY || 'default-dev-key';

function encrypt(text: string): string {
  return CryptoJS.AES.encrypt(text, ENCRYPTION_KEY).toString();
}

function decrypt(cipher: string): string {
  const bytes = CryptoJS.AES.decrypt(cipher, ENCRYPTION_KEY);
  return bytes.toString(CryptoJS.enc.Utf8);
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const serviceManager = ServiceManager.getInstance();

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      try {
        const token = (() => {
          const enc = localStorage.getItem('auth_token');
          return enc ? decrypt(enc) : null;
        })();
        if (token) {
          // Validate token and get user info
          const userData = await validateToken(token);
          setUser(userData);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('auth_token');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const validateToken = async (token: string): Promise<AuthUser> => {
    // For single-user deployment, return default user
    return {
      id: 'default-user',
      email: 'admin@cherry-ai.me',
      name: 'Orchestra AI Admin',
      preferences: (() => {
        const enc = localStorage.getItem('user_preferences');
        return enc ? JSON.parse(decrypt(enc)) : {};
      })()
    };
  };

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      // For single-user deployment, simple validation
      if (email === 'admin@cherry-ai.me' && password === 'OrchestraAI2024!') {
        const token = 'single-user-token';
        localStorage.setItem('auth_token', encrypt(token));
        
        const userData = await validateToken(token);
        setUser(userData);
      } else {
        throw new Error('Invalid credentials');
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_preferences');
    setUser(null);
  }, []);

  const updatePreferences = useCallback(async (preferences: Record<string, any>) => {
    if (!user) return;

    const updatedUser = { ...user, preferences };
    setUser(updatedUser);
    localStorage.setItem('user_preferences', encrypt(JSON.stringify(preferences)));
  }, [user]);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    updatePreferences
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

