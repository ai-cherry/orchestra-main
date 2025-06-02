import React from 'react';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Info } from 'lucide-react';

export interface PersonaTrait {
  id: string;
  name: string;
  description: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  category: 'personality' | 'behavior' | 'capability' | 'preference';
}

interface PersonaTraitSlidersProps {
  traits: PersonaTrait[];
  onChange: (traitId: string, value: number) => void;
  className?: string;
}

const categoryColors = {
  personality: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  behavior: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  capability: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  preference: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
};

export function PersonaTraitSliders({ traits, onChange, className }: PersonaTraitSlidersProps) {
  // Group traits by category
  const groupedTraits = traits.reduce((acc, trait) => {
    if (!acc[trait.category]) {
      acc[trait.category] = [];
    }
    acc[trait.category].push(trait);
    return acc;
  }, {} as Record<string, PersonaTrait[]>);

  const formatValue = (value: number, unit?: string) => {
    return unit ? `${value}${unit}` : value.toString();
  };

  return (
    <div className={className}>
      {Object.entries(groupedTraits).map(([category, categoryTraits]) => (
        <Card key={category} className="mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="capitalize">{category} Traits</CardTitle>
              <Badge className={categoryColors[category as keyof typeof categoryColors]}>
                {categoryTraits.length} traits
              </Badge>
            </div>
            <CardDescription>
              Adjust {category} characteristics to fine-tune the persona's behavior
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {categoryTraits.map((trait) => (
              <div key={trait.id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Label htmlFor={trait.id} className="text-sm font-medium">
                      {trait.name}
                    </Label>
                    <div className="group relative">
                      <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                      <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block z-10">
                        <div className="bg-popover text-popover-foreground text-xs rounded-md py-1 px-2 shadow-md max-w-xs">
                          {trait.description}
                        </div>
                      </div>
                    </div>
                  </div>
                  <span className="text-sm font-mono text-muted-foreground">
                    {formatValue(trait.value, trait.unit)}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-muted-foreground w-8 text-right">
                    {formatValue(trait.min, trait.unit)}
                  </span>
                  <Slider
                    id={trait.id}
                    value={[trait.value]}
                    onValueChange={(values) => onChange(trait.id, values[0])}
                    min={trait.min}
                    max={trait.max}
                    step={trait.step}
                    className="flex-1"
                  />
                  <span className="text-xs text-muted-foreground w-8">
                    {formatValue(trait.max, trait.unit)}
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Example traits for different personas
export const defaultPersonaTraits: Record<string, PersonaTrait[]> = {
  cherry: [
    // Personality traits
    {
      id: 'empathy',
      name: 'Empathy Level',
      description: 'How understanding and compassionate the persona is',
      value: 85,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'personality',
    },
    {
      id: 'enthusiasm',
      name: 'Enthusiasm',
      description: 'Energy and excitement level in interactions',
      value: 75,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'personality',
    },
    // Behavior traits
    {
      id: 'proactivity',
      name: 'Proactivity',
      description: 'How proactive vs reactive the persona is',
      value: 70,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'behavior',
    },
    {
      id: 'formality',
      name: 'Formality',
      description: 'Communication style from casual to formal',
      value: 30,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'behavior',
    },
    // Capability traits
    {
      id: 'detail_orientation',
      name: 'Detail Orientation',
      description: 'Focus on details vs big picture',
      value: 65,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'capability',
    },
    {
      id: 'creativity',
      name: 'Creativity',
      description: 'Creative and innovative thinking level',
      value: 80,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'capability',
    },
    // Preference traits
    {
      id: 'response_length',
      name: 'Response Length',
      description: 'Preferred length of responses',
      value: 3,
      min: 1,
      max: 5,
      step: 1,
      category: 'preference',
    },
    {
      id: 'humor_level',
      name: 'Humor Level',
      description: 'Amount of humor in interactions',
      value: 60,
      min: 0,
      max: 100,
      step: 10,
      unit: '%',
      category: 'preference',
    },
  ],
  sophia: [
    // Personality traits
    {
      id: 'professionalism',
      name: 'Professionalism',
      description: 'Level of professional demeanor',
      value: 95,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'personality',
    },
    {
      id: 'assertiveness',
      name: 'Assertiveness',
      description: 'How assertive and confident the persona is',
      value: 80,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'personality',
    },
    // Add more traits as needed...
  ],
  karen: [
    // Personality traits
    {
      id: 'precision',
      name: 'Precision',
      description: 'Accuracy and exactness in communication',
      value: 90,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'personality',
    },
    {
      id: 'patience',
      name: 'Patience',
      description: 'Level of patience in interactions',
      value: 85,
      min: 0,
      max: 100,
      step: 5,
      unit: '%',
      category: 'personality',
    },
    // Add more traits as needed...
  ],
};