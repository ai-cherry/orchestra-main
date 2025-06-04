# Factory AI Droid Integration Plan

## Executive Summary
This plan details the integration of Factory AI Droid system into our existing cherry_ai project, ensuring compatibility with Roo coder while enhancing our AI coding capabilities.

## Integration Objectives
1. **Preserve Existing Functionality**: Maintain all Roo coder features and MCP servers
2. **Enhance with Factory AI**: Add Factory AI Droids as complementary agents
3. **Maximize Synergy**: Leverage both systems for optimal performance
4. **Maintain Modularity**: Keep systems loosely coupled for flexibility

## Current State Analysis

### Existing Infrastructure
- **MCP Servers**: 5 active servers (conductor, memory, weaviate, deployment, tools)
- **Roo Modes**: 10 specialized modes with specific models and roles
- **Tech Stack**: PostgreSQL, Weaviate, Pulumi, Vultr
- **Context Management**: MCP-based with vector store integration

### Factory AI Requirements
- **Droid Types**: Architect, Code, Debug, Reliability, Knowledge
- **Infrastructure**: Factory Bridge CLI, context management
- **Integration Points**: Vultr API, PostgreSQL, Weaviate

## Integration Architecture

### 1. Dual-System Approach
```
┌─────────────────────────────────────────────────┐
│                cherry_ai Project                 │
├─────────────────────┬───────────────────────────┤
│    Roo System       │      Factory AI System    │
├─────────────────────┼───────────────────────────┤
│ • 10 Roo Modes      │ • 5 Factory Droids        │
│ • MCP Servers       │ • Factory Bridge          │
│ • .roomodes config  │ • .factory/ config        │
└─────────────────────┴───────────────────────────┘
                      ↓
              Shared Resources
         • PostgreSQL • Weaviate
         • Pulumi     • Vultr
```

### 2. MCP Server Enhancement Strategy
Instead of replacing MCP servers, we'll create Factory AI adapters:

```python
# mcp_server/adapters/factory_adapter.py
class FactoryAIDroidAdapter:
    """Bridges Factory AI Droids with MCP servers"""
    def __init__(self, mcp_server, droid_type):
        self.mcp_server = mcp_server
        self.droid_type = droid_type
```

### 3. Configuration Structure
```
cherry_ai-main/
├── .roo/                    # Existing Roo configuration
├── .factory/                # New Factory AI configuration
│   ├── config.yaml          # Main Factory config
│   ├── droids/              # Droid-specific rules
│   │   ├── architect.md
│   │   ├── code.md
│   │   ├── debug.md
│   │   ├── reliability.md
│   │   └── knowledge.md
│   ├── context.py           # Context management
│   └── bridge/              # Factory Bridge integration
├── mcp_server/
│   ├── servers/             # Existing MCP servers
│   └── adapters/            # New Factory adapters
└── factory_integration/     # Integration utilities
```

## Implementation Details

### Phase 1: Foundation Setup

#### 1.1 Create Factory Configuration
```yaml
# .factory/config.yaml
version: "1.0"
project_name: "Cherry AI with Factory Droids"
integration_mode: "hybrid"

droids:
  architect:
    model: "anthropic/claude-opus-4"
    mcp_server: "conductor"
    capabilities:
      - system_design
      - pulumi_iac
      
  code:
    model: "google/gemini-2.5-flash-preview-05-20"
    mcp_server: "tools"
    capabilities:
      - fast_generation
      - code_optimization
      
  debug:
    model: "openai/gpt-4.1"
    mcp_server: "tools"
    capabilities:
      - error_diagnosis
      - query_optimization
      
  reliability:
    model: "anthropic/claude-sonnet-4"
    mcp_server: "deployment"
    capabilities:
      - incident_management
      - monitoring
      
  knowledge:
    model: "anthropic/claude-sonnet-4"
    mcp_server: "memory"
    capabilities:
      - vector_operations
      - documentation

infrastructure:
  vultr:
    api_key: "${VULTR_API_KEY}"
    pulumi_stack: "main"
  
  postgresql:
    uri: "postgresql://user:pass@localhost:5432/main"
    schema_permissions: "RW"
  
  weaviate:
    endpoint: "http://localhost:8080"
    vector_space: "code_embeddings"
```

