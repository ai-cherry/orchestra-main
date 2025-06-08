# Performance-First Workspace Standards

## Core Philosophy: Fast, Powerful, Accurate AI Development

**Priority Order (Non-Negotiable):**
1. **Performance** - Every decision optimized for speed and efficiency
2. **Quality** - Maintainable, reliable, scalable code
3. **Stability** - Resilient systems that don't break
4. **Maintainability** - Code that other AI systems can understand and improve
5. **Security** - Reasonable protection without sacrificing performance
6. **Cost** - Efficient resource usage within performance constraints

---

## MCP Integration - MANDATORY FOR ALL DEVELOPMENT

### Always Use MCP Servers
- **NEVER** write standalone scripts without MCP integration
- **EVERY** development task must coordinate through MCP servers
- **AUTO-UPDATE** MCP servers during development
- **PERFORMANCE-MONITOR** all MCP interactions

### Required MCP Connections by Activity:
```yaml
development:
  - code_intelligence_mcp (AST analysis, optimization)
  - performance_mcp (profiling, benchmarking)
  - testing_mcp (automated test generation)

architecture:
  - infrastructure_mcp (deployment, scaling)
  - database_mcp (query optimization)
  - monitoring_mcp (observability design)

ui_design:
  - design_mcp (component optimization)
  - performance_mcp (bundle analysis)
  - analytics_mcp (UX metrics)

quality_control:
  - testing_mcp (comprehensive automation)
  - performance_mcp (regression detection)
  - monitoring_mcp (quality metrics)
```

---

## Anti-Pattern Prevention

### ❌ STRICTLY FORBIDDEN - One-Off Scripts
**Blocked Patterns:**
- `temp_*.py` / `temp_*.js` / `temp_*.ts`
- `quick_*.py` / `quick_*.js` / `quick_*.ts` 
- `test_script_*.py` / `test_script_*.js`
- `one_time_*.py` / `one_time_*.js`
- `fix_*.py` / `fix_*.js` / `fix_*.ts`
- `backup_*.py` / `backup_*.js`
- `script_*.py` / `script_*.js`

**Instead, Use:**
- Integrate functionality into existing modules
- Create proper CLI commands in `cli/` directory
- Add functions to appropriate service classes
- Use MCP servers for coordination
- Create reusable utilities in `utils/` directory

### ❌ FORBIDDEN - Trivial Documentation
**Blocked Documentation:**
- `README.md` (unless replacing existing)
- `CHANGELOG.md`
- `TODO.md` / `NOTES.md` / `IDEAS.md`
- `INSTALLATION.md` / `SETUP.md`
- `TROUBLESHOOTING.md`
- Any documentation not directly useful to AI coders

**Required Documentation:**
- `architecture_decisions.md` - Technical choices and rationale
- `performance_benchmarks.md` - Performance metrics and targets
- `mcp_integration_guide.md` - MCP server usage patterns
- `ai_coding_patterns.md` - Patterns for AI development
- Code-level docstrings with performance characteristics

---

## Performance-First Development Standards

### Code Quality Requirements
```python
# REQUIRED: Performance-oriented type hints
from typing import Protocol, TypedDict, Literal, Union
from collections.abc import AsyncIterator, Awaitable

class PerformantService(Protocol):
    async def process(self, data: InputData) -> ResultData: ...
    
# REQUIRED: Performance monitoring in all critical functions
import time
from functools import wraps

def performance_monitor(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        duration = time.perf_counter() - start
        # Log to performance_mcp
        return result
    return wrapper
```

### Database Interactions
```python
# REQUIRED: Async database operations
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession

# REQUIRED: Connection pooling and optimization
async def optimized_query(session: AsyncSession, query: str) -> list:
    # Always include performance monitoring
    # Always use proper indexing
    # Always limit result sets
    # Always use connection pooling
    pass
```

### API Development
```python
# REQUIRED: FastAPI with performance optimization
from fastapi import FastAPI, Depends
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

# REQUIRED: Response caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# REQUIRED: Performance monitoring
from prometheus_client import Counter, Histogram
```

---

## File Organization Standards

### Directory Structure - Performance Optimized
```
src/
├── api/                    # FastAPI high-performance APIs
├── core/                   # Core business logic with optimization
├── database/               # Async database operations
├── infrastructure/         # Infrastructure as code (Pulumi)
├── mcp_servers/           # MCP server implementations
├── performance/           # Performance monitoring and optimization
├── services/              # Service layer with async patterns
├── utils/                 # Reusable utilities (NO one-off scripts)
└── workflows/             # Automated workflow definitions

tests/
├── performance/           # Performance tests and benchmarks
├── integration/           # Integration tests with MCP
└── unit/                  # Unit tests with performance assertions

docs/                      # AI-coder focused documentation only
├── architecture_decisions.md
├── performance_benchmarks.md
├── mcp_integration_guide.md
└── ai_coding_patterns.md
```

### File Naming Conventions
```bash
# ✅ GOOD: Clear, performance-focused naming
user_service.py              # Service layer
user_repository_async.py     # Data access layer
performance_monitor.py       # Performance utilities
mcp_coordination.py          # MCP integration

# ❌ BAD: Vague or temporary naming
temp.py                      # Forbidden
quick_fix.py                 # Forbidden
utils.py                     # Too generic
helper.py                    # Too generic
```

