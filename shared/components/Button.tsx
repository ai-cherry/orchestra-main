import React from 'react';

export interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  onClick,
  type = 'button',
  className = '',
}) => {
  const baseStyles = `
    inline-flex items-center justify-center font-medium rounded-lg
    transition-all duration-200 ease-in-out
    focus:outline-none focus:ring-2 focus:ring-offset-2
    disabled:opacity-50 disabled:cursor-not-allowed
    ${fullWidth ? 'w-full' : ''}
  `;

  const variantStyles = {
    primary: `
      bg-gradient-to-r from-blue-600 to-blue-700 text-white
      hover:from-blue-700 hover:to-blue-800 hover:shadow-lg hover:-translate-y-0.5
      focus:ring-blue-500 active:transform active:scale-95
    `,
    secondary: `
      bg-gray-100 text-gray-900 border border-gray-300
      hover:bg-gray-200 hover:border-gray-400 hover:shadow-md
      focus:ring-gray-500 active:transform active:scale-95
    `,
    success: `
      bg-gradient-to-r from-green-600 to-green-700 text-white
      hover:from-green-700 hover:to-green-800 hover:shadow-lg hover:-translate-y-0.5
      focus:ring-green-500 active:transform active:scale-95
    `,
    warning: `
      bg-gradient-to-r from-yellow-500 to-yellow-600 text-white
      hover:from-yellow-600 hover:to-yellow-700 hover:shadow-lg hover:-translate-y-0.5
      focus:ring-yellow-500 active:transform active:scale-95
    `,
    danger: `
      bg-gradient-to-r from-red-600 to-red-700 text-white
      hover:from-red-700 hover:to-red-800 hover:shadow-lg hover:-translate-y-0.5
      focus:ring-red-500 active:transform active:scale-95
    `,
    ghost: `
      text-gray-700 border border-transparent
      hover:bg-gray-100 hover:text-gray-900
      focus:ring-gray-500 active:transform active:scale-95
    `,
  };

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-3 text-base gap-2.5',
  };

  const buttonClass = `
    ${baseStyles}
    ${variantStyles[variant]}
    ${sizeStyles[size]}
    ${className}
  `.trim().replace(/\s+/g, ' ');

  const renderIcon = () => {
    if (loading) {
      return (
        <svg
          className={`animate-spin ${size === 'sm' ? 'h-3 w-3' : size === 'lg' ? 'h-5 w-5' : 'h-4 w-4'}`}
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
      );
    }
    return icon;
  };

  return (
    <button
      type={type}
      className={buttonClass}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {iconPosition === 'left' && renderIcon()}
      <span className={loading ? 'opacity-75' : ''}>{children}</span>
      {iconPosition === 'right' && renderIcon()}
    </button>
  );
};

export default Button;

// Usage examples:
/*
<Button variant="primary" size="lg" icon={<PlusIcon />}>
  Create Workflow
</Button>

<Button variant="secondary" loading>
  Saving...
</Button>

<Button variant="success" fullWidth>
  Deploy to Production
</Button>

<Button 
  variant="danger" 
  icon={<TrashIcon />}
  iconPosition="right"
  onClick={handleDelete}
>
  Delete
</Button>
*/ 