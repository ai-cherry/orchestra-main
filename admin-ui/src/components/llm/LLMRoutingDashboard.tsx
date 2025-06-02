import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Brain, Zap, TrendingUp, AlertCircle } from 'lucide-react';

interface RoutingAnalytics {
  query_type_distribution: Record<string, number>;
  model_performance: Record<string, {
    avg_latency_ms: number;
    p95_latency_ms: number;
    success_rate: number;
    total_requests: number;
  }>;
  recent_routing_decisions: Array<{
    timestamp: string;
    query_type: string;
    model: string;
    reasoning: string;
  }>;
  total_queries_routed: number;
}

interface QueryType {
  value: string;
  name: string;
  description: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export const LLMRoutingDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<RoutingAnalytics | null>(null);
  const [queryTypes, setQueryTypes] = useState<QueryType[]>([]);
  const [testQuery, setTestQuery] = useState('');
  const [selectedQueryType, setSelectedQueryType] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
    fetchQueryTypes();
    const interval = setInterval(fetchAnalytics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('/api/orchestration/routing-analytics');
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
    }
  };

  const fetchQueryTypes = async () => {
    try {
      const response = await fetch('/api/orchestration/query-types');
      if (!response.ok) throw new Error('Failed to fetch query types');
      const data = await response.json();
      setQueryTypes(data);
    } catch (err) {
      console.error('Error fetching query types:', err);
    }
  };

  const testRouting = async () => {
    setLoading(true);
    setError(null);
    setTestResult(null);

    try {
      const response = await fetch('/api/orchestration/test-routing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: testQuery,
          force_query_type: selectedQueryType || undefined
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Routing test failed');
      }

      const result = await response.json();
      setTestResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatQueryTypeData = () => {
    if (!analytics) return [];
    return Object.entries(analytics.query_type_distribution).map(([type, count]) => ({
      name: type.replace(/_/g, ' ').toUpperCase(),
      value: count
    }));
  };

  const formatModelPerformanceData = () => {
    if (!analytics) return [];
    return Object.entries(analytics.model_performance).map(([model, stats]) => ({
      model: model.split('/').pop() || model,
      latency: Math.round(stats.avg_latency_ms),
      p95: Math.round(stats.p95_latency_ms),
      successRate: (stats.success_rate * 100).toFixed(1),
      requests: stats.total_requests
    }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">LLM Routing Dashboard</h2>
        <Badge variant="outline" className="text-lg px-3 py-1">
          <Zap className="w-4 h-4 mr-1" />
          {analytics?.total_queries_routed || 0} Queries Routed
        </Badge>
      </div>

      <Tabs defaultValue="analytics" className="space-y-4">
        <TabsList>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="test">Test Routing</TabsTrigger>
          <TabsTrigger value="decisions">Recent Decisions</TabsTrigger>
        </TabsList>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Query Type Distribution</CardTitle>
                <CardDescription>Breakdown of queries by classification</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={formatQueryTypeData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {formatQueryTypeData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Model Performance</CardTitle>
                <CardDescription>Average latency by model</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={formatModelPerformanceData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="model" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="latency" fill="#8884d8" name="Avg Latency (ms)" />
                    <Bar dataKey="p95" fill="#82ca9d" name="P95 Latency (ms)" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Model Statistics</CardTitle>
              <CardDescription>Detailed performance metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {formatModelPerformanceData().map((model) => (
                  <div key={model.model} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Brain className="w-5 h-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{model.model}</p>
                        <p className="text-sm text-muted-foreground">
                          {model.requests} requests
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <p className="text-sm font-medium">{model.latency}ms</p>
                        <p className="text-xs text-muted-foreground">avg latency</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">{model.successRate}%</p>
                        <p className="text-xs text-muted-foreground">success rate</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="test" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Test Intelligent Routing</CardTitle>
              <CardDescription>
                Test how queries are classified and routed to different models
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="test-query">Query</Label>
                <Input
                  id="test-query"
                  placeholder="Enter a test query..."
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="query-type">Force Query Type (Optional)</Label>
                <Select value={selectedQueryType} onValueChange={setSelectedQueryType}>
                  <SelectTrigger id="query-type">
                    <SelectValue placeholder="Auto-detect" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Auto-detect</SelectItem>
                    {queryTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Button 
                onClick={testRouting} 
                disabled={!testQuery || loading}
                className="w-full"
              >
                {loading ? 'Testing...' : 'Test Routing'}
              </Button>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {testResult && (
                <div className="space-y-3 pt-4 border-t">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Query Type</p>
                      <p className="font-medium">{testResult.query_type}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Model Selected</p>
                      <p className="font-medium">{testResult.model_used}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Temperature</p>
                      <p className="font-medium">{testResult.temperature}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Latency</p>
                      <p className="font-medium">{testResult.latency_ms}ms</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground mb-1">Reasoning</p>
                    <p className="text-sm bg-muted p-2 rounded">{testResult.reasoning}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-muted-foreground mb-1">Response Preview</p>
                    <p className="text-sm bg-muted p-2 rounded">{testResult.response_preview}...</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="decisions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Routing Decisions</CardTitle>
              <CardDescription>
                Latest queries and their routing decisions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analytics?.recent_routing_decisions.map((decision, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="outline">{decision.query_type}</Badge>
                      <span className="text-sm text-muted-foreground">
                        {new Date(decision.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm font-medium">{decision.model}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">{decision.reasoning}</p>
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