---

## Continuous Performance Optimization

### Automated Performance Monitoring
```python
# REQUIRED: Performance assertions in tests
import pytest
import time

@pytest.mark.performance
async def test_api_response_time():
    start = time.perf_counter()
    response = await client.get("/api/users")
    duration = time.perf_counter() - start
    
    assert duration < 0.1  # 100ms max
    assert response.status_code == 200

# REQUIRED: Memory usage monitoring
import psutil
import pytest

@pytest.mark.memory
async def test_memory_usage():
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Execute operation
    await heavy_operation()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    assert memory_increase < 10 * 1024 * 1024  # 10MB max increase
```

### Performance Budgets
```yaml
performance_budgets:
  api_response_time: 100ms
  database_query_time: 50ms
  ui_bundle_size: 250KB
  memory_usage_increase: 10MB
  cpu_usage_max: 80%
  
quality_gates:
  test_coverage: 90%
  type_coverage: 95%
  performance_regression: 5%
  accessibility_score: 95%
```

---

## AI Coding Instruction Standards

### Ongoing Updates Required
All AI coding instructions must be:
- **Performance-focused** - Every instruction optimized for speed
- **MCP-integrated** - Always coordinate through MCP servers
- **Auto-updating** - Instructions evolve based on performance data
- **Context-aware** - Consider system-wide performance impact

### Patrick Instructions Integration
```python
# REQUIRED: Reference Patrick's patterns in all code
from patrick_patterns import (
    PerformanceOptimizedService,
    AsyncDatabasePattern,
    MCPCoordinationMixin
)

class UserService(PerformanceOptimizedService, MCPCoordinationMixin):
    """Implements Patrick's high-performance service pattern"""
    
    async def process_user(self, user_data: UserData) -> UserResult:
        # Always coordinate through MCP
        await self.coordinate_with_mcp('user_processing_start', user_data)
        
        # Apply Patrick's performance optimizations
        result = await self.optimized_process(user_data)
        
        # Performance monitoring as Patrick specified
        await self.log_performance_metrics(result)
        
        return result
```

### Notion Notes Integration
- **Auto-sync** with Notion for AI coding patterns
- **Performance metrics** automatically updated in Notion
- **MCP coordination logs** synced to Notion for analysis
- **Continuous improvement** based on Notion feedback

---

## Quality Gates - No Approval Required

### Automated Quality Checks
```yaml
automated_checks:
  performance_regression: FAIL_IF_SLOWER_THAN_5_PERCENT
  memory_leaks: FAIL_IF_DETECTED
  type_coverage: FAIL_IF_BELOW_95_PERCENT
  test_coverage: FAIL_IF_BELOW_90_PERCENT
  accessibility: FAIL_IF_BELOW_95_PERCENT
  bundle_size: FAIL_IF_ABOVE_250KB
  
auto_fixes:
  performance_optimization: ALWAYS_APPLY
  type_hint_generation: ALWAYS_APPLY
  accessibility_improvements: ALWAYS_APPLY
  security_updates: APPLY_IF_NO_PERFORMANCE_IMPACT
```

### Continuous Improvement Loop
1. **Performance Monitoring** - Real-time metrics collection
2. **Automated Analysis** - MCP-driven performance analysis
3. **Optimization Implementation** - Auto-apply improvements
4. **Validation** - Automated performance testing
5. **Documentation Update** - AI-coder focused docs only

---

## Emergency Override Protocols

### When Performance Degrades
```python
# AUTOMATIC: Performance degradation response
if performance_degradation_detected():
    # 1. Auto-rollback to previous performance baseline
    await auto_rollback_to_baseline()
    
    # 2. Coordinate through MCP for analysis
    await mcp_coordinate('performance_degradation_analysis')
    
    # 3. Auto-implement performance fixes
    await auto_apply_performance_fixes()
    
    # 4. Human notification (no approval required)
    await notify_human_summary_only()
```

### When MCP Servers Fail
```python
# AUTOMATIC: MCP failure response
if mcp_server_failure_detected():
    # 1. Auto-restart MCP servers
    await auto_restart_mcp_servers()
    
    # 2. Failover to backup MCP configuration
    await failover_to_backup_mcp()
    
    # 3. Continue development with degraded MCP
    await continue_with_essential_mcp_only()
```

---

## Success Metrics

### Development Velocity
- **Code commits per hour** - Maximize throughput
- **Feature completion time** - Minimize development cycles
- **Bug resolution time** - Rapid issue resolution
- **Performance optimization rate** - Continuous improvement

### Quality Metrics
- **Performance regression rate** - < 1% of deployments
- **System availability** - > 99.9% uptime
- **Response time consistency** - < 5% variance
- **Memory leak incidents** - Zero tolerance

### AI Coordination Efficiency
- **MCP server uptime** - > 99.9%
- **Cross-agent coordination success** - > 95%
- **Context sharing efficiency** - Minimize redundant work
- **Automated optimization rate** - Maximize auto-improvements

---

**REMEMBER: Fast, powerful, accurate AI development with human oversight through summaries, not interruption. Performance and quality above all else.** 