# 🤖 AI CODING INSTRUCTIONS - Orchestra AI Ecosystem
## Comprehensive Development Standards & AI Assistant Integration

### 📋 **UPDATED**: June 8, 2025 | **VERSION**: 4.0 - Complete AI Assistant Integration

---

## 🎯 **CORE DEVELOPMENT PRINCIPLES**

### **Project Philosophy:**
- **Single-developer project** prioritizing performance over security
- **AI-agent friendly** code and documentation
- **Modular, hot-swappable** architecture
- **PostgreSQL + Weaviate + Redis** stack (NO MongoDB)
- **Python 3.10 ONLY** (NOT 3.11+)
- **Type hints mandatory** for all functions

### **Stack Constraints:**
```yaml
Languages: Python 3.10, TypeScript, SQL
Databases: PostgreSQL (primary), Weaviate (vector), Redis (cache)
Infrastructure: Lambda Labs, Pulumi
UI Framework: React + TypeScript + Tailwind CSS
AI Models: OpenAI GPT-4O, DeepSeek R1, Claude Sonnet/Opus, Gemini
```

---

## 🔧 **TOOL-SPECIFIC INSTRUCTIONS**

### **🎯 Cursor IDE - Quick Development**
```python
# Use for:
# - Quick edits and bug fixes
# - Real-time coding with immediate feedback  
# - File-level operations
# - IDE-integrated development

# Standards enforced by .cursorrules:
# - Python 3.10 features only
# - Type hints mandatory
# - Google-style docstrings
# - Black + isort formatting
# - Performance-first approach
```

### **🤖 Roo Coder - Specialized Modes**
```bash
# Mode Selection:
roo code        # General coding (DeepSeek R1)
roo architect   # System design (Claude Sonnet 4)
roo orchestrator # Complex workflows (Claude Sonnet 4) 
roo debug       # Systematic debugging (DeepSeek R1)
roo research    # Documentation/research (Gemini 2.5 Pro)
roo quality     # Code review/testing (DeepSeek R1)
roo strategy    # Technical decisions (Claude Opus 4)

# Boomerang tasks for multi-step processes:
# - Database schema changes
# - Multi-file refactoring
# - Infrastructure deployment
# - Complex feature implementation
```

### **📱 Continue.dev - UI Development**
```typescript
// Custom Commands:
/ui         // Sophisticated React components (gpt-4o-2024-11-20)
/prototype  // Rapid MVP components (gpt-4o-mini)
/persona    // Cherry/Sophia/Karen specific UI (gpt-4o-2024-11-20)
/admin      // Admin interface components (gpt-4o-2024-11-20)
/mcp        // MCP integration optimization
/review     // Comprehensive code review

// UI Standards:
// - React + TypeScript + Tailwind CSS
// - Accessibility (ARIA labels, keyboard navigation)
// - Responsive design (mobile-first)
// - Persona-specific color schemes
```

---

## 🏗️ **ARCHITECTURE STANDARDS**

### **Code Organization:**
```
orchestra-main/
├── admin-interface/     # Admin UI (React/TypeScript)
├── production-api/      # Main API (FastAPI/Python)
├── legacy/             # Legacy components (migrate gradually)
├── .roo/               # Roo configuration and modes
├── .continue/          # Continue.dev configuration
└── src/                # Core application code
```

### **Database Design:**
```sql
-- PostgreSQL: Primary data storage
-- Use EXPLAIN ANALYZE for all new queries
-- Implement proper indexing
-- Type-safe queries with asyncpg

-- Weaviate: Vector operations and semantic search
-- Store all documentation and code for rapid retrieval
-- Use for AI context and knowledge management

-- Redis: Caching and session management
-- Cache frequently accessed data
-- Session storage for API
-- Rate limiting and performance optimization
```

### **API Standards:**
```python
# FastAPI with type hints
from typing import Dict, List, Optional
from pydantic import BaseModel

class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool
    data: Optional[Dict] = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None

# Async/await patterns for all I/O
async def get_data(user_id: int) -> APIResponse:
    """Get user data with proper error handling"""
    try:
        # Implementation
        pass
    except Exception as e:
        return APIResponse(success=False, errors=[str(e)])
```

---

## 🎨 **PERSONA-SPECIFIC DEVELOPMENT**

### **🍒 Cherry (Life Companion)**
```typescript
// Theme: Warm red accents (red-500)
// Focus: Personal wellness, ranch management, life organization
interface CherryComponent {
  theme: 'warm' | 'personal' | 'friendly';
  colorScheme: 'red-500';  // Primary accent
  dataTypes: 'health' | 'personal' | 'ranch';
}

// UI Patterns:
// - Friendly, approachable design
// - Personal dashboard layouts
// - Wellness tracking interfaces
// - Ranch management tools
```

