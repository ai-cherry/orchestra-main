# Voice Synthesis and Infrastructure Audit Report

## Executive Summary
Comprehensive audit of voice synthesis implementations and infrastructure references across the Cherry AI codebase. This report identifies all instances requiring migration to standardize on ElevenLabs API and cloud infrastructure.

## Audit Findings

### 1. Voice Synthesis References

#### 1.1 Google Cloud TTS (118 references)
**Key Files:**
- `admin-ui/node_modules/` - Multiple package references
- `venv/lib/python3.12/site-packages/` - Python package references
- Documentation references in various markdown files

**Critical Implementation Files:**
- No direct implementation found in application code
- References mainly in documentation and dependencies

#### 1.2 AWS Polly (7 references)
**Key Files:**
- `VOICE_SYNTHESIS_WORKFLOW_GRAPH.md` - Planning document
- `VOICE_SYNTHESIS_STANDARDIZATION_PLAN.md` - Migration plan
- `admin-ui/CONDUCTOR_PHASE4_ROADMAP.md` - Mentions Amazon Polly as option

**Critical Implementation Files:**
- No direct AWS Polly implementation found
- Only mentioned as potential option in planning documents

#### 1.3 Resemble AI (93 references)
**Key Files:**
- `agent/app/services/natural_language_processor.py` - Main implementation
- `requirements/base.txt` - Package dependency
- `venv/lib/python3.12/site-packages/resemble/` - Installed package
- `VOICE_MIGRATION_SUMMARY.md` - Documents completed migration
- `test_elevenlabs_voice.py` - Test file mentioning migration

**Critical Implementation Files:**
- Already migrated to ElevenLabs (per git history and VOICE_MIGRATION_SUMMARY.md)
- Package still present in requirements but code updated

#### 1.4 Generic Voice Synthesis Patterns (286 references)
**Key Locations:**
- `agent/app/services/natural_language_processor.py` - `text_to_speech()` method
- `admin-ui/src/components/conductor/Voice/VoiceSynthesizer.tsx` - Frontend component
- `conductor_implementation_guide.md` - API documentation
- Various planning and architecture documents

### 2. Infrastructure References

#### 2.1 PostgreSQL Vector/PGVector (148 references)
**Key Files:**
- `infra/components/postgres_component.py` - Infrastructure setup
- `packages/phidata/src/cloudsql_pgvector.py` - PGVector implementation
- `requirements/base.txt` - pgvector==0.2.5 dependency
- Multiple agent configuration files using pgvector

**Status:** Currently in use, needs migration to Weaviate Cloud

#### 2.2 Pinecone (Found in infrastructure search)
**Key Files:**
- `shared/memory/pinecone_adapter.py` - Adapter implementation
- `core/env_config.py` - Environment variables (marked as deprecated)
- Various LlamaIndex integration files

**Status:** Marked as deprecated, needs removal

#### 2.3 Local Airbyte
**Key Files:**
- No direct "local Airbyte" references found
- Infrastructure appears to use cloud-based services

### 3. Current State Analysis

#### 3.1 Voice Synthesis
- **Primary Implementation**: ElevenLabs (already migrated)
- **Legacy References**: Resemble AI package still in requirements
- **Documentation**: Needs update to remove mentions of other providers

#### 3.2 Infrastructure
- **Vector Storage**: Using Weaviate 1.30 (primary) + PostgreSQL with pgvector (secondary)
- **Data Sync**: No local Airbyte found
- **Deprecated Services**: Pinecone references exist but marked deprecated

## Risk Assessment

### High Risk Items
1. **Resemble AI Package**: Still in requirements.txt despite code migration
2. **PGVector Usage**: Active use in multiple components
3. **Frontend Voice Synthesis**: Browser-based TTS as fallback

### Medium Risk Items
1. **Documentation Inconsistencies**: Multiple docs reference various voice providers
2. **Test Coverage**: Limited tests for voice synthesis
3. **Environment Variables**: Legacy provider keys may still be configured

### Low Risk Items
1. **Package Dependencies**: Third-party packages mentioning voice services
2. **Example Code**: References in documentation examples

## Migration Requirements

### Phase 1: Cleanup (Immediate)
- [ ] Remove `resemble==1.5.0` from requirements/base.txt
- [ ] Clean up legacy environment variables
- [ ] Update all documentation

### Phase 2: Infrastructure Migration (Week 1-2)
- [ ] Migrate pgvector data to Weaviate Cloud
- [ ] Update all pgvector references to Weaviate
- [ ] Remove Pinecone adapter code

### Phase 3: Standardization (Week 2-3)
- [ ] Implement ElevenLabs service wrapper
- [ ] Add comprehensive voice synthesis tests
- [ ] Update frontend components

### Phase 4: Documentation (Week 3-4)
- [ ] Update all API documentation
- [ ] Create migration guide for developers
- [ ] Update deployment documentation

## File Change Summary

### Files Requiring Modification
1. **requirements/base.txt** - Remove resemble package
2. **agent/app/services/natural_language_processor.py** - Verify ElevenLabs implementation
3. **admin-ui/src/components/conductor/Voice/VoiceSynthesizer.tsx** - Standardize on ElevenLabs
4. **Multiple documentation files** - Update to reflect ElevenLabs only

### Files for Deletion
1. **venv/lib/python3.12/site-packages/resemble/*** - Will be removed after package uninstall
2. **shared/memory/pinecone_adapter.py** - Deprecated service
3. **Legacy test files** - Any tests for removed services

### New Files Required
1. **core/services/elevenlabs_service.py** - Centralized ElevenLabs service
2. **tests/test_elevenlabs_service.py** - Comprehensive test suite
3. **docs/ELEVENLABS_INTEGRATION.md** - Developer guide

## Metrics

### Current State
- Total voice synthesis references: 504
- Infrastructure references to migrate: 148
- Files affected: ~50-60 files
- Estimated effort: 35 days (as per plan)

### Success Criteria
- Zero references to Google Cloud TTS, AWS Polly, Resemble AI
- All voice synthesis through ElevenLabs API
- All vector storage through Weaviate Cloud
- All data sync through Airbyte Cloud
- 100% test coverage for voice synthesis
- Updated documentation across all components

## Next Steps

1. **Immediate Actions**:
   - Create backup of current state
   - Set up feature flags for gradual rollout
   - Configure ElevenLabs API keys in all environments

2. **Phase 2 Preparation**:
   - Design ElevenLabs service architecture
   - Plan data migration strategy
   - Set up monitoring and alerting

3. **Communication**:
   - Notify team of upcoming changes
   - Schedule migration windows
   - Prepare rollback procedures

---

Generated: 2025-01-06
Audit Version: 1.0