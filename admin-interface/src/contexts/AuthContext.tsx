'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
  domains: ('cherry' | 'sophia' | 'karen')[];
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
}

interface LoginCredentials {
  username: string;
  password: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Mock user data - in production this would come from your backend
const MOCK_USERS = {
  admin: {
    id: '1',
    name: 'Administrator',
    email: 'admin@cherry-ai.me',
    role: 'admin' as const,
    domains: ['cherry', 'sophia', 'karen'] as ('cherry' | 'sophia' | 'karen')[],
    password: 'OrchAI_Admin2024!',
  },
  cherry: {
    id: '2',
    name: 'Cherry User',
    email: 'cherry@cherry-ai.me',
    role: 'user' as const,
    domains: ['cherry'] as ('cherry' | 'sophia' | 'karen')[],
    password: 'Cherry_AI_2024!',
  },
  demo: {
    id: '3',
    name: 'Demo User',
    email: 'demo@cherry-ai.me',
    role: 'user' as const,
    domains: ['cherry', 'sophia'] as ('cherry' | 'sophia' | 'karen')[],
    password: 'demo123',
  },
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for stored authentication
    const storedUser = localStorage.getItem('cherry-ai-user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Error parsing stored user:', error);
        localStorage.removeItem('cherry-ai-user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    setLoading(true);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const mockUser = MOCK_USERS[credentials.username as keyof typeof MOCK_USERS];
    
    if (mockUser && mockUser.password === credentials.password) {
      const { password, ...userWithoutPassword } = mockUser;
      setUser(userWithoutPassword);
      localStorage.setItem('cherry-ai-user', JSON.stringify(userWithoutPassword));
      setLoading(false);
      return true;
    }
    
    setLoading(false);
    return false;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('cherry-ai-user');
  };

  const value = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

