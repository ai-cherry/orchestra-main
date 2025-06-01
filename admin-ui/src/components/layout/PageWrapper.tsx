import React from 'react';

interface PageWrapperProps {
  children: React.ReactNode;
  title?: string; // Optional title to display
  description?: string; // Optional description to display
}

const PageWrapper: React.FC<PageWrapperProps> = ({ children, title, description }) => {
  return (
    <div className="container mx-auto py-6 px-4 sm:px-6 lg:px-8">
      {title && (
        <div className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            {title}
          </h1>
          {description && (
            <p className="mt-2 text-lg text-muted-foreground">
              {description}
            </p>
          )}
        </div>
      )}
      <div className="bg-card text-card-foreground shadow-sm rounded-lg p-6">
        {children}
      </div>
    </div>
  );
};

export default PageWrapper;
