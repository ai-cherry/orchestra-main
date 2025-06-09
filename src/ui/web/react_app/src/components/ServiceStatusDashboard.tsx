// src/components/ServiceStatusDashboard.tsx
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Button } from './ui/button';
import { ExternalLink } from 'lucide-react';

// Service configuration - easily extensible
export const services = [
  {
    name: "Vercel",
    url: "https://vercel.com/lynn-musils-projects/orchestra-ai-frontend",
    icon: "/icons/vercel.svg",
    description: "Frontend deployment status",
    status: "🟢",
    lastChecked: "2024-06-09",
    notes: "Live deployment at orchestra-ai-frontend.vercel.app"
  },
  {
    name: "Portkey",
    url: "https://dashboard.portkey.ai/projects/your-project-id",
    icon: "/icons/portkey.svg",
    description: "AI gateway and LLM routing",
    status: "🟢",
    lastChecked: "2024-06-09",
    notes: "AI gateway configured"
  },
  {
    name: "Sentry",
    url: "https://sentry.io/organizations/your-org/projects/",
    icon: "/icons/sentry.svg",
    description: "Error tracking and monitoring",
    status: "🟢",
    lastChecked: "2024-06-09",
    notes: "No errors reported"
  }
];

// Quick actions configuration
export const quickActions = [
  {
    name: "Trigger redeploy on Vercel",
    url: "https://vercel.com/lynn-musils-projects/orchestra-ai-frontend/deployments",
    status: "🟢"
  },
  {
    name: "Check Portkey LLM status",
    url: "https://dashboard.portkey.ai/projects/your-project-id",
    status: "🟢"
  },
  {
    name: "Review latest Sentry errors",
    url: "https://sentry.io/organizations/your-org/projects/",
    status: "🟢"
  }
];

// Card view component
export const ServiceCards: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {services.map((service) => (
        <Card key={service.name} className="overflow-hidden">
          <CardHeader className="flex flex-row items-center gap-2">
            {service.icon && (
              <img src={service.icon} alt={`${service.name} icon`} className="w-6 h-6" />
            )}
            <div>
              <CardTitle>{service.name}</CardTitle>
              <CardDescription>{service.description}</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">{service.status}</span>
                <span className="text-sm text-gray-500">Last checked: {service.lastChecked}</span>
              </div>
              <Button variant="outline" size="sm" asChild>
                <a href={service.url} target="_blank" rel="noopener noreferrer">
                  Open Dashboard <ExternalLink className="ml-1 w-4 h-4" />
                </a>
              </Button>
            </div>
            <p className="mt-2 text-sm text-gray-600">{service.notes}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// Table view component
export const ServiceTable: React.FC = () => {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Service</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Last Checked</TableHead>
          <TableHead>Notes</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {services.map((service) => (
          <TableRow key={service.name}>
            <TableCell className="font-medium">
              <div className="flex items-center gap-2">
                {service.icon && (
                  <img src={service.icon} alt={`${service.name} icon`} className="w-5 h-5" />
                )}
                {service.name}
              </div>
            </TableCell>
            <TableCell>{service.status}</TableCell>
            <TableCell>{service.lastChecked}</TableCell>
            <TableCell>{service.notes}</TableCell>
            <TableCell>
              <Button variant="outline" size="sm" asChild>
                <a href={service.url} target="_blank" rel="noopener noreferrer">
                  Open <ExternalLink className="ml-1 w-3 h-3" />
                </a>
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};

// Quick actions component
export const QuickActions: React.FC = () => {
  return (
    <div className="space-y-2">
      <h3 className="text-lg font-medium">Quick Actions</h3>
      <div className="flex flex-col gap-2">
        {quickActions.map((action) => (
          <Button key={action.name} variant="outline" className="justify-start" asChild>
            <a href={action.url} target="_blank" rel="noopener noreferrer">
              <span className="mr-2">{action.status}</span>
              {action.name}
            </a>
          </Button>
        ))}
      </div>
    </div>
  );
};

// Main dashboard component
export const ServiceStatusDashboard: React.FC = () => {
  const [viewMode, setViewMode] = React.useState<'cards' | 'table'>('cards');
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Orchestra AI Service Dashboards</h2>
        <div className="flex gap-2">
          <Button 
            variant={viewMode === 'cards' ? 'default' : 'outline'} 
            onClick={() => setViewMode('cards')}
          >
            Cards
          </Button>
          <Button 
            variant={viewMode === 'table' ? 'default' : 'outline'} 
            onClick={() => setViewMode('table')}
          >
            Table
          </Button>
        </div>
      </div>
      
      <div>
        {viewMode === 'cards' ? <ServiceCards /> : <ServiceTable />}
      </div>
      
      <div className="mt-8">
        <QuickActions />
      </div>
    </div>
  );
};

export default ServiceStatusDashboard;
