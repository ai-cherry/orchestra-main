# MCP Database Migration Status

## Current State (December 2024)

### ✅ COMPLETED: Database Consolidation
The Orchestra AI system has been migrated to use **ONLY**:
- **PostgreSQL** - For all relational/structured data
- **Weaviate** - For all vector/semantic search data

### ❌ DEPRECATED Databases
The following databases are NO LONGER USED:
- MongoDB
- Redis  
- DragonflyDB

### ⚠️ IMPORTANT: Legacy Code Warning
Many files in the codebase still contain references to the deprecated databases. These references should be **IGNORED**. All new development must use only PostgreSQL + Weaviate through the `UnifiedDatabase` class.

## MCP Server Status

### Active MCP Servers
1. **memory_server.py** - ✅ Uses PostgreSQL + Weaviate
2. **orchestrator_server.py** - ✅ Uses PostgreSQL  
3. **tools_server.py** - ✅ Database agnostic
4. **weaviate_direct_mcp_server.py** - ✅ Direct Weaviate access

### Legacy Servers (DO NOT USE)
- **dragonfly_server.py** - ❌ Uses deprecated DragonflyDB
- **mongodb_server.py** - ❌ Uses deprecated MongoDB
- Any other database-specific servers

## For AI Coding Agents

### 1. Always Use UnifiedDatabase
```python
from shared.database import UnifiedDatabase
db = UnifiedDatabase()
```

### 2. Never Import Deprecated Libraries
```python
# ❌ DO NOT USE:
import redis
import pymongo
import dragonfly
```

### 3. Reference Documentation
- Main guide: `MCP_INSTRUCTIONS_FOR_AI_AGENTS.md`
- Quick reference: `MCP_QUICK_REFERENCE.md`
- Usage examples: `MCP_USAGE_GUIDE_FOR_AI_CODERS.md`

## Migration Checklist
- [x] Create PostgreSQL schema
- [x] Create Weaviate collections
- [x] Implement UnifiedDatabase class
- [x] Update MCP servers to use new database layer
- [x] Create migration documentation
- [ ] Remove legacy database code (future task)
- [ ] Update all references in documentation (in progress)

## Known Issues
1. **check_mcp_servers.sh** only checks syntax, not runtime status
2. Legacy database references exist throughout codebase
3. Some documentation still mentions deprecated databases

## Next Steps
1. Continue using PostgreSQL + Weaviate for all new features
2. Gradually remove legacy database code
3. Update documentation to reflect current state
4. Create automated tests for database layer

---
*Last Updated: December 2024* 