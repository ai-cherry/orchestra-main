"""
AI CONTEXT: PLANNER MODE - Orchestra Project (GCP-Free Edition)
================================================================

READ THIS ENTIRE FILE BEFORE PLANNING ANY CHANGES!

Project: Orchestra AI (Python 3.10, pip/venv, External Services, Single-developer)
Role: You are planning a change or feature for this project.

CRITICAL RULES:
1. Python 3.10 ONLY (system constraint)
2. pip/venv for dependency management (NO Poetry, Docker, Pipenv)
3. External managed services for data storage:
   - MongoDB Atlas for persistent memory
   - DragonflyDB (Aiven) for caching
   - Weaviate Cloud for vector search
4. Local development with docker-compose (for services only, not app)
5. Simple > Complex, Performance > Security
6. DigitalOcean for deployment (via Pulumi Python)

TOOL AWARENESS FOR PLANNING:
Before planning new features, discover available tools:
1. List tool categories: list_tool_categories()
2. Search for relevant tools: search_tools("your feature")
3. Get tool details: get_tool_details("tool_name")
4. Check tool costs and constraints
5. Plan tool sequences for complex tasks

Current tool categories:
- cache: Fast data access (low cost)
- database: Persistent storage (medium cost)
- search: Semantic search (medium cost)
- system: Script execution (low cost)
- ai: LLM operations (high cost)

PLANNING CHECKLIST:
□ Does this functionality already exist in scripts/ or core modules?
□ Are there existing tools that can accomplish this?
□ Am I reusing existing patterns from the codebase?
□ Is this the simplest solution possible?
□ Does this avoid adding heavy dependencies?
□ Will this work with pip/venv workflow?
□ Does this align with external services architecture?

BEFORE PLANNING NEW FEATURES:
```bash
# Check what already exists
ls -la scripts/*.py
grep -r "def.*${FEATURE_KEYWORD}" scripts/
python scripts/orchestra.py services status
python scripts/orchestra_status.py

# Check available tools
python scripts/test_tool_system.py
cat docs/AVAILABLE_TOOLS.md
```

ARCHITECTURAL PRINCIPLES:
- All automation tools go in scripts/
- All configs in appropriate subdirectories
- Use subprocess.run() (never os.system())
- Type hints for all functions
- Google-style docstrings
- Black formatting
- External services over self-hosted
- Use existing tools over new implementations

FORBIDDEN IN YOUR PLAN:
❌ Poetry, Pipenv, or complex dependency management
❌ Docker for the application (only for local service mocks)
❌ Any GCP services or dependencies
❌ Python 3.11+ features (match/case, tomllib)
❌ Complex patterns (metaclasses, multiple inheritance)
❌ Heavy dependencies for simple tasks
❌ Reimplementing existing tools

GOOD PLANNING EXAMPLE:
"I need to add health metrics collection. First, I'll search for monitoring tools
with search_tools('monitor health metrics'). If none exist, I'll check
scripts/health_monitor.py and extend it. I'll ensure it works with our external
services (MongoDB, DragonflyDB) and uses only pip-installable dependencies."

EXTERNAL SERVICES TO CONSIDER:
- MongoDB Atlas: Document storage (agent memories)
- DragonflyDB: High-performance caching
- Weaviate: Vector search and embeddings
- OpenRouter/Anthropic: LLM providers
- DigitalOcean: Deployment infrastructure

REMEMBER:
- Check existing tools first
- Performance > Security (within reason)
- Stability > Features
- Existing patterns > New patterns
- Check scripts/ directory FIRST!
- All dependencies via pip/requirements files

# This file is meant to be read by AI when planning changes.
# Usage: Include this filename in your prompt when planning.
# Example: "Read ai_context_planner.py and help me plan a feature for X"
"""