### **💼 Sophia (Business Intelligence)**
```typescript
// Theme: Professional blue accents (blue-500)
// Focus: Financial analysis, business operations, data processing
interface SophiaComponent {
  theme: 'professional' | 'efficient' | 'data-driven';
  colorScheme: 'blue-500';  // Primary accent
  dataTypes: 'financial' | 'business' | 'analytics';
}

// UI Patterns:
// - Data tables and charts
// - Professional dashboards
// - Financial report layouts
// - Business metrics visualization
```

### **🏥 Karen (Healthcare)**
```typescript
// Theme: Clinical green accents (green-500)
// Focus: Healthcare operations, clinical research, medical data
interface KarenComponent {
  theme: 'clinical' | 'precise' | 'compliant';
  colorScheme: 'green-500';  // Primary accent
  dataTypes: 'medical' | 'research' | 'clinical';
}

// UI Patterns:
// - Clinical interface design
// - Medical data forms
// - Research data visualization
// - Compliance-focused layouts
```

---

## 🔌 **MCP INTEGRATION STANDARDS**

### **Server Usage:**
```python
# MCP Server Selection:
# enhanced-memory: PostgreSQL + Weaviate + Redis operations
# code-intelligence: AST analysis, complexity, code smells
# git-intelligence: Git history, blame analysis, hotspots
# infrastructure-manager: Lambda Labs deployment, scaling
# web-scraping: Research, content analysis, data gathering
# cherry-domain: Personal assistant, wellness, ranch
# sophia-payready: Financial analysis, business intelligence
# weaviate-direct: Vector operations, semantic search

# Integration Pattern:
async def mcp_operation(server: str, operation: str, params: Dict) -> Any:
    """Standard MCP operation pattern"""
    try:
        result = await mcp_client.call_tool(server, operation, params)
        return result
    except Exception as e:
        logger.error(f"MCP operation failed: {server}.{operation}: {e}")
        raise
```

### **Context Sharing:**
```python
# Cross-tool context via orchestra-unified MCP server
async def share_context(tool: str, context: Dict[str, Any]) -> bool:
    """Share context between Cursor, Roo, and Continue"""
    return await mcp_client.update_context(tool, context)

async def get_shared_context(requesting_tool: str) -> Dict[str, Any]:
    """Get shared context for optimal tool coordination"""
    return await mcp_client.get_shared_context(requesting_tool)
```

---

## 💻 **PYTHON CODING STANDARDS**

### **Mandatory Patterns:**
```python
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path
import logging

# Type hints for all functions
def process_data(
    input_data: List[Dict[str, Any]], 
    config: Optional[Dict[str, str]] = None
) -> Dict[str, Union[int, str]]:
    """Process input data according to configuration.
    
    Args:
        input_data: List of data dictionaries to process
        config: Optional configuration parameters
        
    Returns:
        Dictionary containing processing results
        
    Raises:
        ValueError: If input_data is empty
        ProcessingError: If processing fails
    """
    if not input_data:
        raise ValueError("Input data cannot be empty")
    
    try:
        # Implementation
        result = {"processed": len(input_data), "status": "success"}
        return result
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        raise ProcessingError(f"Failed to process data: {e}") from e

# Dataclasses for structured data
@dataclass
class UserProfile:
    """User profile data structure"""
    user_id: int
    name: str
    email: str
    preferences: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API serialization"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "preferences": self.preferences
        }
```

### **Error Handling:**
```python
# Specific exceptions, not generic Exception
class ProcessingError(Exception):
    """Raised when data processing fails"""
    pass

class APIConnectionError(Exception):
    """Raised when API connection fails"""
    pass

# Proper error handling with context
async def api_call(endpoint: str, data: Dict) -> Dict[str, Any]:
    """Make API call with proper error handling"""
    try:
        response = await http_client.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"API call failed: {e.response.status_code}")
        raise APIConnectionError(f"API returned {e.response.status_code}") from e
    except httpx.RequestError as e:
        logger.error(f"Request failed: {e}")
        raise APIConnectionError(f"Request failed: {e}") from e
```

---

## 🎨 **UI/FRONTEND STANDARDS**

