import PageWrapper from '@/components/layout/PageWrapper';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import MetricsDisplayCard from '@/components/ui/MetricsDisplayCard'; // Created in previous step
import StatusIndicator from '@/components/ui/StatusIndicator';   // Created in previous step
import { Users, Workflow, BarChart3, PlusCircle, Settings as SettingsIcon, ExternalLink, Briefcase } from 'lucide-react';
import { Link } from '@tanstack/react-router';
import { useAgents } from '@/lib/api';
import { useEffect, useState } from 'react';

// Helper function to format the last run time
const formatLastRun = (lastRun: string) => {
  const date = new Date(lastRun);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString();
};

export function DashboardPage() {
  const userName = "Admin User"; // Placeholder
  const { data: agentsData = [] } = useAgents();
  const [metrics, setMetrics] = useState<any>(null);

  // Fetch metrics data
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // Get auth token from the auth store
        const authData = localStorage.getItem('admin-auth-storage');
        let token = '';
        if (authData) {
          try {
            const parsed = JSON.parse(authData);
            token = parsed.state?.token || '';
          } catch (e) {
            console.error('Failed to parse auth data:', e);
          }
        }
        
        const response = await fetch(`${window.location.origin}/api/metrics`, {
          headers: {
            'X-API-Key': token,
          },
        });
        if (response.ok) {
          const data = await response.json();
          setMetrics(data);
        }
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };
    fetchMetrics();
  }, []);

  // Calculate real metrics
  const activeAgents = agentsData.filter((agent: any) => agent.status === 'active').length;
  const totalAgents = agentsData.length;
  const totalTasksCompleted = agentsData.reduce((sum: number, agent: any) => sum + (agent.tasks_completed || 0), 0);
  const avgMemoryUsage = agentsData.length > 0 
    ? (agentsData.reduce((sum: number, agent: any) => sum + (agent.memory_usage || 0), 0) / agentsData.length).toFixed(1)
    : '0';

  return (
    <PageWrapper title={`Welcome, ${userName}!`}>
      <div className="space-y-6">
        {/* Row 1: Quick Stats */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricsDisplayCard
            title="Active Agents"
            value={`${activeAgents}/${totalAgents}`}
            icon={Users}
            description="Currently running agents"
          />
          <MetricsDisplayCard
            title="Tasks Completed"
            value={totalTasksCompleted.toString()}
            icon={Workflow}
            description="Total tasks completed"
          />
          <MetricsDisplayCard
            title="Avg Memory Usage"
            value={`${avgMemoryUsage}%`}
            icon={Briefcase}
            description="Average agent memory usage"
          />
          <MetricsDisplayCard
            title="System CPU"
            value={metrics?.cpu_usage ? `${metrics.cpu_usage.toFixed(1)}%` : '--'}
            icon={BarChart3}
            description={metrics?.uptime || 'Loading...'}
            colorClassName={metrics?.cpu_usage > 80 ? 'text-red-500' : 'text-green-500'}
          />
        </div>

        {/* Row 2: Agent Status & System Health */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* Card 1: Agent Overview (Span 2/3 on large screens) */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Agent Activity</CardTitle>
              <CardDescription>Real-time agent status overview</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Agent Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Activity</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {agentsData.slice(0,4).map((agent: any) => (
                    <TableRow key={agent.id}>
                      <TableCell className="font-medium">{agent.name}</TableCell>
                      <TableCell>{agent.type}</TableCell>
                      <TableCell>
                        <StatusIndicator status={agent.status} />
                      </TableCell>
                      <TableCell>{formatLastRun(agent.lastRun)}</TableCell>
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

          {/* Card 2: System Health */}
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>Real system metrics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ul className="space-y-2">
                <li className="flex items-center justify-between">
                  <span className="text-sm">API Services</span>
                  <StatusIndicator status="active" />
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-sm">CPU Usage</span>
                  <span className="text-sm font-medium">{metrics?.cpu_usage ? `${metrics.cpu_usage.toFixed(1)}%` : '--'}</span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-sm">Memory Usage</span>
                  <span className="text-sm font-medium">{metrics?.memory_usage ? `${metrics.memory_usage.toFixed(1)}%` : '--'}</span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-sm">Disk Usage</span>
                  <span className="text-sm font-medium">{metrics?.disk_usage ? `${metrics.disk_usage.toFixed(1)}%` : '--'}</span>
                </li>
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
