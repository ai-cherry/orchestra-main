/**
 * Main LLM Configuration Component for Admin Dashboard
 * Provides a comprehensive interface for managing LLM routing configurations
 */

import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { RefreshCw, Settings, Activity, Database } from 'lucide-react';
import { LLMProviderSettings } from './LLMProviderSettings';
import { LLMModelSelector } from './LLMModelSelector';
import { LLMMetricsDashboard } from './LLMMetricsDashboard';
import { LLMTestInterface } from './LLMTestInterface';
import { useToast } from '@/components/ui/use-toast';

interface ConfigurationSummary {
  providers: Array<{
    name: string;
    models_count: number;
    priority: number;
  }>;
  use_cases: Array<{
    use_case: string;
    display_name: string;
    tiers: Record<string, { model: string; provider: string }>;
  }>;
  total_models: number;
  last_updated: string | null;
}

export const LLMConfiguration: React.FC = () => {
  const [activeTab, setActiveTab] = useState('models');
  const [isLoading, setIsLoading] = useState(false);
  const [summary, setSummary] = useState<ConfigurationSummary | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const { toast } = useToast();

  // Load configuration summary
  const loadSummary = async () => {
    try {
      const response = await fetch('/api/admin/llm/configuration-summary');
      if (!response.ok) throw new Error('Failed to load configuration');
      const data = await response.json();
      setSummary(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load configuration summary',
        variant: 'destructive',
      });
    }
  };

  // Discover new models from providers
  const discoverModels = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/admin/llm/models/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_refresh: true }),
      });
      
      if (!response.ok) throw new Error('Failed to discover models');
      
      const result = await response.json();
      toast({
        title: 'Model Discovery',
        description: `Discovered ${result.total_models || 0} models from providers`,
      });
      
      // Reload summary after discovery
      await loadSummary();
      setLastRefresh(new Date());
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to discover models',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">LLM Configuration</h1>
          <p className="text-muted-foreground mt-1">
            Manage AI model routing with Portkey and OpenRouter
          </p>
        </div>
        <Button
          onClick={discoverModels}
          disabled={isLoading}
          className="gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Discover Models
        </Button>
      </div>

      {/* Configuration Summary */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Active Providers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {summary.providers.map((provider) => (
                  <div key={provider.name} className="flex justify-between items-center">
                    <span className="font-medium capitalize">{provider.name}</span>
                    <span className="text-sm text-muted-foreground">
                      {provider.models_count} models
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Total Models</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{summary.total_models}</div>
              <p className="text-sm text-muted-foreground mt-1">
                Available for routing
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Last Updated</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm">
                {summary.last_updated
                  ? new Date(summary.last_updated).toLocaleString()
                  : 'Never'}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Configuration cache
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Configuration Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="models" className="gap-2">
            <Database className="h-4 w-4" />
            Model Selection
          </TabsTrigger>
          <TabsTrigger value="providers" className="gap-2">
            <Settings className="h-4 w-4" />
            Providers
          </TabsTrigger>
          <TabsTrigger value="metrics" className="gap-2">
            <Activity className="h-4 w-4" />
            Metrics
          </TabsTrigger>
          <TabsTrigger value="test" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Test
          </TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Selection by Use Case</CardTitle>
              <CardDescription>
                Configure which models to use for different AI tasks and performance tiers
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LLMModelSelector onUpdate={() => loadSummary()} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="providers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Provider Settings</CardTitle>
              <CardDescription>
                Configure Portkey and OpenRouter API connections
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LLMProviderSettings />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>
                Monitor model performance, costs, and usage patterns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LLMMetricsDashboard />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="test" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Test Configuration</CardTitle>
              <CardDescription>
                Test model configurations before applying them
              </CardDescription>
            </CardHeader>
            <CardContent>
              <LLMTestInterface />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Info Alert */}
      <Alert>
        <AlertDescription>
          <strong>Dynamic Routing:</strong> Changes to model configurations take effect immediately 
          without requiring a server restart. The system automatically falls back to alternative 
          models if the primary model fails.
        </AlertDescription>
      </Alert>
    </div>
  );
};