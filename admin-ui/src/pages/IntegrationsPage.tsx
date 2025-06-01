import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import StatusIndicator from '@/components/ui/StatusIndicator';
import { Search, RefreshCw, Settings, Zap } from 'lucide-react';
import { useIntegrations } from '@/lib/api';

export function IntegrationsPage() {
  const { data: integrationsData = [], refetch } = useIntegrations();

  const formatLastSync = (lastSync: string) => {
    if (lastSync === 'N/A') return lastSync;
    const date = new Date(lastSync);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    
    if (mins < 60) return `${mins} minutes ago`;
    if (hours < 24) return `${hours} hours ago`;
    return date.toLocaleDateString();
  };

  const getTypeIcon = (type: string) => {
    switch(type) {
      case 'llm': return '🤖';
      case 'database': return '🗄️';
      case 'vector_db': return '🔍';
      case 'api': return '🔌';
      default: return '📦';
    }
  };

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
          <Button onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh Integrations
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
                  <TableHead>Configuration</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {integrationsData.map((integration: any) => (
                  <TableRow key={integration.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{getTypeIcon(integration.type)}</span>
                        {integration.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{integration.type.toUpperCase()}</Badge>
                    </TableCell>
                    <TableCell>
                      <StatusIndicator 
                        status={integration.status === 'connected' ? 'active' : integration.status === 'disconnected' ? 'error' : 'idle'} 
                      />
                    </TableCell>
                    <TableCell>{formatLastSync(integration.last_sync)}</TableCell>
                    <TableCell>
                      <div className="text-xs text-muted-foreground max-w-xs">
                        {integration.config.model && <div>Model: {integration.config.model}</div>}
                        {integration.config.database && <div>DB: {integration.config.database}</div>}
                        {integration.config.collection && <div>Collection: {integration.config.collection}</div>}
                        {integration.config.status && <div className="text-orange-500">{integration.config.status}</div>}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        <Settings className="h-3 w-3 mr-1" />
                        Configure
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        disabled={integration.status !== 'connected'}
                      >
                        <Zap className="h-3 w-3 mr-1" />
                        Test
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          <CardFooter className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              Showing <strong>{integrationsData.length}</strong> integrations • 
              <span className="text-green-600 ml-2">{integrationsData.filter((i: any) => i.status === 'connected').length} connected</span>
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
