# Voice Synthesis Standardization - Phase 2 Execution Plan

## Overview
Based on the Phase 1 audit findings, this document outlines the detailed execution plan for Phase 2: Design & Architecture.

## Phase 2 Objectives
1. Design comprehensive ElevenLabs service architecture
2. Create migration strategy for existing implementations
3. Design feature flag system for gradual rollout
4. Plan infrastructure migration to cloud services

## Task Breakdown

### 2.1 ElevenLabs Service Design (Days 4-5)

#### 2.1.1 Core Service Architecture
```python
# Proposed structure: core/services/elevenlabs_service.py
class ElevenLabsService:
    """Centralized voice synthesis service"""
    
    def __init__(self):
        self.client = None
        self.voice_cache = {}
        self.feature_flags = {}
    
    async def initialize(self):
        """Initialize ElevenLabs client with retry logic"""
        pass
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str = None,
        model_id: str = "eleven_monolingual_v1",
        stream: bool = False
    ):
        """Main synthesis method with caching"""
        pass
    
    async def stream_speech(self, text: str, voice_id: str):
        """Streaming synthesis for real-time applications"""
        pass
```

#### 2.1.2 Voice Management
- Voice profile mapping (old provider → ElevenLabs)
- Voice cloning capabilities for custom voices
- Voice preview and selection API

#### 2.1.3 Error Handling & Resilience
- Retry logic with exponential backoff
- Circuit breaker for API failures
- Fallback to cached audio when available
- Graceful degradation to browser TTS

### 2.2 Migration Strategy (Day 5)

#### 2.2.1 Code Migration Plan
1. **Immediate Actions**:
   - Remove `resemble==1.5.0` from requirements/base.txt
   - Update frozen requirements files
   - Clean virtual environment

2. **Service Updates**:
   ```python
   # Current: agent/app/services/natural_language_processor.py
   async def text_to_speech(self, text: str) -> Optional[str]:
       """Convert text to speech using ElevenLabs"""
       # Already migrated - needs verification
   
   # New: Centralized service usage
   from core.services.elevenlabs_service import ElevenLabsService
   
   voice_service = ElevenLabsService()
   audio_url = await voice_service.synthesize_speech(text)
   ```

3. **Frontend Migration**:
   - Update VoiceSynthesizer component
   - Remove browser TTS fallback option
   - Implement streaming support

#### 2.2.2 Data Migration Plan
1. **PGVector → Weaviate Cloud**:
   - Export existing embeddings
   - Transform to Weaviate format
   - Batch import with validation
   - Parallel run for verification

2. **Remove Pinecone References**:
   - Delete `shared/memory/pinecone_adapter.py`
   - Update environment configurations
   - Remove from dependency injection

### 2.3 Feature Flag System (Day 5)

#### 2.3.1 Flag Structure
```yaml
voice_synthesis_flags:
  use_elevenlabs: true
  enable_streaming: false
  enable_voice_cloning: false
  fallback_to_browser: true
  cache_audio: true
  
rollout_percentage:
  dev: 100
  staging: 100
  production: 10  # Gradual rollout
```

#### 2.3.2 Implementation
```python
class FeatureFlagService:
    def is_enabled(self, flag: str, user_id: str = None) -> bool:
        """Check if feature is enabled for user"""
        if user_id and self.is_in_rollout_group(user_id, flag):
            return True
        return self.get_flag_value(flag)
```

### 2.4 Infrastructure Design (Day 5)

#### 2.4.1 Weaviate Cloud Configuration
```yaml
weaviate_config:
  cluster_url: "https://cherry_ai-ai.weaviate.network"
  auth_type: "api_key"
  collections:
    - name: "voice_embeddings"
      vectorizer: "text2vec-openai"
    - name: "audio_cache"
      vectorizer: "none"
```

#### 2.4.2 Airbyte Cloud Setup
```yaml
airbyte_config:
  workspace_id: "cherry_ai-ai-prod"
  connections:
    - source: "postgres"
      destination: "weaviate"
      sync_frequency: "hourly"
    - source: "application_logs"
      destination: "analytics_warehouse"
```

## Implementation Checklist

### Day 4 Tasks:
- [ ] Design ElevenLabs service interface
- [ ] Create voice mapping schema
- [ ] Design error handling strategy
- [ ] Plan caching architecture

### Day 5 Tasks:
- [ ] Complete migration strategy document
- [ ] Design feature flag system
- [ ] Create infrastructure migration plan
- [ ] Prepare design review presentation

## Design Decisions

### 1. Service Architecture
- **Decision**: Centralized service with dependency injection
- **Rationale**: Easier testing, better separation of concerns
- **Alternative**: Direct client usage (rejected for tight coupling)

### 2. Caching Strategy
- **Decision**: Two-tier cache (memory + persistent)
- **Rationale**: Reduce API costs, improve latency
- **Implementation**: Redis for hot cache, S3 for cold storage

### 3. Streaming vs Batch
- **Decision**: Support both modes
- **Rationale**: Different use cases require different approaches
- **Default**: Batch for most cases, streaming for real-time

### 4. Voice Selection
- **Decision**: Automatic mapping with manual override
- **Rationale**: Smooth migration while allowing customization
- **Mapping**: Stored in configuration with UI management

## Risk Mitigation

### Technical Risks
1. **API Rate Limits**
   - Mitigation: Implement request queuing and caching
   - Monitoring: Track API usage metrics

2. **Latency Issues**
   - Mitigation: Pre-generate common phrases
   - Fallback: Progressive enhancement with browser TTS

3. **Cost Overruns**
   - Mitigation: Set usage alerts and limits
   - Control: Per-user quotas in production

### Migration Risks
1. **Data Loss**
   - Mitigation: Backup before migration
   - Verification: Checksum validation

2. **Service Disruption**
   - Mitigation: Feature flags for gradual rollout
   - Rollback: One-click reversion capability

## Success Criteria

### Phase 2 Completion:
- [ ] Service design approved by architect
- [ ] Migration plan reviewed and approved
- [ ] Feature flag system designed
- [ ] Infrastructure plan validated
- [ ] All design documents complete
- [ ] Risk assessment updated

### Quality Gates:
- Design follows SOLID principles
- API contracts are well-defined
- Error scenarios are documented
- Performance requirements are specified
- Security considerations addressed

## Next Steps

Upon completion of Phase 2:
1. Begin Phase 3: Core Implementation
2. Set up development environment
3. Create service skeleton
4. Implement basic functionality
5. Write initial tests

---

Generated: 2025-01-06
Phase: 2 of 9
Status: Ready to Execute