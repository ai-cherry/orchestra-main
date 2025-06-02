# Cherry AI Admin Interface - Implementation Guide

## Quick Start Guide

This guide provides step-by-step instructions for implementing the unified AI interface enhancements while maintaining the existing Cherry dark theme aesthetic.

## Prerequisites

- Node.js 18+ and pnpm
- PostgreSQL 15+ with vector extensions
- Redis 7+ for caching
- Weaviate instance for vector search
- Vultr account for deployment

## Implementation Steps

### Phase 1: Foundation Components (Week 1-2)

#### 1.1 Universal Command Hub

**Step 1: Enhance OmniSearch Component**

```typescript
// admin-ui/src/components/layout/EnhancedOmniSearch.tsx
import { useState, useCallback, useEffect } from 'react';
import { useDebounce } from '@/hooks/useDebounce';
import { useNLPProcessor } from '@/hooks/useNLPProcessor';
import { useModelRouter } from '@/hooks/useModelRouter';

interface EnhancedOmniSearchProps {
  onCommand: (command: ProcessedCommand) => void;
  className?: string;
}

export const EnhancedOmniSearch: React.FC<EnhancedOmniSearchProps> = ({
  onCommand,
  className
}) => {
  const [query, setQuery] = useState('');
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const debouncedQuery = useDebounce(query, 300);
  
  const { processQuery, suggestions } = useNLPProcessor();
  const { routeQuery } = useModelRouter();
  
  const handleSubmit = useCallback(async () => {
    const intent = await processQuery(debouncedQuery);
    const routing = await routeQuery(intent);
    
    onCommand({
      query: debouncedQuery,
      intent,
      routing,
      timestamp: new Date()
    });
  }, [debouncedQuery, processQuery, routeQuery, onCommand]);
  
  // Voice input handler
  const handleVoiceInput = useCallback(() => {
    if ('webkitSpeechRecognition' in window) {
      const recognition = new webkitSpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
        handleSubmit();
      };
      
      recognition.start();
      setIsVoiceActive(true);
    }
  }, [handleSubmit]);
  
  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center space-x-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          placeholder="Ask anything or type a command..."
          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg 
                     text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
        />
        <button
          onClick={handleVoiceInput}
          className={`p-2 rounded-lg transition-colors ${
            isVoiceActive ? 'bg-purple-600' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          <MicrophoneIcon className="w-5 h-5 text-white" />
        </button>
      </div>
      
      {suggestions.length > 0 && (
        <div className="absolute top-full mt-2 w-full bg-gray-800 border border-gray-700 
                        rounded-lg shadow-xl z-50">
          {suggestions.map((suggestion, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(suggestion.text);
                handleSubmit();
              }}
              className="w-full px-4 py-2 text-left hover:bg-gray-700 
                         flex items-center justify-between"
            >
              <span className="text-white">{suggestion.text}</span>
              <span className="text-xs text-gray-400">{suggestion.type}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
```

**Step 2: Create Command Palette**

```typescript
// admin-ui/src/components/command/CommandPalette.tsx
import { useEffect, useState } from 'react';
import { Dialog } from '@headlessui/react';
import { useCommandRegistry } from '@/hooks/useCommandRegistry';

export const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const { commands, executeCommand } = useCommandRegistry();
  
  // Global keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
  
  const filteredCommands = commands.filter(cmd =>
    cmd.name.toLowerCase().includes(search.toLowerCase()) ||
    cmd.description.toLowerCase().includes(search.toLowerCase())
  );
  
  return (
    <Dialog
      open={isOpen}
      onClose={() => setIsOpen(false)}
      className="fixed inset-0 z-50 overflow-y-auto"
    >
      <div className="flex items-center justify-center min-h-screen">
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        
        <div className="relative bg-gray-900 rounded-xl shadow-2xl w-full max-w-2xl 
                        mx-4 border border-gray-800">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Type a command or search..."
            className="w-full px-6 py-4 bg-transparent text-white placeholder-gray-400 
                       border-b border-gray-800 focus:outline-none"
            autoFocus
          />
          
          <div className="max-h-96 overflow-y-auto">
            {filteredCommands.map((command) => (
              <button
                key={command.id}
                onClick={() => {
                  executeCommand(command.id);
                  setIsOpen(false);
                }}
                className="w-full px-6 py-3 flex items-center justify-between 
                           hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <command.icon className="w-5 h-5 text-purple-500" />
                  <div className="text-left">
                    <div className="text-white font-medium">{command.name}</div>
                    <div className="text-sm text-gray-400">{command.description}</div>
                  </div>
                </div>
                {command.shortcut && (
                  <kbd className="px-2 py-1 text-xs bg-gray-800 rounded text-gray-400">
                    {command.shortcut}
                  </kbd>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
    </Dialog>
  );
};
```

**Step 3: Database Schema Updates**

```sql
-- Create command history and analytics tables
CREATE TABLE IF NOT EXISTS command_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  command TEXT NOT NULL,
  intent_classification JSONB NOT NULL,
  models_used TEXT[] NOT NULL,
  execution_time_ms INTEGER NOT NULL,
  success BOOLEAN NOT NULL DEFAULT true,
  error_message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX idx_command_history_user_time ON command_history(user_id, created_at DESC);
CREATE INDEX idx_command_history_intent ON command_history USING GIN(intent_classification);
CREATE INDEX idx_command_history_models ON command_history USING GIN(models_used);

-- Partitioning for scalability
CREATE TABLE command_history_2025_01 PARTITION OF command_history
  FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

#### 1.2 Adaptive LLM Routing Enhancement

**Step 1: Create ML-based Router**

```typescript
// admin-ui/src/services/AdaptiveLLMRouter.ts
import { LRUCache } from 'lru-cache';
import { ModelPerformanceTracker } from './ModelPerformanceTracker';

export class AdaptiveLLMRouter {
  private cache: LRUCache<string, RoutingDecision>;
  private performanceTracker: ModelPerformanceTracker;
  private costOptimizer: CostOptimizer;
  
  constructor() {
    this.cache = new LRUCache({
      max: 1000,
      ttl: 1000 * 60 * 5 // 5 minutes
    });
    
    this.performanceTracker = new ModelPerformanceTracker();
    this.costOptimizer = new CostOptimizer();
  }
  
  async route(query: Query): Promise<RoutingDecision> {
    const cacheKey = this.getCacheKey(query);
    const cached = this.cache.get(cacheKey);
    
    if (cached && !query.forceRefresh) {
      return cached;
    }
    
    // Classify query type
    const queryType = await this.classifyQuery(query);
    
    // Get available models and their current performance
    const models = await this.getAvailableModels();
    const performance = await this.performanceTracker.getMetrics(models);
    
    // Calculate optimal routing
    const decision = await this.calculateOptimalRoute({
      queryType,
      models,
      performance,
      constraints: query.constraints
    });
    
    // Cache the decision
    this.cache.set(cacheKey, decision);
    
    // Track the routing decision
    await this.trackDecision(decision);
    
    return decision;
  }
  
  private async calculateOptimalRoute(params: RoutingParams): Promise<RoutingDecision> {
    const { queryType, models, performance, constraints } = params;
    
    // Score each model based on multiple factors
    const scores = models.map(model => {
      const perfScore = this.calculatePerformanceScore(model, performance);
      const costScore = this.costOptimizer.calculateCostScore(model, queryType);
      const capabilityScore = this.calculateCapabilityScore(model, queryType);
      
      // Weighted combination
      const totalScore = 
        perfScore * 0.3 + 
        costScore * 0.4 + 
        capabilityScore * 0.3;
      
      return { model, score: totalScore };
    });
    
    // Select best model considering constraints
    const selected = this.selectBestModel(scores, constraints);
    
    return {
      model: selected.model,
      reasoning: this.generateReasoning(selected, queryType),
      alternativeModels: this.getAlternatives(scores, selected),
      estimatedCost: this.costOptimizer.estimateCost(selected.model, queryType),
      estimatedLatency: performance[selected.model.id].avgLatency
    };
  }
}
```

**Step 2: Enhanced Routing Dashboard**

```typescript
// admin-ui/src/components/llm/EnhancedLLMRoutingDashboard.tsx
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Heatmap } from '@/components/charts/Heatmap';
import { CostPredictor } from '@/components/llm/CostPredictor';
import { PerformanceMonitor } from '@/components/llm/PerformanceMonitor';

export const EnhancedLLMRoutingDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<RoutingAnalytics | null>(null);
  const [predictions, setPredictions] = useState<CostPredictions | null>(null);
  
  return (
    <div className="space-y-6">
      {/* Cost Prediction Widget */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Cost Optimization</CardTitle>
        </CardHeader>
        <CardContent>
          <CostPredictor
            onPredict={(query) => predictCost(query)}
            predictions={predictions}
          />
        </CardContent>
      </Card>
      
      {/* Performance Heatmap */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Model Performance Heatmap</CardTitle>
        </CardHeader>
        <CardContent>
          <Heatmap
            data={analytics?.performanceMatrix}
            xLabel="Query Type"
            yLabel="Model"
            valueLabel="Latency (ms)"
            colorScheme="purples"
          />
        </CardContent>
      </Card>
      
      {/* A/B Testing Results */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">A/B Testing Results</CardTitle>
        </CardHeader>
        <CardContent>
          <ABTestingResults
            experiments={analytics?.abTests}
            onNewExperiment={createABTest}
          />
        </CardContent>
      </Card>
    </div>
  );
};
```

### Phase 2: Core Features (Week 3-4)

#### 2.1 Research & Analysis Dashboard

**Step 1: Create Research Hub Page**

```typescript
// admin-ui/src/pages/ResearchDashboard.tsx
import { useState } from 'react';
import { MultiModelInsights } from '@/components/research/MultiModelInsights';
import { SourceNetworkGraph } from '@/components/research/SourceNetworkGraph';
import { ConsensusBuilder } from '@/components/research/ConsensusBuilder';

export const ResearchDashboard: React.FC = () => {
  const [activeResearch, setActiveResearch] = useState<Research | null>(null);
  
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-8">Research & Analysis Dashboard</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Multi-Model Insights Panel */}
          <div className="lg:col-span-2">
            <MultiModelInsights
              research={activeResearch}
              onModelSelect={(model) => highlightModelContribution(model)}
            />
          </div>
          
          {/* Source Network Visualization */}
          <div className="lg:col-span-1">
            <SourceNetworkGraph
              sources={activeResearch?.sources}
              onSourceClick={(source) => showSourceDetails(source)}
            />
          </div>
          
          {/* Consensus Builder */}
          <div className="lg:col-span-3">
            <ConsensusBuilder
              responses={activeResearch?.modelResponses}
              onConsensusReached={(consensus) => saveConsensus(consensus)}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
```

**Step 2: Implement Source Network Visualization**

```typescript
// admin-ui/src/components/research/SourceNetworkGraph.tsx
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface SourceNetworkGraphProps {
  sources: Source[];
  onSourceClick: (source: Source) => void;
}

export const SourceNetworkGraph: React.FC<SourceNetworkGraphProps> = ({
  sources,
  onSourceClick
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  
  useEffect(() => {
    if (!sources || !svgRef.current) return;
    
    const width = 600;
    const height = 400;
    
    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove();
    
    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);
    
    // Create force simulation
    const simulation = d3.forceSimulation(sources)
      .force('link', d3.forceLink(links).id(d => d.id))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));
    
    // Add links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .enter().append('line')
      .attr('stroke', '#4B5563')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', d => Math.sqrt(d.value));
    
    // Add nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(sources)
      .enter().append('circle')
      .attr('r', d => Math.sqrt(d.reliability * 20))
      .attr('fill', d => getNodeColor(d.type))
      .attr('stroke', '#9333EA')
      .attr('stroke-width', 2)
      .on('click', (event, d) => onSourceClick(d))
      .call(drag(simulation));
    
    // Add labels
    const label = svg.append('g')
      .selectAll('text')
      .data(sources)
      .enter().append('text')
      .text(d => d.name)
      .attr('font-size', '12px')
      .attr('fill', '#E5E7EB')
      .attr('text-anchor', 'middle');
    
    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      
      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
      
      label
        .attr('x', d => d.x)
        .attr('y', d => d.y - 15);
    });
    
  }, [sources, onSourceClick]);
  
  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white">Source Network</CardTitle>
      </CardHeader>
      <CardContent>
        <svg ref={svgRef} className="w-full h-full" />
      </CardContent>
    </Card>
  );
};
```

#### 2.2 Code & Data Workshop

**Step 1: Multi-LLM Code Editor**

```typescript
// admin-ui/src/components/code/MultiLLMCodeEditor.tsx
import { useState, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { useMultiModelSuggestions } from '@/hooks/useMultiModelSuggestions';

export const MultiLLMCodeEditor: React.FC = () => {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('typescript');
  const { suggestions, requestSuggestions } = useMultiModelSuggestions();
  
  const handleEditorChange = useCallback((value: string | undefined) => {
    if (value) {
      setCode(value);
      // Debounced suggestion request
      requestSuggestions(value, language);
    }
  }, [language, requestSuggestions]);
  
  return (
    <div className="flex h-full">
      {/* Main Editor */}
      <div className="flex-1">
        <Editor
          height="100%"
          language={language}
          value={code}
          onChange={handleEditorChange}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            rulers: [80],
            wordWrap: 'on'
          }}
        />
      </div>
      
      {/* Multi-Model Suggestions Panel */}
      <div className="w-96 bg-gray-900 border-l border-gray-800 overflow-y-auto">
        <div className="p-4">
          <h3 className="text-lg font-semibold text-white mb-4">
            AI Suggestions
          </h3>
          
          {suggestions.map((suggestion, idx) => (
            <div
              key={idx}
              className="mb-4 p-3 bg-gray-800 rounded-lg border border-gray-700"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-purple-400">
                  {suggestion.model}
                </span>
                <span className="text-xs text-gray-400">
                  {suggestion.confidence}% confidence
                </span>
              </div>
              
              <pre className="text-sm text-gray-300 overflow-x-auto">
                {suggestion.code}
              </pre>
              
              <div className="mt-2 flex space-x-2">
                <button
                  onClick={() => applysuggestion(suggestion)}
                  className="px-3 py-1 text-xs bg-purple-600 hover:bg-purple-700 
                           rounded text-white transition-colors"
                >
                  Apply
                </button>
                <button
                  onClick={() => explainSuggestion(suggestion)}
                  className="px-3 py-1 text-xs bg-gray-700 hover:bg-gray-600 
                           rounded text-white transition-colors"
                >
                  Explain
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

**Step 2: Live Execution Environment**

```typescript
// admin-ui/src/components/code/LiveExecutionPanel.tsx
import { useState, useEffect } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';

export const LiveExecutionPanel: React.FC<{ code: string; language: string }> = ({
  code,
  language
}) => {
  const [terminal, setTerminal] = useState<Terminal | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionId, setExecutionId] = useState<string | null>(null);
  
  useEffect(() => {
    const term = new Terminal({
      theme: {
        background: '#111827',
        foreground: '#E5E7EB',
        cursor: '#9333EA'
      }
    });
    
    const fitAddon = new FitAddon();
    const webLinksAddon = new WebLinksAddon();
    
    term.loadAddon(fitAddon);
    term.loadAddon(webLinksAddon);
    
    term.open(document.getElementById('terminal-container')!);
    fitAddon.fit();
    
    setTerminal(term);
    
    // WebSocket connection for live output
    const ws = new WebSocket(`${WS_URL}/execution/${executionId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'output') {
        term.write(data.content);
      } else if (data.type === 'complete') {
        setIsExecuting(false);
      }
    };
    
    return () => {
      ws.close();
      term.dispose();
    };
  }, [executionId]);
  
  const executeCode = async () => {
    setIsExecuting(true);
    
    const response = await fetch('/api/code/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language })
    });
    
    const { executionId } = await response.json();
    setExecutionId(executionId);
  };
  
  return (
    <div className="h-full flex flex-col bg-gray-900">
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <h3 className="text-lg font-semibold text-white">Execution Output</h3>
        <button
          onClick={executeCode}
          disabled={isExecuting}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 
                   rounded text-white transition-colors flex items-center space-x-2"
        >
          {isExecuting ? (
            <>
              <Spinner className="w-4 h-4" />
              <span>Executing...</span>
            </>
          ) : (
            <>
              <PlayIcon className="w-4 h-4" />
              <span>Run Code</span>
            </>
          )}
        </button>
      </div>
      
      <div id="terminal-container" className="flex-1" />
    </div>
  );
};
```

### Phase 3: Advanced Features (Week 5-6)

#### 3.1 Creative Studio

**Step 1: Multi-Modal Canvas**

```typescript
// admin-ui/src/components/creative/CreativeCanvas.tsx
import { useState, useRef } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Canvas } from '@/components/creative/Canvas';
import { AssetLibrary } from '@/components/creative/AssetLibrary';
import { VersionTimeline } from '@/components/creative/VersionTimeline';

export const CreativeStudio: React.FC = () => {
  const [project, setProject] = useState<CreativeProject | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<string>('main');
  
  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen flex bg-gray-950">
        {/* Asset Library Sidebar */}
        <div className="w-64 bg-gray-900 border-r border-gray-800">
          <AssetLibrary
            onAssetSelect={(asset) => addToCanvas(asset)}
          />
        </div>
        
        {/* Main Canvas Area */}
        <div className="flex-1 flex flex-col">
          <Canvas
            project={project}
            version={selectedVersion}
            onUpdate={(updates) => updateProject(updates)}
          />
          
          {/* Version Timeline */}
          <div className="h-32 bg-gray-900 border-t border-gray-800">
            <VersionTimeline
              versions={project?.versions || []}
              selected={selectedVersion}
              onVersionSelect={setSelectedVersion}
            />
          </div>
        </div>
        
        {/* Properties Panel */}
        <div className="w-80 bg-gray-900 border-l border-gray-800">
          <PropertiesPanel
            selectedElement={project?.selectedElement}
            onPropertyChange={(prop, value) => updateProperty(prop, value)}
          />
        </div>
      </div>
    </DndProvider>
  );
};
```

#### 3.2 Unified I/O Matrix

**Step 1: Cross-Modal Processor**

```typescript
// admin-ui/src/services/CrossModalProcessor.ts
export class CrossModalProcessor {
  private modalityDetector: ModalityDetector;
  private translators: Map<string, ModalityTranslator>;
  
  constructor() {
    this.modalityDetector = new ModalityDetector();
    this.translators = new Map([
      ['text-to-image', new TextToImageTranslator()],
      ['image-to-text', new ImageToTextTranslator()],
      ['audio-to-text', new AudioToTextTranslator()],
      ['text-to-audio', new TextToAudioTranslator()]
    ]);
  }
  
  async process(input: MultiModalInput): Promise<MultiModalOutput> {
    // Detect input modality
    const inputModality = await this.modalityDetector.detect(input);
    
    // Determine required output modalities
    const outputModalities = this.determineOutputModalities(
      inputModality,
      input.requestedOutputs
    );
    
    // Process through appropriate translators
    const outputs = await Promise.all(
      outputModalities.map(async (outputModality) => {
        const translatorKey = `${inputModality}-to-${outputModality}`;
        const translator = this.translators.get(translatorKey);
        
        if (!translator) {
          // Chain multiple translators if needed
          return this.chainTranslators(input, inputModality, outputModality);
        }
        
        return translator.translate(input);
      })
    );
    
    return {
      inputs: [input],
      outputs,
      metadata: {
        processingTime: Date.now() - startTime,
        translationPath: this.getTranslationPath(inputModality, outputModalities)
      }
    };
  }
}
```

## Performance Optimization Implementation

### Caching Strategy

```typescript
// admin-ui/src/services/CacheManager.ts
import { LRUCache } from 'lru-cache';
import { openDB, IDBPDatabase } from 'idb';

export class CacheManager {
  private memoryCache: LRUCache<string, any>;
  private indexedDB: IDBPDatabase | null = null;
  
  constructor() {
    // In-memory LRU cache
    this.memoryCache = new LRUCache({
      max: 500,
      ttl: 1000 * 60 * 5, // 5 minutes
      updateAgeOnGet: true
    });
    
    // Initialize IndexedDB for persistent caching
    this.initIndexedDB();
  }
  
  private async initIndexedDB() {
    this.indexedDB = await openDB('CherryAICache', 1, {
      upgrade(db) {
        db.createObjectStore('queries', { keyPath: 'id' });
        db.createObjectStore('models', { keyPath: 'id' });
        db.createObjectStore('results', { keyPath: 'id' });
      }
    });
  }
  
  async get(key: string, options?: CacheOptions): Promise<any> {
    // Check memory cache first
    const memCached = this.memoryCache.get