### **React/TypeScript Components:**
```typescript
// Component structure with proper TypeScript
interface ComponentProps {
  data: UserData[];
  onUpdate: (id: string, data: Partial<UserData>) => void;
  className?: string;
  persona: 'cherry' | 'sophia' | 'karen';
}

export const DataTable: React.FC<ComponentProps> = ({
  data,
  onUpdate,
  className = '',
  persona
}) => {
  // Persona-specific styling
  const colorScheme = {
    cherry: 'border-red-500 text-red-600',
    sophia: 'border-blue-500 text-blue-600', 
    karen: 'border-green-500 text-green-600'
  }[persona];

  return (
    <div 
      className={`${colorScheme} ${className}`}
      role="table"
      aria-label="Data table"
    >
      {/* Implementation with accessibility */}
    </div>
  );
};
```

### **Tailwind CSS Standards:**
```css
/* Responsive design (mobile-first) */
.data-card {
  @apply 
    p-4 
    rounded-lg 
    shadow-sm 
    border 
    bg-white
    hover:shadow-md 
    transition-shadow
    /* Mobile first */
    w-full
    /* Tablet */
    md:w-1/2
    /* Desktop */
    lg:w-1/3;
}

/* Persona-specific themes */
.cherry-theme { @apply border-red-500 text-red-600; }
.sophia-theme { @apply border-blue-500 text-blue-600; }
.karen-theme { @apply border-green-500 text-green-600; }
```

---

## 📊 **PERFORMANCE STANDARDS**

### **Algorithm Complexity:**
```python
# Prefer O(n log n) or better algorithms
# Benchmark functions with loops > 1000 iterations

import time
from functools import wraps

def benchmark(func):
    """Decorator to benchmark function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__}: {(end - start) * 1000:.2f}ms")
        return result
    return wrapper

@benchmark
def process_large_dataset(data: List[Dict]) -> List[Dict]:
    """Process large dataset with O(n log n) complexity"""
    # Use efficient algorithms
    return sorted(data, key=lambda x: x['priority'])
```

### **Database Optimization:**
```sql
-- Use EXPLAIN ANALYZE for all new queries
EXPLAIN ANALYZE 
SELECT u.name, p.title 
FROM users u 
JOIN posts p ON u.id = p.user_id 
WHERE u.active = true 
ORDER BY p.created_at DESC;

-- Proper indexing
CREATE INDEX CONCURRENTLY idx_users_active ON users(active) WHERE active = true;
CREATE INDEX CONCURRENTLY idx_posts_user_created ON posts(user_id, created_at DESC);
```

---

## 🧪 **TESTING STANDARDS**

### **Unit Testing:**
```python
import pytest
from unittest.mock import AsyncMock, patch

class TestUserService:
    """Test user service functionality"""
    
    @pytest.mark.asyncio
    async def test_get_user_success(self):
        """Test successful user retrieval"""
        # Arrange
        user_id = 123
        expected_user = {"id": 123, "name": "Test User"}
        
        with patch('services.database.get_user') as mock_get:
            mock_get.return_value = expected_user
            
            # Act
            result = await user_service.get_user(user_id)
            
            # Assert
            assert result == expected_user
            mock_get.assert_called_once_with(user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self):
        """Test user not found scenario"""
        with patch('services.database.get_user') as mock_get:
            mock_get.return_value = None
            
            with pytest.raises(UserNotFoundError):
                await user_service.get_user(999)
```

---

## 🚀 **DEPLOYMENT STANDARDS**

### **Pulumi Infrastructure:**
```python
# Infrastructure as Code with Pulumi
import pulumi
from pulumi_lambda_labs import Instance

# Lambda Labs instance configuration
instance = Instance(
    "orchestra-api",
    instance_type="gpu_1x_a100_40gb",
    region="us-west-2",
    startup_script="""
    #!/bin/bash
    cd /home/ubuntu/orchestra-main
    ./deploy_production.sh
    """,
    tags={
        "Environment": "production",
        "Project": "orchestra-ai",
        "ManagedBy": "pulumi"
    }
)

# Export important values
pulumi.export("instance_ip", instance.public_ip)
pulumi.export("ssh_command", pulumi.Output.concat("ssh ubuntu@", instance.public_ip))
```

---

## 📝 **DOCUMENTATION STANDARDS**

