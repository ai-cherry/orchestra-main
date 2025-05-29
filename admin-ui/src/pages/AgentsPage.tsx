import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import StatusIndicator from '@/components/ui/StatusIndicator';
import { Search, RefreshCw } from 'lucide-react';
import { Link } from '@tanstack/react-router';

// Dummy data
const agentsData = [
  { id: '1', name: 'Data Collector', type: 'Web Scraper', status: 'active', lastRun: '2 minutes ago' },
  { id: '2', name: 'Email Processor', type: 'Communication', status: 'idle', lastRun: '3 hours ago' },
  { id: '3', name: 'Sentiment Analyzer', type: 'NLP', status: 'error', lastRun: '1 day ago' },
  { id: '4', name: 'Content Generator', type: 'Creative', status: 'active', lastRun: '45 minutes ago' },
  { id: '5', name: 'Data Validator', type: 'Quality Control', status: 'idle', lastRun: '5 hours ago' },
  { id: '6', name: 'Transaction Monitor', type: 'Security', status: 'active', lastRun: '17 minutes ago' },
  { id: '7', name: 'Customer Support Bot', type: 'Communication', status: 'active', lastRun: '1 minute ago' },
  { id: '8', name: 'Log Analyzer', type: 'Monitoring', status: 'error', lastRun: '2 hours ago' },
];

export function AgentsPage() {
  return (
    <PageWrapper title="Agents">
      <div className="flex flex-col space-y-6">
        {/* Header with search and actions */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search agents..."
              className="w-full rounded-md pl-8 sm:w-[300px] md:w-[200px] lg:w-[300px]"
            />
          </div>
          <Button asChild>
            <Link to="/agents">
              <RefreshCw className="mr-2 h-4 w-4" /> Refresh Agents
            </Link>
          </Button>
        </div>

        {/* Main content */}
        <Card>
          <CardHeader>
            <CardTitle>Agent Inventory</CardTitle>
            <CardDescription>Manage and monitor your active agents.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Run</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {agentsData.map((agent) => (
                  <TableRow key={agent.id}>
                    <TableCell className="font-medium">{agent.name}</TableCell>
                    <TableCell>{agent.type}</TableCell>
                    <TableCell>
                      <StatusIndicator status={agent.status} />
                    </TableCell>
                    <TableCell>{agent.lastRun}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">View</Button>
                      <Button variant="ghost" size="sm">Run</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
          <CardFooter className="flex items-center justify-between">
            <div className="text-xs text-muted-foreground">
              Showing <strong>{agentsData.length}</strong> agents
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
