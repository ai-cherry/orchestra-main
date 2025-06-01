/**
 * LLM Metrics Dashboard Component
 * Displays performance metrics, costs, and usage patterns for LLM models
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { 
  TrendingUp, TrendingDown, DollarSign, Zap, 
  AlertCircle, CheckCircle, Clock, Activity
} from 'lucide-react';

interface MetricsSummary {
  total_requests: number;
  total_successes: number;
  total_failures: number;
  success_rate: number;
  total_tokens: number;
  total_cost: number;
}

interface ModelMetrics {
  requests: number;
  successes: number;
  failures: number;
  tokens: number;
  cost: number;
  avg_latency_ms: number;
}

interface MetricsData {
  summary: MetricsSummary;
  by_model: Record<string, ModelMetrics>;
  metrics: Array<{
    id: number;
    model: { model_identifier: string; provider_name: string };
    use_case: string;
    request_count: number;
    success_count: number;
    failure_count: number;
    success_rate: number;
    total_tokens: number;
    total_cost: number;
    avg_latency_ms: number;
    date: string;
  }>;
}

export const LLMMetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [timeRange, setTimeRange] = useState('7d');
  const [selectedUseCase, setSelectedUseCase] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadMetrics();
  }, [timeRange, selectedUseCase]);

  const loadMetrics = async () => {
    setIsLoading(true);
    try {
      // Calculate date range
      const endDate = new Date();
      const startDate = new Date();
      switch (timeRange) {
        case '24h':
          startDate.setDate(startDate.getDate() - 1);
          break;
        case '7d':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(startDate.getDate() - 30);
          break;
      }

      const params = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      });
      
      if (selectedUseCase !== 'all') {
        params.append('use_case', selectedUseCase);
      }

      const response = await fetch(`/api/admin/llm/metrics?${params}`);
      if (!response.ok) throw new Error('Failed to load metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load metrics',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (value: number) => `$${value.toFixed(4)}`;
  const formatNumber = (value: number) => value.toLocaleString();
  const formatLatency = (ms: number) => `${ms.toFixed(0)}ms`;

  const renderSummaryCard = (
    title: string,
    value: string | number,
    icon: React.ReactNode,
    trend?: number,
    description?: string
  ) => (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {trend !== undefined && (
          <div className="flex items-center mt-2">
            {trend > 0 ? (
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
            )}
            <span className={`text-xs ${trend > 0 ? 'text-green-500' : 'text-red-500'}`}>
              {Math.abs(trend)}%
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );

  if (isLoading || !metrics) {
    return <div className="text-center py-8">Loading metrics...</div>;
  }

  // Prepare chart data
  const modelPerformanceData = Object.entries(metrics.by_model).map(([model, data]) => ({
    model: model.split('/').pop() || model,
    requests: data.requests,
    successRate: data.successes / data.requests * 100,
    avgLatency: data.avg_latency_ms,
    cost: data.cost,
  }));

  const costByModelData = Object.entries(metrics.by_model).map(([model, data]) => ({
    name: model.split('/').pop() || model,
    value: data.cost,
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex justify-between items-center">
        <div className="flex gap-4">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24h">Last 24h</SelectItem>
              <SelectItem value="7d">Last 7 days</SelectItem>
              <SelectItem value="30d">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
          
          <Select value={selectedUseCase} onValueChange={setSelectedUseCase}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Use Cases</SelectItem>
              <SelectItem value="code_generation">Code Generation</SelectItem>
              <SelectItem value="architecture_design">Architecture Design</SelectItem>
              <SelectItem value="debugging">Debugging</SelectItem>
              <SelectItem value="documentation">Documentation</SelectItem>
              <SelectItem value="chat_conversation">Chat</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {renderSummaryCard(
          'Total Requests',
          formatNumber(metrics.summary.total_requests),
          <Activity className="h-4 w-4 text-muted-foreground" />,
          undefined,
          `${metrics.summary.total_successes} successful`
        )}
        
        {renderSummaryCard(
          'Success Rate',
          `${metrics.summary.success_rate.toFixed(1)}%`,
          metrics.summary.success_rate > 95 ? (
            <CheckCircle className="h-4 w-4 text-green-500" />
          ) : (
            <AlertCircle className="h-4 w-4 text-yellow-500" />
          )
        )}
        
        {renderSummaryCard(
          'Total Cost',
          formatCurrency(metrics.summary.total_cost),
          <DollarSign className="h-4 w-4 text-muted-foreground" />,
          undefined,
          `${formatNumber(metrics.summary.total_tokens)} tokens`
        )}
        
        {renderSummaryCard(
          'Avg Response Time',
          formatLatency(
            Object.values(metrics.by_model).reduce((sum, m) => sum + m.avg_latency_ms, 0) /
            Object.keys(metrics.by_model).length
          ),
          <Zap className="h-4 w-4 text-muted-foreground" />
        )}
      </div>

      {/* Charts */}
      <Tabs defaultValue="performance" className="space-y-4">
        <TabsList>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
        </TabsList>

        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Performance Comparison</CardTitle>
              <CardDescription>
                Success rate and latency by model
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={modelPerformanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="model" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="successRate" fill="#8884d8" name="Success Rate (%)" />
                  <Bar yAxisId="right" dataKey="avgLatency" fill="#82ca9d" name="Avg Latency (ms)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="costs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cost Distribution by Model</CardTitle>
              <CardDescription>
                Total costs across different models
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={costByModelData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {costByModelData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Usage Details</CardTitle>
              <CardDescription>
                Detailed metrics for each model
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(metrics.by_model).map(([model, data]) => (
                  <div key={model} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-medium">{model}</h4>
                        <p className="text-sm text-muted-foreground">
                          {data.requests} requests
                        </p>
                      </div>
                      <Badge variant={data.successes / data.requests > 0.95 ? 'default' : 'secondary'}>
                        {(data.successes / data.requests * 100).toFixed(1)}% success
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Tokens:</span>
                        <span className="ml-2 font-medium">{formatNumber(data.tokens)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Cost:</span>
                        <span className="ml-2 font-medium">{formatCurrency(data.cost)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Avg Latency:</span>
                        <span className="ml-2 font-medium">{formatLatency(data.avg_latency_ms)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Failures:</span>
                        <span className="ml-2 font-medium">{data.failures}</span>
                      </div>
                    </div>
                    
                    <Progress 
                      value={data.successes / data.requests * 100} 
                      className="mt-2"
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};