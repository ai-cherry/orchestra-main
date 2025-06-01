# Orchestra AI Cleanup and Optimization Plan

## Overview
This document outlines conflicts, redundancies, and optimization opportunities identified in the Orchestra AI codebase, with specific actions to address each issue.

## 1. OpenRouter Integration Enhancement

### Current State
- OpenRouter is treated as just another LLM provider
- Not leveraging its access to 300+ models
- Redundant with Portkey's routing capabilities

### Recommended Actions
1. **Position OpenRouter as a Model Catalog**:
   ```typescript
   // admin-ui/src/config/portkey.config.ts
   export const OPENROUTER_MODELS = {
     // Fast & Cheap
     'mixtral-8x7b': { provider: 'openrouter', model: 'mistralai/mixtral-8x7b-instruct', cost: 0.0006 },
     'llama-3-70b': { provider: 'openrouter', model: 'meta-llama/llama-3-70b-instruct', cost: 0.0008 },
     
     // Balanced
     'claude-3-haiku': { provider: 'openrouter', model: 'anthropic/claude-3-haiku', cost: 0.0025 },
     'gpt-3.5-turbo': { provider: 'openrouter', model: 'openai/gpt-3.5-turbo', cost: 0.002 },
     
     // Premium
     'gpt-4-turbo': { provider: 'openrouter', model: 'openai/gpt-4-turbo', cost: 0.02 },
     'claude-3-opus': { provider: 'openrouter', model: 'anthropic/claude-3-opus', cost: 0.06 }
   };
   ```

2. **Add Model Selection UI**:
   - Create ModelSelector component for choosing from 300+ models
   - Group by capability (coding, creative, analysis, etc.)
   - Show pricing and performance metrics

## 2. Component Redundancy Cleanup

### OmniSearch Consolidation
**Issue**: Both `OmniSearch` and `OmniSearchEnhanced` exist

**Actions**:
1. Replace OmniSearch with OmniSearchEnhanced in TopBar.tsx:
   ```typescript
   import OmniSearchEnhanced from './OmniSearchEnhanced';
   // Use <OmniSearchEnhanced /> instead of <OmniSearch />
   ```
2. Delete the original OmniSearch.tsx file
3. Rename OmniSearchEnhanced to OmniSearch for consistency

## 3. Database Reference Cleanup

### Legacy Database References
**Issue**: MongoDB, Redis, DragonflyDB references still exist despite consolidation to PostgreSQL + Weaviate

**Actions to Remove**:
1. **Files to Delete**:
   - `agent/core/redis_alloydb_sync.py`
   - `test_dragonfly_connection.py`
   - `dragonfly_config.py`
   - Any MongoDB-specific files

2. **Update Context Files**:
   - `ai_context_reviewer.py`: Remove MongoDB/Redis references
   - `ai_context_debugger.py`: Remove MongoDB/DragonflyDB references
   - `tools/orchestra_cli.py`: Remove Redis health checks

3. **Update Environment Variables**:
   - Remove from `.env.example`: `MONGODB_URI`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
   - Remove from GitHub secrets documentation

## 4. TypeScript Build Errors

### Fix Import and Type Issues
1. **Remove unused imports**:
   ```typescript
   // Remove 'Zap' from imports if not used
   import { Search, Paperclip, Loader2, Sparkles, Brain, FileSearch, Globe } from 'lucide-react';
   ```

2. **Fix User type**:
   ```typescript
   // Add username to User interface or use optional chaining
   {user?.username || user?.email || 'User'}
   ```

3. **Fix ReactNode type issues in orchestration nodes**:
   ```typescript
   // Ensure all data properties are typed correctly
   interface NodeData {
     name?: string;
     type?: string;
     description?: string;
     // ... other properties
   }
   ```

## 5. Deployment Script Consolidation

### Current Redundancy
Multiple deployment scripts with overlapping functionality:
- `deploy_admin_ui.sh`
- `deploy_admin_ui_quick.sh`
- `deploy_to_vultr.sh`
- `quick_deploy.sh`

### Recommended Action
Create single unified deployment script:
```bash
#!/bin/bash
# deploy.sh - Unified deployment script

SERVICE=${1:-all}  # admin-ui, api, or all

case $SERVICE in
  admin-ui)
    deploy_admin_ui()
    ;;
  api)
    deploy_api()
    ;;
  all)
    deploy_admin_ui()
    deploy_api()
    ;;
esac
```

## 6. API Key Management Strategy

### Current State
- Direct API keys in GitHub secrets
- Portkey virtual keys
- OpenRouter keys
- Redundant key management

### Recommended Architecture
```
┌─────────────────┐
│   Application   │
└────────┬────────┘
         │
┌────────▼────────┐
│     Portkey     │ (Primary Gateway)
│  - Virtual Keys │
│  - Monitoring   │
│  - Fallbacks    │
└────────┬────────┘
         │
┌────────▼────────┐
│   OpenRouter    │ (Model Catalog)
│  - 300+ Models  │
│  - As fallback  │
└─────────────────┘
```

## 7. Configuration File Consolidation

### Current Redundancy
Multiple LLM configuration files:
- `config/litellm_config.yaml`
- `core/business/llm/provider.py`
- `core/orchestrator/src/services/llm/providers.py`
- `.roo/scripts/portkey-router.js`

### Recommended Action
Single source of truth in `admin-ui/src/config/ai.config.ts`:
```typescript
export const AI_CONFIG = {
  primaryGateway: 'portkey',
  fallbackGateway: 'openrouter',
  providers: { /* ... */ },
  models: { /* ... */ },
  routing: { /* ... */ }
};
```

## 8. Syntax and Formatting Fixes

### Indentation Issues
Run formatting on all files:
```bash
# Python files
black . --line-length 120

# TypeScript/JavaScript files
cd admin-ui && npx prettier --write "src/**/*.{ts,tsx,js,jsx}"
```

### Import Organization
```bash
# Python
isort . --profile black

# TypeScript
cd admin-ui && npx eslint --fix "src/**/*.{ts,tsx}"
```

## Implementation Priority

1. **High Priority (Week 1)**:
   - Fix OmniSearch redundancy
   - Clean up database references
   - Fix TypeScript build errors

2. **Medium Priority (Week 2)**:
   - Enhance OpenRouter integration
   - Consolidate deployment scripts
   - Unify configuration files

3. **Low Priority (Week 3-4)**:
   - Add model selection UI
   - Optimize API key management
   - Run full formatting pass

## Success Metrics

- [ ] Zero TypeScript build errors
- [ ] No legacy database references
- [ ] Single OmniSearch component
- [ ] Unified deployment process
- [ ] 300+ models accessible via OpenRouter
- [ ] All code properly formatted

## Next Steps

1. Create feature branch: `feat/cleanup-and-optimization`
2. Address high-priority items first
3. Test each change thoroughly
4. Deploy incrementally
5. Monitor for any regressions 