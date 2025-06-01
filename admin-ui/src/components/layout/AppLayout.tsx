import React from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import ContextualMemoryPanel from './ContextualMemoryPanel';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(true); // Default to open for desktop

  return (
    <div className="flex h-screen bg-background text-foreground">
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 bg-muted/30">
          {children}
        </main>
      </div>
      <div className="hidden lg:flex lg:w-72 xl:w-80 flex-shrink-0 flex-col border-l border-border dark:border-gray-700">
        <ContextualMemoryPanel />
      </div>
    </div>
  );
};

export default AppLayout;
