'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'react-hot-toast';
import { Eye, EyeOff, Cherry, Sparkles, Brain } from 'lucide-react';

export function LoginForm() {
  const { login, loading } = useAuth();
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!credentials.username || !credentials.password) {
      toast.error('Please enter both username and password');
      return;
    }

    const success = await login(credentials);
    
    if (success) {
      toast.success('Welcome to Cherry AI Orchestrator!');
    } else {
      toast.error('Invalid credentials. Please try again.');
    }
  };

  const quickLogin = (username: string, password: string) => {
    setCredentials({ username, password });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="max-w-md w-full space-y-8 p-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex justify-center items-center space-x-2 mb-4">
            <Cherry className="h-12 w-12 text-cherry-500" />
            <h1 className="text-3xl font-bold text-gray-900">Cherry AI</h1>
          </div>
          <h2 className="text-xl text-gray-600">Orchestrator Admin Interface</h2>
          <p className="mt-2 text-sm text-gray-500">
            Manage your AI domains: Cherry, Sophia, and Karen
          </p>
        </div>

        {/* Login Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={credentials.username}
                onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter your username"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={credentials.password}
                  onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                  className="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="loading-spinner mr-2"></div>
                  Signing in...
                </div>
              ) : (
                'Sign in'
              )}
            </button>
          </div>
        </form>

        {/* Quick Login Options */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-4">Quick Login Options:</h3>
          <div className="space-y-2">
            <button
              onClick={() => quickLogin('admin', 'OrchAI_Admin2024!')}
              className="w-full flex items-center justify-between p-3 text-left border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center">
                <Sparkles className="h-5 w-5 text-purple-500 mr-3" />
                <div>
                  <div className="font-medium text-gray-900">Administrator</div>
                  <div className="text-sm text-gray-500">Full access to all domains</div>
                </div>
              </div>
            </button>
            
            <button
              onClick={() => quickLogin('cherry', 'Cherry_AI_2024!')}
              className="w-full flex items-center justify-between p-3 text-left border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center">
                <Cherry className="h-5 w-5 text-cherry-500 mr-3" />
                <div>
                  <div className="font-medium text-gray-900">Cherry User</div>
                  <div className="text-sm text-gray-500">Personal domain access</div>
                </div>
              </div>
            </button>
            
            <button
              onClick={() => quickLogin('demo', 'demo123')}
              className="w-full flex items-center justify-between p-3 text-left border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center">
                <Brain className="h-5 w-5 text-blue-500 mr-3" />
                <div>
                  <div className="font-medium text-gray-900">Demo User</div>
                  <div className="text-sm text-gray-500">Limited access for testing</div>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          <p>Cherry AI Orchestrator v1.0</p>
          <p>Intelligent Orchestration Platform</p>
        </div>
      </div>
    </div>
  );
}

