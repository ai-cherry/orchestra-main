import React from 'react';
import { cn } from '@/lib/utils';

interface OrchestraButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'icon';
  loading?: boolean;
  children: React.ReactNode;
}

export const OrchestraButton: React.FC<OrchestraButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  className,
  disabled,
  children,
  ...props
}) => {
  const baseStyles = `
    inline-flex items-center justify-center
    font-medium rounded-lg
    transition-all duration-200 ease-out
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orchestra-primary
    disabled:opacity-50 disabled:cursor-not-allowed
    transform hover:scale-105 active:scale-95
  `;

  const variants = {
    primary: `
      bg-orchestra-primary text-white
      hover:bg-orchestra-primary-hover
      shadow-md hover:shadow-lg
    `,
    secondary: `
      bg-white text-orchestra-gray-700
      border border-orchestra-gray-300
      hover:bg-orchestra-gray-50 hover:border-orchestra-gray-400
      shadow-sm hover:shadow-md
    `,
    ghost: `
      bg-transparent text-orchestra-gray-600
      hover:bg-orchestra-gray-100 hover:text-orchestra-gray-800
    `,
    danger: `
      bg-orchestra-error text-white
      hover:bg-red-700
      shadow-md hover:shadow-lg
    `,
    success: `
      bg-orchestra-accent text-white
      hover:bg-orchestra-accent-hover
      shadow-md hover:shadow-lg
    `
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
    xl: 'px-8 py-4 text-xl',
    icon: 'p-2'
  };

  return (
    <button
      className={cn(
        baseStyles,
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg 
          className="animate-spin -ml-1 mr-2 h-4 w-4" 
          fill="none" 
          viewBox="0 0 24 24"
        >
          <circle 
            className="opacity-25" 
            cx="12" 
            cy="12" 
            r="10" 
            stroke="currentColor" 
            strokeWidth="4"
          />
          <path 
            className="opacity-75" 
            fill="currentColor" 
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}; 