'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { LoginForm } from '@/components/auth/LoginForm';
import { MainLayout } from '@/components/layout/MainLayout';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { DashboardOverview } from '@/components/dashboard/DashboardOverview';

export default function HomePage() {
  const { isAuthenticated, user } = useAuth();
  const [activeView, setActiveView] = useState<'chat' | 'dashboard'>('chat');

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  return (
    <MainLayout>
      <div className="flex flex-col h-full">
        {/* Header with view toggle */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                🍒 Cherry AI Orchestrator
              </h1>
              <p className="text-sm text-gray-600">
                Welcome back, {user?.name || 'User'}! How can I help you today?
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setActiveView('chat')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeView === 'chat'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                💬 Chat
              </button>
              <button
                onClick={() => setActiveView('dashboard')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeView === 'dashboard'
                    ? 'bg-indigo-100 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                📊 Dashboard
              </button>
            </div>
          </div>
        </div>

        {/* Main content area */}
        <div className="flex-1 overflow-hidden">
          {activeView === 'chat' ? (
            <ChatInterface />
          ) : (
            <DashboardOverview />
          )}
        </div>
      </div>
    </MainLayout>
  );
}

