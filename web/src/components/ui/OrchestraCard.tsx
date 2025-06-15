import React from 'react';
import { cn } from '@/lib/utils';

interface OrchestraCardProps {
  variant?: 'default' | 'stat' | 'feature' | 'glass';
  className?: string;
  children: React.ReactNode;
}

interface CardHeaderProps {
  className?: string;
  children: React.ReactNode;
}

interface CardContentProps {
  className?: string;
  children: React.ReactNode;
}

interface CardTitleProps {
  className?: string;
  children: React.ReactNode;
}

interface CardDescriptionProps {
  className?: string;
  children: React.ReactNode;
}

export const OrchestraCard: React.FC<OrchestraCardProps> = ({
  variant = 'default',
  className,
  children,
}) => {
  const baseStyles = `
    rounded-lg border transition-all duration-200 ease-out
    hover:shadow-md
  `;

  const variants = {
    default: `
      bg-white border-orchestra-gray-200 shadow-sm
      hover:shadow-md
    `,
    stat: `
      bg-gradient-to-br from-orchestra-primary to-orchestra-secondary
      text-white border-0 shadow-lg
      hover:shadow-xl transform hover:scale-105
    `,
    feature: `
      bg-white border-orchestra-gray-200 shadow-sm
      hover:border-orchestra-primary hover:shadow-lg
      transition-all duration-300
    `,
    glass: `
      bg-white/80 backdrop-blur-sm border-orchestra-gray-200/50
      shadow-lg hover:shadow-xl
    `
  };

  return (
    <div className={cn(baseStyles, variants[variant], className)}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<CardHeaderProps> = ({ className, children }) => (
  <div className={cn("p-6 border-b border-orchestra-gray-100", className)}>
    {children}
  </div>
);

export const CardContent: React.FC<CardContentProps> = ({ className, children }) => (
  <div className={cn("p-6", className)}>
    {children}
  </div>
);

export const CardTitle: React.FC<CardTitleProps> = ({ className, children }) => (
  <h3 className={cn("text-lg font-semibold text-orchestra-gray-900 leading-tight", className)}>
    {children}
  </h3>
);

export const CardDescription: React.FC<CardDescriptionProps> = ({ className, children }) => (
  <p className={cn("text-sm text-orchestra-gray-600 mt-1", className)}>
    {children}
  </p>
);

// Stat Card specific component
interface StatCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  trend,
  className
}) => (
  <OrchestraCard variant="stat" className={className}>
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm opacity-90">{title}</p>
          <p className="text-3xl font-bold">{value}</p>
          {trend && (
            <p className={cn(
              "text-sm mt-1 flex items-center",
              trend.isPositive ? "text-green-200" : "text-red-200"
            )}>
              <span className="mr-1">
                {trend.isPositive ? "↗" : "↘"}
              </span>
              {Math.abs(trend.value)}%
            </p>
          )}
        </div>
        {icon && (
          <div className="opacity-80">
            {icon}
          </div>
        )}
      </div>
    </CardContent>
  </OrchestraCard>
); 