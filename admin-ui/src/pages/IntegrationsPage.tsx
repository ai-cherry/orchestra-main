import React from 'react';
import PageWrapper from '@/components/layout/PageWrapper';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import StatusIndicator from '@/components/ui/StatusIndicator'; // Ensure this path is correct
import { Cpu, FolderKanban, MessageSquare, Settings2, Trash2, PlusCircle, Zap } from 'lucide-react'; // Added Zap for a generic integration icon
import { Link } from '@tanstack/react-router'; // For "Add New Integration" button link

type IntegrationStatus = 'Connected' | 'Disconnected' | 'Needs Attention';

// Mock Data
const mockIntegrations = [
  { id: '1', name: 'OpenAI GPT-4', Icon: Cpu, status: 'Connected' as IntegrationStatus, description: 'Advanced language model for content generation and analysis.' },
  { id: '2', name: 'Google Drive', Icon: FolderKanban, status: 'Disconnected' as IntegrationStatus, description: 'Cloud storage for documents and collaboration.' },
  { id: '3', name: 'Slack Workspace', Icon: MessageSquare, status: 'Needs Attention' as IntegrationStatus, description: 'Team communication and real-time notifications.' },
  { id: '4', name: 'Generic API', Icon: Zap, status: 'Connected' as IntegrationStatus, description: 'Connect to a custom third-party API endpoint.' },
];

// Helper to map integration status text to StatusIndicator's 'status' prop values
const mapIntegrationStatusToIndicator = (status: IntegrationStatus): string => {
  switch (status) {
    case 'Connected': return 'active';       // Maps to green
    case 'Disconnected': return 'offline';    // Maps to gray
    case 'Needs Attention': return 'warn';     // Maps to yellow
    default: return 'offline';               // Default to gray
  }
};

export function IntegrationsPage() {
  // Placeholder for handling actions
  const handleConfigure = (integrationId: string) => {
    alert(`Configure action for integration ${integrationId}`);
    console.log(`Configure action for integration ${integrationId}`);
  };

  const handleDisconnect = (integrationId: string) => {
    alert(`Disconnect action for integration ${integrationId}`);
    console.log(`Disconnect action for integration ${integrationId}`);
  };

  return (
    <PageWrapper title="Integrations Management">
      <div className="flex items-center justify-between mb-6">
        <p className="text-muted-foreground">
          Connect and manage your third-party service integrations.
        </p>
        <Button asChild>
          <Link to="/integrations/new"> {/* Assuming a route for adding new integrations */}
            <PlusCircle className="mr-2 h-4 w-4" /> Add New Integration
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockIntegrations.map((integration) => (
          <Card key={integration.id} className="flex flex-col justify-between shadow-lg hover:shadow-xl transition-shadow duration-300">
            <CardHeader>
              <div className="flex items-start space-x-4 mb-3"> {/* items-start for better alignment with multiline title */}
                <integration.Icon className="h-10 w-10 text-theme-accent-primary mt-1" /> {/* Slightly larger icon, themed */}
                <div>
                  <CardTitle className="text-xl mb-1">{integration.name}</CardTitle>
                  <StatusIndicator 
                    status={mapIntegrationStatusToIndicator(integration.status)} 
                    text={integration.status} 
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent className="flex-grow">
              <CardDescription className="text-sm">{integration.description}</CardDescription>
            </CardContent>
            <CardFooter className="flex justify-end space-x-2 pt-4"> {/* Added pt-4 for spacing */}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => handleConfigure(integration.id)}
                aria-label={`Configure ${integration.name}`}
              >
                <Settings2 className="mr-1.5 h-4 w-4" /> Configure
              </Button>
              <Button 
                variant="destructive" 
                size="sm" 
                onClick={() => handleDisconnect(integration.id)}
                aria-label={`Disconnect ${integration.name}`}
              >
                <Trash2 className="mr-1.5 h-4 w-4" /> Disconnect
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </PageWrapper>
  );
}
