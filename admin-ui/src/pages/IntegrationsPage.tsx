import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import StatusIndicator from '@/components/ui/StatusIndicator';
import { Search, RefreshCw } from 'lucide-react';
import { Link } from '@tanstack/react-router';

// Dummy data for integrations
const integrationsData = [
  { id: '1', name: 'Slack', type: 'Communication', status: 'active', lastSync: '5 minutes ago' },
  { id: '2', name: 'Google Drive', type: 'Storage', status: 'active', lastSync: '1 hour ago' },
  { id: '3', name: 'GitHub', type: 'Development', status: 'error', lastSync: '2 days ago' },
  { id: '4', name: 'Salesforce', type: 'CRM', status: 'idle', lastSync: '3 hours ago' },
  { id: '5', name: 'Jira', type: 'Project Management', status: 'active', lastSync: '30 minutes ago' },
  { id: '6', name: 'Zendesk', type: 'Support', status: 'idle', lastSync: '1 day ago' },
  { id: '7', name: 'Stripe', type: 'Payment', status: 'active', lastSync: '15 minutes ago' },
  { id: '8', name: 'HubSpot', type: 'Marketing', status: 'error', lastSync: '4 hours ago' },
];

export function IntegrationsPage() {
  return (
    <PageWrapper title="Integrations">
      <div className="flex flex-col space-y-6">
        {/* Header with search and actions */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search integrations..."
              className="w-full rounded-md pl-8 sm:w-[300px] md:w-[200px] lg:w-[300px]"
            />
          </div>
          <Button asChild>
            <Link to="/integrations">
              <RefreshCw className="mr-2 h-4 w-4" /> Refresh Integrations
            </Link>
          </Button>
        </div>

        {/* Main content */}
        <Card>
          <CardHeader>
            <CardTitle>Connected Services</CardTitle>
            <CardDescription>Manage your external service integrations.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Sync</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {integrationsData.map((integration) => (
                  <TableRow key={integration.id}>
                    <TableCell className="font-medium">{integration.name}</TableCell>
                    <TableCell>{integration.type}</TableCell>
                    <TableCell>
                      <StatusIndicator status={integration.status} />
                    </TableCell>
                    <TableCell>{integration.lastSync}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">Configure</Button>
                      <Button variant="ghost" size="sm">Sync Now</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          <CardFooter className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              Showing <strong>{integrationsData.length}</strong> integrations
            </div>
            <div className="space-x-2">
              <Button variant="outline" size="sm" disabled>Previous</Button>
              <Button variant="outline" size="sm" disabled>Next</Button>
            </div>
          </CardFooter>
        </Card>
      </div>
    </PageWrapper>
  );
}
