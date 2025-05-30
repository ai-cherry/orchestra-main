import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import StatusIndicator from '@/components/ui/StatusIndicator';
import { Search, RefreshCw } from 'lucide-react';
import { Link } from '@tanstack/react-router';
import { useAgents } from '@/lib/api';

// Define Agent interface with required properties
interface Agent {
  id: string | number;
  name: string;
  type: string;
  status: string; // e.g., 'active', 'inactive', 'error'
  lastRun: string; // ISO date string or human-readable
}

export function AgentsPage() {
  const { data: agentsData = [] } = useAgents()
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
                {agentsData.map((agent: Agent) => (
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
