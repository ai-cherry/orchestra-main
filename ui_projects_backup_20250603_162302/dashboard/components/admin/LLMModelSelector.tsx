/**
 * LLM Model Selector Component
 * Allows admins to configure which models to use for each use case and tier
 */

import React, { useState, useEffect } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { Save, Plus, Trash2 } from 'lucide-react';
import { UseCase, ModelTier } from '@/types/llm';

interface Model {
  id: number;
  model_identifier: string;
  display_name: string;
  provider_name: string;
  is_available: boolean;
  capabilities: {
    max_tokens: number;
    supports_tools: boolean;
    supports_vision: boolean;
  };
}

interface UseCase {
  id: number;
  use_case: string;
  display_name: string;
  description: string;
  default_temperature: number;
  default_max_tokens: number;
}

interface Assignment {
  id?: number;
  use_case_id: number;
  tier: string;
  primary_model_id: number;
  fallback_model_ids: number[];
  temperature_override?: number;
  max_tokens_override?: number;
  system_prompt_override?: string;
}

interface Props {
  onUpdate?: () => void;
}

export const LLMModelSelector: React.FC<Props> = ({ onUpdate }) => {
  const [models, setModels] = useState<Model[]>([]);
  const [useCases, setUseCases] = useState<UseCase[]>([]);
  const [assignments, setAssignments] = useState<Record<string, Assignment>>({});
  const [selectedUseCase, setSelectedUseCase] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  const tiers: ModelTier[] = ['premium', 'standard', 'economy'];

  // Load models and use cases
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Load models
      const modelsResponse = await fetch('/api/admin/llm/models?available_only=true');
      if (!modelsResponse.ok) throw new Error('Failed to load models');
      const modelsData = await modelsResponse.json();
      setModels(modelsData);

      // Load use cases
      const useCasesResponse = await fetch('/api/admin/llm/use-cases');
      if (!useCasesResponse.ok) throw new Error('Failed to load use cases');
      const useCasesData = await useCasesResponse.json();
      setUseCases(useCasesData);

      // Load assignments
      const assignmentsResponse = await fetch('/api/admin/llm/assignments');
      if (!assignmentsResponse.ok) throw new Error('Failed to load assignments');
      const assignmentsData = await assignmentsResponse.json();

      // Convert to record format
      const assignmentsRecord: Record<string, Assignment> = {};
      assignmentsData.forEach((assignment: any) => {
        const key = `${assignment.use_case}-${assignment.tier}`;
        assignmentsRecord[key] = {
          id: assignment.id,
          use_case_id: assignment.use_case_id,
          tier: assignment.tier,
          primary_model_id: assignment.primary_model?.id || 0,
          fallback_model_ids: assignment.fallback_models?.map((fb: any) => fb.id) || [],
          temperature_override: assignment.temperature_override,
          max_tokens_override: assignment.max_tokens_override,
          system_prompt_override: assignment.system_prompt_override,
        };
      });
      setAssignments(assignmentsRecord);

      // Set first use case as selected
      if (useCasesData.length > 0) {
        setSelectedUseCase(useCasesData[0].use_case);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load configuration data',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const saveAssignment = async (useCase: string, tier: string) => {
    const key = `${useCase}-${tier}`;
    const assignment = assignments[key];
    
    if (!assignment || !assignment.primary_model_id) {
      toast({
        title: 'Error',
        description: 'Please select a primary model',
        variant: 'destructive',
      });
      return;
    }

    setIsSaving(true);
    try {
      const response = await fetch('/api/admin/llm/assignments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          use_case: useCase,
          tier: tier,
          primary_model_id: assignment.primary_model_id,
          fallback_model_ids: assignment.fallback_model_ids,
          temperature_override: assignment.temperature_override,
          max_tokens_override: assignment.max_tokens_override,
          system_prompt_override: assignment.system_prompt_override,
        }),
      });

      if (!response.ok) throw new Error('Failed to save assignment');

      toast({
        title: 'Success',
        description: `Saved ${tier} configuration for ${useCase}`,
      });

      if (onUpdate) onUpdate();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save assignment',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const updateAssignment = (useCase: string, tier: string, updates: Partial<Assignment>) => {
    const key = `${useCase}-${tier}`;
    const useCase_obj = useCases.find(uc => uc.use_case === useCase);
    
    setAssignments(prev => ({
      ...prev,
      [key]: {
        ...prev[key],
        use_case_id: useCase_obj?.id || 0,
        tier,
        ...updates,
      },
    }));
  };

  const addFallbackModel = (useCase: string, tier: string, modelId: number) => {
    const key = `${useCase}-${tier}`;
    const current = assignments[key];
    
    if (current && !current.fallback_model_ids.includes(modelId)) {
      updateAssignment(useCase, tier, {
        fallback_model_ids: [...current.fallback_model_ids, modelId],
      });
    }
  };

  const removeFallbackModel = (useCase: string, tier: string, modelId: number) => {
    const key = `${useCase}-${tier}`;
    const current = assignments[key];
    
    if (current) {
      updateAssignment(useCase, tier, {
        fallback_model_ids: current.fallback_model_ids.filter(id => id !== modelId),
      });
    }
  };

  const renderTierConfiguration = (useCase: string, tier: string) => {
    const key = `${useCase}-${tier}`;
    const assignment = assignments[key] || {
      primary_model_id: 0,
      fallback_model_ids: [],
    };

    return (
      <Card key={tier}>
        <CardHeader>
          <CardTitle className="text-lg capitalize">{tier} Tier</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Primary Model Selection */}
          <div>
            <Label>Primary Model</Label>
            <Select
              value={assignment.primary_model_id?.toString() || ''}
              onValueChange={(value) =>
                updateAssignment(useCase, tier, { primary_model_id: parseInt(value) })
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select primary model" />
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

          {/* Fallback Models */}
          <div>
            <Label>Fallback Models (in order)</Label>
            <div className="space-y-2">
              {assignment.fallback_model_ids.map((modelId, index) => {
                const model = models.find(m => m.id === modelId);
                return (
                  <div key={modelId} className="flex items-center gap-2">
                    <Badge variant="secondary" className="flex-1">
                      {index + 1}. {model?.display_name || 'Unknown'}
                    </Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeFallbackModel(useCase, tier, modelId)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                );
              })}
              
              {/* Add Fallback Model */}
              <Select
                value=""
                onValueChange={(value) => addFallbackModel(useCase, tier, parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Add fallback model" />
                </SelectTrigger>
                <SelectContent>
                  {models
                    .filter(
                      (model) =>
                        model.id !== assignment.primary_model_id &&
                        !assignment.fallback_model_ids.includes(model.id)
                    )
                    .map((model) => (
                      <SelectItem key={model.id} value={model.id.toString()}>
                        {model.display_name} ({model.provider_name})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-xs">Temperature Override</Label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  className="w-full px-2 py-1 text-sm border rounded"
                  placeholder="Default"
                  value={assignment.temperature_override || ''}
                  onChange={(e) =>
                    updateAssignment(useCase, tier, {
                      temperature_override: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                />
              </div>
              <div>
                <Label className="text-xs">Max Tokens Override</Label>
                <input
                  type="number"
                  min="1"
                  max="32000"
                  className="w-full px-2 py-1 text-sm border rounded"
                  placeholder="Default"
                  value={assignment.max_tokens_override || ''}
                  onChange={(e) =>
                    updateAssignment(useCase, tier, {
                      max_tokens_override: e.target.value ? parseInt(e.target.value) : undefined,
                    })
                  }
                />
              </div>
            </div>
          </div>

          {/* Save Button */}
          <Button
            onClick={() => saveAssignment(useCase, tier)}
            disabled={isSaving || !assignment.primary_model_id}
            className="w-full"
          >
            <Save className="h-4 w-4 mr-2" />
            Save {tier} Configuration
          </Button>
        </CardContent>
      </Card>
    );
  };

  if (isLoading) {
    return <div className="text-center py-8">Loading configuration...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Use Case Selection */}
      <Tabs value={selectedUseCase} onValueChange={setSelectedUseCase}>
        <TabsList className="grid grid-cols-4 lg:grid-cols-8">
          {useCases.map((useCase) => (
            <TabsTrigger key={useCase.use_case} value={useCase.use_case}>
              {useCase.display_name}
            </TabsTrigger>
          ))}
        </TabsList>

        {useCases.map((useCase) => (
          <TabsContent key={useCase.use_case} value={useCase.use_case} className="space-y-4">
            <div className="text-sm text-muted-foreground mb-4">
              {useCase.description}
            </div>
            
            {/* Tier Configurations */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {tiers.map((tier) => renderTierConfiguration(useCase.use_case, tier))}
            </div>
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
};