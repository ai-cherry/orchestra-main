import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import StatusIndicator from '@/components/ui/StatusIndicator';
import { Search, RefreshCw, Play } from 'lucide-react';
import { useWorkflows } from '@/lib/api';

export function WorkflowsPage() {
  const { data: workflowsData = [], refetch } = useWorkflows();

  // Format the datetime strings to be more readable
  const formatDateTime = (dateStr: string) => {
    if (dateStr === 'Manual trigger') return dateStr;
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    
    if (Math.abs(diff) < 86400000) { // Less than 24 hours
      const hours = Math.floor(Math.abs(diff) / 3600000);
      const mins = Math.floor((Math.abs(diff) % 3600000) / 60000);
      if (diff > 0) {
        return hours > 0 ? `In ${hours}h ${mins}m` : `In ${mins} minutes`;
      } else {
        return hours > 0 ? `${hours}h ${mins}m ago` : `${mins} minutes ago`;
      }
    }
    return date.toLocaleString();
  };

  return (
    <PageWrapper title="Workflows">
      <div className="flex flex-col space-y-6">
        {/* Header with search and actions */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search workflows..."
              className="w-full rounded-md pl-8 sm:w-[300px] md:w-[200px] lg:w-[300px]"
            />
          </div>
          <Button onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" /> Refresh Workflows
          </Button>
        </div>

        {/* Main content */}
        <Card>
          <CardHeader>
            <CardTitle>Workflow Management</CardTitle>
            <CardDescription>Orchestrate and monitor your automated processes.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Run</TableHead>
                  <TableHead>Next Run</TableHead>
                  <TableHead>Actions</TableHead>
                  <TableHead className="text-right">Controls</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workflowsData.map((workflow: any) => (
                  <TableRow key={workflow.id}>
                    <TableCell className="font-medium">{workflow.name}</TableCell>
                    <TableCell>
                      <StatusIndicator status={workflow.status} />
                    </TableCell>
                    <TableCell>{formatDateTime(workflow.last_run)}</TableCell>
                    <TableCell>{formatDateTime(workflow.next_run)}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{workflow.actions} steps</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">Edit</Button>
                      <Button variant="ghost" size="sm">
                        <Play className="h-3 w-3 mr-1" />
                        Run Now
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          <CardFooter className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              Showing <strong>{workflowsData.length}</strong> workflows
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