### **AI-Optimized Documentation:**
```python
def calculate_user_score(
    interactions: List[UserInteraction],
    weights: Dict[str, float],
    time_decay: float = 0.95
) -> float:
    """Calculate weighted user engagement score with time decay.
    
    This function computes a user engagement score based on their interactions,
    applying configurable weights to different interaction types and a time
    decay factor to prioritize recent activity.
    
    Args:
        interactions: List of user interactions, must be sorted by timestamp
        weights: Dictionary mapping interaction types to weight values
                Example: {"view": 1.0, "like": 2.0, "share": 3.0}
        time_decay: Decay factor applied to older interactions (0.0-1.0)
                   Higher values decay less, default 0.95
    
    Returns:
        Calculated engagement score as float, range 0.0 to unbounded
        
    Raises:
        ValueError: If interactions list is empty or weights are invalid
        
    Example:
        >>> interactions = [
        ...     UserInteraction(type="view", timestamp=datetime.now()),
        ...     UserInteraction(type="like", timestamp=datetime.now() - timedelta(days=1))
        ... ]
        >>> weights = {"view": 1.0, "like": 2.0}
        >>> score = calculate_user_score(interactions, weights)
        >>> print(f"User score: {score:.2f}")
        User score: 2.95
    """
    if not interactions:
        raise ValueError("Interactions list cannot be empty")
        
    # Implementation details...
```

---

## 🔗 **INTEGRATION PATTERNS**

### **MCP + API Integration:**
```python
class OrchestralService:
    """Service integrating MCP servers with API endpoints"""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client
        
    async def enhanced_search(
        self, 
        query: str, 
        persona: str = "general"
    ) -> Dict[str, Any]:
        """Enhanced search using multiple MCP servers"""
        
        # Use enhanced-memory for semantic search
        semantic_results = await self.mcp.call_tool(
            "enhanced-memory",
            "search_memories_cached",
            {"query": query, "limit": 10}
        )
        
        # Use weaviate-direct for vector operations
        vector_results = await self.mcp.call_tool(
            "weaviate-direct", 
            "hybrid_search",
            {"query": query, "persona": persona}
        )
        
        # Combine and rank results
        return {
            "semantic": semantic_results,
            "vector": vector_results,
            "combined_score": self._calculate_relevance(
                semantic_results, vector_results
            )
        }
```

---

## 📋 **QUALITY CHECKLIST**

### **Before Code Commit:**
- [ ] **Type hints** on all functions and methods
- [ ] **Google-style docstrings** with examples
- [ ] **Error handling** with specific exceptions
- [ ] **Unit tests** with >80% coverage
- [ ] **Performance analysis** for loops >1000 iterations
- [ ] **EXPLAIN ANALYZE** for new database queries
- [ ] **Accessibility** compliance (ARIA labels, keyboard navigation)
- [ ] **Responsive design** testing (mobile, tablet, desktop)
- [ ] **Persona-specific** styling and UX patterns
- [ ] **MCP integration** where applicable
- [ ] **Logging** for important operations
- [ ] **Security** review for API endpoints

### **Before Deployment:**
- [ ] **Environment variables** properly configured
- [ ] **Database migrations** tested
- [ ] **API endpoints** tested with proper error scenarios
- [ ] **Infrastructure** provisioned via Pulumi
- [ ] **MCP servers** running and accessible
- [ ] **Performance benchmarks** meet requirements
- [ ] **Backup procedures** verified
- [ ] **Monitoring** and alerting configured

---

## 🎯 **SUCCESS METRICS**

### **Development Velocity:**
- **Code generation**: 3-5x faster with AI assistants
- **Bug resolution**: <2 hours average with roo debug
- **UI development**: 10x faster with Continue.dev UI-GPT-4O
- **Architecture decisions**: Documented and rationale-backed

### **Code Quality:**
- **Type coverage**: >95% for all Python code
- **Test coverage**: >80% for all modules
- **Performance**: All queries <100ms, API endpoints <500ms
- **Accessibility**: WCAG 2.1 AA compliance
- **Documentation**: All public APIs documented with examples

---

## 🔧 **TOOLING COMMANDS**

### **Daily Development:**
```bash
# Verify all configurations
python setup_api_keys.py --verify

# Test all systems
python test_coding_assistant_setup.py

# Start MCP servers (when needed)
./start_mcp_system_enhanced.sh

# Format and lint code
black . && isort . && flake8

# Run tests
pytest tests/ -v --cov=src/

# Database query analysis
psql -c "EXPLAIN ANALYZE SELECT ..."
```

---

## 🎉 **READY FOR DEVELOPMENT**

**✅ All systems operational for maximum AI-assisted development velocity!**

- **Coding Standards**: Enforced across all tools
- **AI Integration**: Seamless context sharing
- **Performance**: Optimized for single-developer workflow  
- **Quality**: Comprehensive testing and review processes
- **Documentation**: AI-optimized for maximum efficiency

**🚀 Build the future with AI-accelerated development!** 