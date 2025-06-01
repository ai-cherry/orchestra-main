/**
 * LLM Provider Settings Component
 * Manages API keys and settings for Portkey and OpenRouter
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { Save, Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react';

interface Provider {
  id: number;
  name: string;
  api_key_env_var: string;
  base_url: string;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export const LLMProviderSettings: React.FC = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [apiKeyValues, setApiKeyValues] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState<Record<string, boolean>>({});
  const { toast } = useToast();

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/admin/llm/providers?include_inactive=true');
      if (!response.ok) throw new Error('Failed to load providers');
      const data = await response.json();
      setProviders(data);
      
      // Initialize API key values (empty for security)
      const keyValues: Record<string, string> = {};
      data.forEach((provider: Provider) => {
        keyValues[provider.name] = '';
      });
      setApiKeyValues(keyValues);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load provider settings',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const updateProvider = async (providerName: string, updates: Partial<Provider>) => {
    setIsSaving(prev => ({ ...prev, [providerName]: true }));
    
    try {
      const response = await fetch(`/api/admin/llm/providers/${providerName}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      
      if (!response.ok) throw new Error('Failed to update provider');
      
      const updatedProvider = await response.json();
      setProviders(prev =>
        prev.map(p => (p.name === providerName ? updatedProvider : p))
      );
      
      toast({
        title: 'Success',
        description: `Updated ${providerName} settings`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to update ${providerName}`,
        variant: 'destructive',
      });
    } finally {
      setIsSaving(prev => ({ ...prev, [providerName]: false }));
    }
  };

  const toggleApiKeyVisibility = (providerName: string) => {
    setShowApiKeys(prev => ({
      ...prev,
      [providerName]: !prev[providerName],
    }));
  };

  const renderProvider = (provider: Provider) => {
    const isPortkey = provider.name === 'portkey';
    const isOpenRouter = provider.name === 'openrouter';
    
    return (
      <Card key={provider.name}>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-xl capitalize">{provider.name}</CardTitle>
              <CardDescription>
                {isPortkey && 'Primary routing service with 300+ models'}
                {isOpenRouter && 'Fallback routing service for high availability'}
              </CardDescription>
            </div>
            <Badge variant={provider.is_active ? 'default' : 'secondary'}>
              {provider.is_active ? (
                <>
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Active
                </>
              ) : (
                <>
                  <XCircle className="h-3 w-3 mr-1" />
                  Inactive
                </>
              )}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* API Key Configuration */}
          <div className="space-y-2">
            <Label>API Key Environment Variable</Label>
            <div className="flex gap-2">
              <Input
                type={showApiKeys[provider.name] ? 'text' : 'password'}
                value={apiKeyValues[provider.name] || ''}
                onChange={(e) =>
                  setApiKeyValues(prev => ({
                    ...prev,
                    [provider.name]: e.target.value,
                  }))
                }
                placeholder={`Enter new ${provider.api_key_env_var} value`}
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => toggleApiKeyVisibility(provider.name)}
              >
                {showApiKeys[provider.name] ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Environment variable: {provider.api_key_env_var}
            </p>
          </div>

          {/* Base URL */}
          <div className="space-y-2">
            <Label>Base URL</Label>
            <Input value={provider.base_url} disabled />
          </div>

          {/* Priority */}
          <div className="space-y-2">
            <Label>Priority (lower = higher priority)</Label>
            <Input
              type="number"
              min="0"
              max="10"
              value={provider.priority}
              onChange={(e) =>
                updateProvider(provider.name, {
                  priority: parseInt(e.target.value),
                })
              }
            />
          </div>

          {/* Active Status */}
          <div className="flex items-center justify-between">
            <Label htmlFor={`active-${provider.name}`}>Enable Provider</Label>
            <Switch
              id={`active-${provider.name}`}
              checked={provider.is_active}
              onCheckedChange={(checked) =>
                updateProvider(provider.name, { is_active: checked })
              }
            />
          </div>

          {/* Save Button */}
          <Button
            onClick={() => {
              if (apiKeyValues[provider.name]) {
                updateProvider(provider.name, {
                  api_key_env_var: apiKeyValues[provider.name],
                });
              }
            }}
            disabled={isSaving[provider.name] || !apiKeyValues[provider.name]}
            className="w-full"
          >
            <Save className="h-4 w-4 mr-2" />
            Update {provider.name} Settings
          </Button>

          {/* Provider-specific information */}
          {isPortkey && (
            <Alert>
              <AlertDescription>
                <strong>Portkey Features:</strong>
                <ul className="list-disc list-inside mt-2 space-y-1 text-sm">
                  <li>Unified API for 300+ models</li>
                  <li>Automatic retries and fallbacks</li>
                  <li>Request caching and optimization</li>
                  <li>Detailed analytics and monitoring</li>
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {isOpenRouter && (
            <Alert>
              <AlertDescription>
                <strong>OpenRouter Features:</strong>
                <ul className="list-disc list-inside mt-2 space-y-1 text-sm">
                  <li>Access to latest models</li>
                  <li>Competitive pricing</li>
                  <li>No rate limits on most models</li>
                  <li>Automatic model routing</li>
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    );
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading provider settings...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <Alert>
        <AlertDescription>
          <strong>Setup Instructions:</strong>
          <ol className="list-decimal list-inside mt-2 space-y-1">
            <li>Get your API keys from <a href="https://portkey.ai" target="_blank" rel="noopener noreferrer" className="underline">Portkey</a> and <a href="https://openrouter.ai" target="_blank" rel="noopener noreferrer" className="underline">OpenRouter</a></li>
            <li>Enter the API keys below (they will be stored as environment variables)</li>
            <li>Enable the providers you want to use</li>
            <li>Set priority (0 = highest) to control fallback order</li>
          </ol>
        </AlertDescription>
      </Alert>

      {/* Provider Cards */}
      <div className="grid gap-6">
        {providers
          .sort((a, b) => a.priority - b.priority)
          .map(provider => renderProvider(provider))}
      </div>

      {/* Status Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Routing Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Active Providers:</span>
              <span className="font-medium">
                {providers.filter(p => p.is_active).length} / {providers.length}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Primary Provider:</span>
              <span className="font-medium capitalize">
                {providers.find(p => p.priority === 0)?.name || 'None'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Fallback Order:</span>
              <span className="font-medium">
                {providers
                  .filter(p => p.is_active)
                  .sort((a, b) => a.priority - b.priority)
                  .map(p => p.name)
                  .join(' → ')}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};