import React from 'react';

interface PageWrapperProps {
  children: React.ReactNode;
  title?: string; // Optional title to display
}

const PageWrapper: React.FC<PageWrapperProps> = ({ children, title }) => {
  return (
    <div className="container mx-auto py-6 px-4 sm:px-6 lg:px-8">
      {title && (
        <h1 className="text-3xl font-bold tracking-tight text-foreground mb-6">
          {title}
        </h1>
      )}
      <div className="bg-card text-card-foreground shadow-sm rounded-lg p-6">
        {children}
      </div>
    </div>
  );
};

export default PageWrapper;
