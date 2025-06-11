/**
 * LLM Test Interface Component
 * Allows testing model configurations before applying them
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/components/ui/use-toast';
import { 
  Send, Loader2, CheckCircle, XCircle, 
  Clock, Zap, DollarSign, Hash
} from 'lucide-react';

interface Model {
  id: number;
  model_identifier: string;
  display_name: string;
  provider_name: string;
}

interface TestResult {
  status: 'success' | 'error';
  model: string;
  response?: string;
  error?: string;
  tokens_used?: number;
  latency_ms?: number;
}

export const LLMTestInterface: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedProvider, setSelectedProvider] = useState('');
  const [testPrompt, setTestPrompt] = useState('Hello! Please respond with a brief introduction of yourself and confirm you can process this message.');
  const [temperature, setTemperature] = useState(0.5);
  const [maxTokens, setMaxTokens] = useState(100);
  const [isLoading, setIsLoading] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const { toast } = useToast();

  // Load models on component mount
  React.useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const response = await fetch('/api/admin/llm/models?available_only=true');
      if (!response.ok) throw new Error('Failed to load models');
      const data = await response.json();
      setModels(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load available models',
        variant: 'destructive',
      });
    }
  };

  const runTest = async () => {
    if (!selectedModel || !selectedProvider) {
      toast({
        title: 'Error',
        description: 'Please select a model and provider',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    setTestResult(null);

    try {
      const response = await fetch('/api/admin/llm/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_identifier: selectedModel,
          provider: selectedProvider,
          test_prompt: testPrompt,
          temperature: temperature,
          max_tokens: maxTokens,
        }),
      });

      if (!response.ok) throw new Error('Test request failed');
      
      const result = await response.json();
      setTestResult(result);
      
      if (result.status === 'success') {
        toast({
          title: 'Test Successful',
          description: `Model responded in ${result.latency_ms}ms`,
        });
      } else {
        toast({
          title: 'Test Failed',
          description: result.error || 'Unknown error occurred',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to run test',
        variant: 'destructive',
      });
      setTestResult({
        status: 'error',
        model: selectedModel,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleModelSelect = (modelId: string) => {
    const model = models.find(m => m.id.toString() === modelId);
    if (model) {
      setSelectedModel(model.model_identifier);
      setSelectedProvider(model.provider_name);
    }
  };

  const estimateCost = () => {
    if (!testResult || testResult.status !== 'success' || !testResult.tokens_used) {
      return null;
    }
    
    // Rough cost estimates per 1k tokens (these should come from the model data)
    const costEstimates: Record<string, number> = {
      'gpt-4': 0.03,
      'gpt-3.5': 0.002,
      'claude-3-opus': 0.015,
      'claude-3-sonnet': 0.003,
      'gemini-1.5-pro': 0.007,
    };
    
    const modelKey = Object.keys(costEstimates).find(key => 
      selectedModel.toLowerCase().includes(key)
    );
    
    if (modelKey) {
      const cost = (testResult.tokens_used / 1000) * costEstimates[modelKey];
      return cost.toFixed(6);
    }
    
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Test Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Test Configuration</CardTitle>
          <CardDescription>
            Configure and test a model before using it in production
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Model Selection */}
          <div>
            <Label>Select Model</Label>
            <Select value={selectedModel} onValueChange={handleModelSelect}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a model to test" />
              </SelectTrigger>
              <SelectContent>
                {models.map((model) => (
                  <SelectItem key={model.id} value={model.id.toString()}>
                    <div className="flex items-center gap-2">
                      <span>{model.display_name}</span>
                      <Badge variant="outline" className="text-xs">
                        {model.provider_name}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Test Prompt */}
          <div>
            <Label>Test Prompt</Label>
            <Textarea
              value={testPrompt}
              onChange={(e) => setTestPrompt(e.target.value)}
              placeholder="Enter your test prompt..."
              rows={4}
              className="font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground mt-1">
              This prompt will be sent to the selected model
            </p>
          </div>

          {/* Temperature */}
          <div>
            <div className="flex justify-between mb-2">
              <Label>Temperature</Label>
              <span className="text-sm text-muted-foreground">{temperature}</span>
            </div>
            <Slider
              value={[temperature]}
              onValueChange={([value]) => setTemperature(value)}
              min={0}
              max={2}
              step={0.1}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Lower = more focused, Higher = more creative
            </p>
          </div>

          {/* Max Tokens */}
          <div>
            <div className="flex justify-between mb-2">
              <Label>Max Tokens</Label>
              <span className="text-sm text-muted-foreground">{maxTokens}</span>
            </div>
            <Slider
              value={[maxTokens]}
              onValueChange={([value]) => setMaxTokens(value)}
              min={10}
              max={1000}
              step={10}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Maximum response length
            </p>
          </div>

          {/* Run Test Button */}
          <Button
            onClick={runTest}
            disabled={isLoading || !selectedModel}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Running Test...
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Run Test
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Test Results */}
      {testResult && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle>Test Results</CardTitle>
                <CardDescription>
                  Model: {testResult.model}
                </CardDescription>
              </div>
              <Badge variant={testResult.status === 'success' ? 'default' : 'destructive'}>
                {testResult.status === 'success' ? (
                  <>
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Success
                  </>
                ) : (
                  <>
                    <XCircle className="h-3 w-3 mr-1" />
                    Failed
                  </>
                )}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {testResult.status === 'success' ? (
              <>
                {/* Response */}
                <div>
                  <Label>Response</Label>
                  <div className="mt-2 p-4 bg-muted rounded-lg">
                    <pre className="whitespace-pre-wrap text-sm font-mono">
                      {testResult.response}
                    </pre>
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      <span className="text-sm">Latency</span>
                    </div>
                    <p className="text-lg font-medium">
                      {testResult.latency_ms}ms
                    </p>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Hash className="h-4 w-4" />
                      <span className="text-sm">Tokens</span>
                    </div>
                    <p className="text-lg font-medium">
                      {testResult.tokens_used || 'N/A'}
                    </p>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <DollarSign className="h-4 w-4" />
                      <span className="text-sm">Est. Cost</span>
                    </div>
                    <p className="text-lg font-medium">
                      ${estimateCost() || 'N/A'}
                    </p>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <Zap className="h-4 w-4" />
                      <span className="text-sm">Speed</span>
                    </div>
                    <p className="text-lg font-medium">
                      {testResult.latency_ms && testResult.tokens_used
                        ? `${(testResult.tokens_used / (testResult.latency_ms / 1000)).toFixed(0)} tok/s`
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <Alert variant="destructive">
                <AlertDescription>
                  <strong>Error:</strong> {testResult.error}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tips */}
      <Alert>
        <AlertDescription>
          <strong>Testing Tips:</strong>
          <ul className="list-disc list-inside mt-2 space-y-1 text-sm">
            <li>Test with prompts similar to your actual use cases</li>
            <li>Compare response quality across different models</li>
            <li>Monitor latency to ensure acceptable performance</li>
            <li>Check token usage to estimate costs</li>
            <li>Test edge cases and error handling</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );
};