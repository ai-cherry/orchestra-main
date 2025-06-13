import { createContext, useContext, useState, ReactNode } from 'react';

interface AppContextType {
  // Define your shared state and functions here
  // For now, we'll keep it simple as a placeholder
  isAuthenticated: boolean;
  setAuthentication: (status: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [isAuthenticated, setAuthentication] = useState(false);

  const value = {
    isAuthenticated,
    setAuthentication,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}; 