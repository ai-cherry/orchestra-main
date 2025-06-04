'use client';

import React from 'react';
import { AuthProvider } from '@/contexts/AuthContext';
import { AppStateProvider } from '@/contexts/AppStateContext';
import { InfrastructureProvider } from '@/contexts/InfrastructureContext';

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <AuthProvider>
      <AppStateProvider>
        <InfrastructureProvider>
          {children}
        </InfrastructureProvider>
      </AppStateProvider>
    </AuthProvider>
  );
}

