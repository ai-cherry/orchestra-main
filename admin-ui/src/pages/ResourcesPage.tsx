import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import StatusIndicator from '@/components/ui/StatusIndicator';
import { Search, RefreshCw } from 'lucide-react';
import { Link } from '@tanstack/react-router';

// Dummy data for resources
const resourcesData = [
  { id: '1', name: 'API Documentation', type: 'Document', status: 'active', lastUpdated: '2 days ago' },
  { id: '2', name: 'User Guide', type: 'Document', status: 'active', lastUpdated: '1 week ago' },
  { id: '3', name: 'System Architecture', type: 'Diagram', status: 'active', lastUpdated: '3 days ago' },
  { id: '4', name: 'Database Schema', type: 'Diagram', status: 'outdated', lastUpdated: '2 months ago' },
  { id: '5', name: 'Deployment Guide', type: 'Document', status: 'active', lastUpdated: '5 days ago' },
  { id: '6', name: 'Training Videos', type: 'Media', status: 'active', lastUpdated: '1 month ago' },
  { id: '7', name: 'Code Samples', type: 'Repository', status: 'active', lastUpdated: '1 day ago' },
  { id: '8', name: 'Security Policy', type: 'Document', status: 'active', lastUpdated: '2 weeks ago' },
];

// Status mapping for resource status indicators
const statusMap = {
  'active': 'healthy',
  'outdated': 'warning',
  'archived': 'idle',
  'error': 'error',
} as const;

export function ResourcesPage() {
  return (
    <PageWrapper title="Resources">
      <div className="flex flex-col space-y-6">
        {/* Header with search and actions */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search resources..."
              className="w-full rounded-md pl-8 sm:w-[300px] md:w-[200px] lg:w-[300px]"
            />
          </div>
          <Button asChild>
            <Link to="/resources">
              <RefreshCw className="mr-2 h-4 w-4" /> Refresh Resources
            </Link>
          </Button>
        </div>

        {/* Main content */}
        <Card>
          <CardHeader>
            <CardTitle>Resource Library</CardTitle>
            <CardDescription>Manage and access your knowledge resources.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Updated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {resourcesData.map((resource) => (
                  <TableRow key={resource.id}>
                    <TableCell className="font-medium">{resource.name}</TableCell>
                    <TableCell>{resource.type}</TableCell>
                    <TableCell>
                      <StatusIndicator status={statusMap[resource.status as keyof typeof statusMap] || 'error'} />
                    </TableCell>
                    <TableCell>{resource.lastUpdated}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">View</Button>
                      <Button variant="ghost" size="sm">Edit</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          <CardFooter className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              Showing <strong>{resourcesData.length}</strong> resources
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
