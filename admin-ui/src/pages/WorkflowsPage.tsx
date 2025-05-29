import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import StatusIndicator from '@/components/ui/StatusIndicator';
import { Search, RefreshCw } from 'lucide-react';
import { Link } from '@tanstack/react-router';

// Dummy data
const workflowsData = [
  { id: '1', name: 'Data Ingestion Pipeline', status: 'active', lastRun: '15 minutes ago', nextRun: 'In 45 minutes' },
  { id: '2', name: 'Weekly Report Generator', status: 'idle', lastRun: '3 days ago', nextRun: 'In 4 days' },
  { id: '3', name: 'Customer Onboarding', status: 'error', lastRun: '1 hour ago', nextRun: 'Manual trigger' },
  { id: '4', name: 'Inventory Sync', status: 'active', lastRun: '30 minutes ago', nextRun: 'In 30 minutes' },
  { id: '5', name: 'Log Cleanup', status: 'idle', lastRun: '1 day ago', nextRun: 'Tomorrow, 2:00 AM' },
  { id: '6', name: 'Security Scan', status: 'active', lastRun: '4 hours ago', nextRun: 'In 20 hours' },
  { id: '7', name: 'Database Backup', status: 'active', lastRun: '12 hours ago', nextRun: 'In 12 hours' },
];

export function WorkflowsPage() {
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
          <Button asChild>
            <Link to="/workflows">
              <RefreshCw className="mr-2 h-4 w-4" /> Refresh Workflows
            </Link>
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
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workflowsData.map((workflow) => (
                  <TableRow key={workflow.id}>
                    <TableCell className="font-medium">{workflow.name}</TableCell>
                    <TableCell>
                      <StatusIndicator status={workflow.status} />
                    </TableCell>
                    <TableCell>{workflow.lastRun}</TableCell>
                    <TableCell>{workflow.nextRun}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">Edit</Button>
                      <Button variant="ghost" size="sm">Run Now</Button>
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