#### 1.2 Factory Bridge Setup Script
```bash
# factory_integration/setup_bridge.sh
#!/bin/bash
# Install Factory Bridge with our specific configuration

curl -sSL https://factory.ai/install-bridge | bash -s -- \
  --vultr-token=$VULTR_TOKEN \
  --pulumi-passphrase=$PULUMI_PASSPHRASE \
  --config-path=.factory/config.yaml
```

### Phase 2: MCP Integration

#### 2.1 Factory-MCP Adapter
```python
# mcp_server/adapters/factory_mcp_adapter.py
from typing import Dict, Any
import asyncio
from factory import FactoryDroid

class FactoryMCPAdapter:
    """Enables Factory AI Droids to work through MCP servers"""
    
    def __init__(self, mcp_server, droid_config: Dict[str, Any]):
        self.mcp_server = mcp_server
        self.droid = FactoryDroid(droid_config)
        
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route requests between Factory Droid and MCP server"""
        # Translate MCP request to Factory format
        factory_request = self._translate_to_factory(request)
        
        # Process through Factory Droid
        factory_response = await self.droid.process(factory_request)
        
        # Translate back to MCP format
        return self._translate_to_mcp(factory_response)
```

### Phase 3: Context Management Enhancement

#### 3.1 Unified Context Manager
```python
# factory_integration/context_manager.py
from factory import ContextManager as FactoryContext
from mcp_server.storage.memory_store import MemoryStore

class UnifiedContextManager:
    """Manages context for both Roo and Factory AI systems"""
    
    def __init__(self):
        self.factory_context = FactoryContext()
        self.mcp_memory = MemoryStore()
        
    def sync_contexts(self):
        """Synchronize context between systems"""
        # Pull from MCP memory
        mcp_data = self.mcp_memory.get_all()
        
        # Update Factory context
        self.factory_context.update(mcp_data)
        
        # Register shared resources
        self.factory_context.add_repository("https://github.com/your/repo")
        self.factory_context.link_database("postgres", "main_db")
        self.factory_context.register_vector_store("weaviate", "code_vectors")
```

### Phase 4: Workflow Integration

#### 4.1 Hybrid Workflow conductor
```python
# factory_integration/hybrid_conductor.py
class Hybridconductor:
    """cherry_aites workflows across Roo modes and Factory droids"""
    
    def __init__(self):
        self.roo_modes = self._load_roo_modes()
        self.factory_droids = self._load_factory_droids()
        
    async def execute_task(self, task_type: str, context: Dict):
        """Route tasks to appropriate system"""
        if task_type in ['architect', 'code', 'debug']:
            # Can use either system based on availability
            if self._should_use_factory(task_type, context):
                return await self._execute_factory_droid(task_type, context)
            else:
                return await self._execute_roo_mode(task_type, context)
```

## Migration Strategy

### Step 1: Parallel Installation
1. Install Factory AI alongside existing setup
2. No changes to existing Roo configuration
3. Test Factory AI in isolation

### Step 2: Gradual Integration
1. Start with non-critical tasks
2. Route specific workflows to Factory droids
3. Monitor performance and compatibility

### Step 3: Full Integration
1. Enable hybrid coordination
2. Implement automatic task routing
3. Optimize based on performance metrics

## Risk Mitigation

### Compatibility Risks
- **Risk**: Conflicts between Roo and Factory systems
- **Mitigation**: Isolated namespaces, adapter pattern

### Performance Risks
- **Risk**: Overhead from dual systems
- **Mitigation**: Selective routing, caching, monitoring

### Context Management Risks
- **Risk**: Context synchronization issues
- **Mitigation**: Unified context manager, versioning

## Success Metrics
1. **Development Speed**: 40% reduction in task completion time
2. **System Stability**: No degradation in existing functionality
3. **Resource Utilization**: <10% overhead from integration
4. **Context Accuracy**: 95%+ context relevance across systems

## Next Steps
1. Hand off to Architect mode for detailed system design
2. Implement foundation components in Code mode
3. Validate integration in Quality mode