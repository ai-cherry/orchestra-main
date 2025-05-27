import React from 'react';
import { cn } from '@/lib/utils';

interface StatusIndicatorProps {
  status: 'info' | 'warn' | 'error' | 'active' | 'idle' | 'offline' | string; // Allow specific log levels and general statuses
  text?: string; // Optional text to display (e.g., "INFO", "WARN")
  className?: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, text, className }) => {
  let colorClass = '';
  const lowerStatus = status.toLowerCase();

  switch (lowerStatus) {
    case 'info':
      colorClass = 'bg-blue-500'; // Blue for INFO
      break;
    case 'warn':
    case 'warning': // Allow 'warning' as well
    case 'idle':    // Keep 'idle' for yellow if used elsewhere
    case 'pending':
      colorClass = 'bg-yellow-500'; // Yellow for WARN
      break;
    case 'error':
    case 'failed':
      colorClass = 'bg-red-500'; // Red for ERROR
      break;
    case 'active':
    case 'online':
    case 'healthy':
    case 'success': // Add success for green
      colorClass = 'bg-green-500'; // Green for active/healthy
      break;
    case 'offline':
    case 'unavailable':
      colorClass = 'bg-gray-400';
      break;
    default:
      colorClass = 'bg-gray-300'; // Default for unknown statuses
  }

  const displayText = text !== undefined ? text : status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();

  return (
    <div className={cn("flex items-center", className)}>
      <span className={`h-3 w-3 rounded-full mr-2 shrink-0 ${colorClass}`} /> {/* Added shrink-0 to prevent dot from shrinking */}
      <span className="text-sm">{displayText}</span>
    </div>
  );
};

export default StatusIndicator;
