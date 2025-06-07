import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  DollarSign, 
  Phone, 
  Target,
  AlertTriangle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';

interface SalesMetric {
  label: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  icon: React.ReactNode;
}

interface ClientHealth {
  id: string;
  name: string;
  company: string;
  score: number;
  risk: 'Low' | 'Medium' | 'High';
}

interface CallPerformance {
  employeeId: string;
  calls: number;
  duration: number;
  conversion: number;
}

const PayReadyDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [mcpConnected, setMcpConnected] = useState(false);
  
  // Mock data - in production, this would come from MCP server
  const salesMetrics: SalesMetric[] = [
    {
      label: 'Pipeline Value',
      value: '$847,290',
      change: '+12.5%',
      trend: 'up',
      icon: <DollarSign className="h-4 w-4" />
    },
    {
      label: 'Active Deals',
      value: '23',
      change: '+3',
      trend: 'up',
      icon: <Target className="h-4 w-4" />
    },
    {
      label: 'Calls This Week',
      value: '156',
      change: '-8',
      trend: 'down',
      icon: <Phone className="h-4 w-4" />
    },
    {
      label: 'New Leads',
      value: '31',
      change: '+22%',
      trend: 'up',
      icon: <Users className="h-4 w-4" />
    }
  ];

  const pipelineData = [
    { stage: 'Qualified', deals: 12, value: 234000 },
    { stage: 'Presentation', deals: 8, value: 189000 },
    { stage: 'Proposal', deals: 5, value: 156000 },
    { stage: 'Negotiation', deals: 3, value: 98000 },
    { stage: 'Closed Won', deals: 2, value: 67000 }
  ];

  const clientHealthData: ClientHealth[] = [
    { id: '1', name: 'John Smith', company: 'Acme Corp', score: 85, risk: 'Low' },
    { id: '2', name: 'Sarah Johnson', company: 'TechStart Inc', score: 45, risk: 'High' },
    { id: '3', name: 'Mike Wilson', company: 'GlobalTech', score: 72, risk: 'Medium' },
    { id: '4', name: 'Lisa Chen', company: 'InnovateX', score: 91, risk: 'Low' },
    { id: '5', name: 'David Brown', company: 'NextGen Solutions', score: 38, risk: 'High' }
  ];

  const callPerformanceData: CallPerformance[] = [
    { employeeId: 'user_001', calls: 45, duration: 1200, conversion: 0.23 },
    { employeeId: 'user_002', calls: 38, duration: 980, conversion: 0.31 },
    { employeeId: 'user_003', calls: 52, duration: 1456, conversion: 0.19 },
    { employeeId: 'user_004', calls: 41, duration: 1087, conversion: 0.27 }
  ];

  const refreshData = async () => {
    setLoading(true);
    try {
      // In production, call MCP server endpoints
      // const pipeline = await mcpServer.call_tool('get_sales_pipeline', {});
      // const performance = await mcpServer.call_tool('analyze_call_performance', {});
      // const health = await mcpServer.call_tool('get_client_health_score', {});
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      setLastUpdated(new Date());
      setMcpConnected(true);
    } catch (error) {
      console.error('Failed to refresh data:', error);
      setMcpConnected(false);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'High': return 'bg-red-500';
      case 'Medium': return 'bg-yellow-500';
      case 'Low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getRiskBadgeVariant = (risk: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (risk) {
      case 'High': return 'destructive';
      case 'Medium': return 'secondary';
      case 'Low': return 'default';
      default: return 'outline';
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Pay Ready/Sophia</h1>
          <p className="text-gray-600">Sales Intelligence Dashboard</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${mcpConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600">
              MCP {mcpConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <Button onClick={refreshData} disabled={loading} variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {salesMetrics.map((metric, index) => (
          <Card key={index}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{metric.label}</CardTitle>
              {metric.icon}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                {metric.trend === 'up' ? (
                  <TrendingUp className="h-3 w-3 text-green-500" />
                ) : (
                  <TrendingDown className="h-3 w-3 text-red-500" />
                )}
                <span className={metric.trend === 'up' ? 'text-green-500' : 'text-red-500'}>
                  {metric.change}
                </span>
                <span>from last week</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Dashboard Content */}
      <Tabs defaultValue="pipeline" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="pipeline">Sales Pipeline</TabsTrigger>
          <TabsTrigger value="performance">Call Performance</TabsTrigger>
          <TabsTrigger value="health">Client Health</TabsTrigger>
          <TabsTrigger value="leads">Lead Generation</TabsTrigger>
        </TabsList>

        {/* Sales Pipeline Tab */}
        <TabsContent value="pipeline" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Pipeline by Stage</CardTitle>
                <CardDescription>Number of deals in each stage</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={pipelineData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="stage" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="deals" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Pipeline Value</CardTitle>
                <CardDescription>Total value by stage</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={pipelineData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="stage" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Value']} />
                    <Bar dataKey="value" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Call Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Call Volume by Employee</CardTitle>
                <CardDescription>Number of calls made this week</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={callPerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="employeeId" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="calls" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Conversion Rates</CardTitle>
                <CardDescription>Call to deal conversion by employee</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={callPerformanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="employeeId" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`${(value * 100).toFixed(1)}%`, 'Conversion']} />
                    <Bar dataKey="conversion" fill="#f59e0b" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Client Health Tab */}
        <TabsContent value="health" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Client Health Scores</CardTitle>
              <CardDescription>Current health status of all clients</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {clientHealthData.map((client) => (
                  <div key={client.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className={`w-4 h-4 rounded-full ${getRiskColor(client.risk)}`} />
                      <div>
                        <div className="font-medium">{client.name}</div>
                        <div className="text-sm text-gray-600">{client.company}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <div className="font-bold">{client.score}/100</div>
                        <Badge variant={getRiskBadgeVariant(client.risk)}>
                          {client.risk} Risk
                        </Badge>
                      </div>
                      {client.risk === 'High' && (
                        <AlertTriangle className="h-5 w-5 text-red-500" />
                      )}
                      {client.risk === 'Low' && (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Lead Generation Tab */}
        <TabsContent value="leads" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Generate New Leads</CardTitle>
              <CardDescription>Use Apollo.io integration to find qualified prospects</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input placeholder="Keywords (e.g., 'CTO startup')" />
                <Input placeholder="Industry (e.g., 'Technology')" />
                <Input placeholder="Company Size (e.g., '50-200')" />
              </div>
              <Button className="w-full">
                <Target className="h-4 w-4 mr-2" />
                Generate Leads
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Lead Activity</CardTitle>
              <CardDescription>Latest leads and their engagement status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-gray-500">
                Generate leads to see activity here
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Footer */}
      <div className="text-center text-sm text-gray-500">
        Last updated: {lastUpdated.toLocaleString()} | 
        Single-user mode active | 
        Pay Ready/Sophia v1.0.0
      </div>
    </div>
  );
};

export default PayReadyDashboard; 