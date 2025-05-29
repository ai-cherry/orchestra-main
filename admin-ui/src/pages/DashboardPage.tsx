import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import MetricsDisplayCard from '@/components/ui/MetricsDisplayCard'; // Created in previous step
import StatusIndicator from '@/components/ui/StatusIndicator';   // Created in previous step
import { Users, Workflow, BarChart3, PlusCircle, Settings as SettingsIcon, ExternalLink, Briefcase } from 'lucide-react';
import { Link } from '@tanstack/react-router';

// Dummy data
const agentsData = [
  { name: 'Agent Smith', status: 'active', lastActivity: '2m ago' },
  { name: 'Agent 007', status: 'idle', lastActivity: '1h ago' },
  { name: 'ErrorBot', status: 'error', lastActivity: '5m ago' },
  { name: 'DataCruncher', status: 'active', lastActivity: '15m ago' },
];

const systemStatus = [
  { name: 'API Services', status: 'healthy' as const },
  { name: 'Database Connection', status: 'healthy' as const },
  { name: 'Background Workers', status: 'active' as const },
];

export function DashboardPage() {
  const userName = "Admin User"; // Placeholder

  return (
    <PageWrapper title={`Welcome, ${userName}!`}>
      <div className="space-y-6">
        {/* Row 1: Quick Stats */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricsDisplayCard
            title="Active Agents"
            value="12"
            icon={Users}
            description="Currently running agents"
          />
          <MetricsDisplayCard
            title="Workflows Executed"
            value="157"
            icon={Workflow}
            description="Past 24 hours"
          />
          <MetricsDisplayCard
            title="Resources Monitored"
            value="75%"
            icon={Briefcase} // Changed from Database for variety
            description="Total capacity utilization"
          />
          <MetricsDisplayCard
            title="API Calls Today"
            value="1.2M"
            icon={BarChart3}
            description="+5% from yesterday"
            colorClassName="text-green-500"
          />
        </div>

        {/* Row 2: Agent Status & System Health */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* Card 1: Agent Overview (Span 2/3 on large screens) */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Agent Activity</CardTitle>
              <CardDescription>Overview of recent agent statuses.</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Agent Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Activity</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {agentsData.slice(0,4).map((agent) => ( // Show top 4
                    <TableRow key={agent.name}>
                      <TableCell className="font-medium">{agent.name}</TableCell>
                      <TableCell>
                        <StatusIndicator status={agent.status} />
                      </TableCell>
                      <TableCell>{agent.lastActivity}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button asChild variant="outline">
                <Link to="/agents">View All Agents <ExternalLink className="ml-2 h-4 w-4" /></Link>
              </Button>
            </CardFooter>
          </Card>

          {/* Card 2: System Health / Logs Summary (Span 1/3 on large screens) */}
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>Current status of core services.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="h-32 flex items-center justify-center bg-muted rounded-md">
                <p className="text-sm text-muted-foreground">Uptime chart placeholder</p>
              </div>
              <ul className="space-y-2">
                {systemStatus.map(service => (
                  <li key={service.name} className="flex items-center justify-between">
                    <span className="text-sm">{service.name}</span>
                    <StatusIndicator status={service.status} />
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button asChild variant="outline">
                <Link to="/logs">View Detailed Logs <ExternalLink className="ml-2 h-4 w-4" /></Link>
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* Row 3: Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common administrative tasks.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button asChild>
              <Link to="/agents">
                <PlusCircle className="mr-2 h-4 w-4" /> View Agents
              </Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to="/workflows">
                 <PlusCircle className="mr-2 h-4 w-4" /> View Workflows
              </Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to="/settings">
                <SettingsIcon className="mr-2 h-4 w-4" /> Manage Settings
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </PageWrapper>
  );
}
