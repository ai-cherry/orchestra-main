import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'; // Assuming card is already added
import { LucideIcon } from 'lucide-react';

interface MetricsDisplayCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
  description?: string; // Optional description or sub-text
  colorClassName?: string; // Optional color for the icon, e.g., "text-green-500"
}

const MetricsDisplayCard: React.FC<MetricsDisplayCardProps> = ({
  title,
  value,
  icon: Icon,
  description,
  colorClassName = 'text-theme-accent-primary', // Default to theme accent
}) => {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={`h-5 w-5 ${colorClassName}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </CardContent>
    </Card>
  );
};

export default MetricsDisplayCard;
