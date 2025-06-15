# 🎼 Orchestra AI - Cursor Agent Rules & Guidelines

## 🎯 Project Overview

Orchestra AI is an enterprise-grade AI orchestration platform with a PostgreSQL-Redis-Vector Database architecture, deployed via Pulumi infrastructure-as-code, and scaled with Lambda Labs GPU clusters. The platform emphasizes modular MCP (Model Context Protocol) servers, data integration via Airbyte, and professional-grade UI/UX.

## 🏗️ Architecture & Structure

### **Core Components**
```yaml
api/:                     # FastAPI backend
  main.py                 # Main application entry
  main_simple.py          # Simplified API for development
  database/               # Database connections and models
  services/               # Business logic services
  
web/:                     # React frontend
  src/
    components/           # UI components
    pages/               # Page components
    contexts/            # React contexts
    lib/                 # Utilities
    
shared/:                  # Shared utilities between frontend/backend
mcp_servers/             # MCP server implementations
lambda_infrastructure/   # Lambda Labs GPU integration
```

### **Development Workflow**
- **Main Branch**: Production-ready code only
- **Feature Branches**: `feature/descriptive-name`
- **Environment Layers**: Local → Integration → Staging → Production
- **Safety Protocols**: Comprehensive validation and rollback procedures

## 🎯 Cursor Agent Behavior Guidelines

### **1. Code Generation Standards**

#### **Backend (FastAPI)**
- Always use **async/await** patterns for database operations
- Follow **SQLAlchemy 2.0+ syntax** with async engines
- Use **Pydantic v2** for data validation and serialization
- Implement **proper error handling** with structured logging
- Include **type hints** for all function parameters and returns

```python
# Preferred Pattern
async def create_file(
    file_data: FileCreateSchema,
    db: AsyncSession = Depends(get_db)
) -> FileResponse:
    try:
        # Implementation with proper error handling
        pass
    except Exception as e:
        logger.error(f"Failed to create file: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### **Frontend (React + TypeScript)**
- Use **functional components** with hooks
- Implement **proper TypeScript types** for all props and state
- Use **@ import aliases** configured in tsconfig.json
- Follow **Tailwind CSS utility-first** approach
- Implement **proper error boundaries** and loading states

```typescript
// Preferred Pattern
interface ComponentProps {
  data: DataType;
  onUpdate: (data: DataType) => Promise<void>;
}

export const Component: React.FC<ComponentProps> = ({ data, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  // Implementation
};
```

### **2. File Organization Rules**

#### **When Creating New Files**
- **API Routes**: Place in `api/routes/` with proper grouping
- **Database Models**: Place in `api/database/models/`
- **Services**: Place in `api/services/` with single responsibility
- **React Components**: Place in `web/src/components/` with proper nesting
- **Types**: Place in `shared/types/` for cross-platform types

#### **Import Conventions**
```python
# Backend Imports (order matters)
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database.connection import get_db
from services.file_service import FileService
from shared.types import FileType
```

```typescript
// Frontend Imports (order matters)
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import type { FileType } from '@/shared/types';
```

### **3. Environment-Specific Behavior**

#### **Development Environment**
- Use **SQLite** for local development by default
- Enable **debug logging** and **hot reload**
- Use **simplified authentication** for development
- Implement **mock services** for external dependencies

#### **Production Environment**
- Use **PostgreSQL** with connection pooling
- Enable **structured logging** with proper levels
- Implement **proper authentication** and security
- Use **real external services** with proper error handling

### **4. MCP Server Integration Rules**

#### **When Working with MCP Servers**
- Follow the **MCP protocol specification**
- Use **port allocation strategy**: 8003-8009 for MCP servers
- Implement **proper health checks** for all MCP services
- Use **async patterns** for inter-service communication

```python
# MCP Server Pattern
class MCPServer:
    def __init__(self, port: int, name: str):
        self.port = port
        self.name = name
        self.health_endpoint = f"http://localhost:{port}/health"
    
    async def health_check(self) -> bool:
        # Implementation
        pass
```

### **5. Error Handling & Logging**

#### **Always Implement**
- **Structured logging** with context information
- **Proper exception handling** with user-friendly messages
- **Graceful degradation** for optional features
- **Detailed error responses** for development, sanitized for production

```python
# Logging Pattern
import structlog
logger = structlog.get_logger(__name__)

async def process_file(file_id: str):
    logger.info("Processing file", file_id=file_id)
    try:
        # Processing logic
        logger.info("File processed successfully", file_id=file_id)
    except Exception as e:
        logger.error("File processing failed", file_id=file_id, error=str(e))
        raise
```

### **6. Database Patterns**

#### **SQLAlchemy Async Patterns**
```python
# Model Definition
class FileModel(Base):
    __tablename__ = "files"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

# Service Pattern
async def get_file(db: AsyncSession, file_id: UUID) -> FileModel:
    stmt = select(FileModel).where(FileModel.id == file_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

### **7. Testing Requirements**

#### **Always Include Tests For**
- **API endpoints** with proper status codes
- **Database operations** with rollback
- **Service layer logic** with mocking
- **Frontend components** with user interactions

### **8. Security Considerations**

#### **Always Implement**
- **Input validation** with Pydantic schemas
- **SQL injection prevention** with parameterized queries
- **XSS prevention** with proper escaping
- **Authentication checks** for protected endpoints
- **Rate limiting** for public endpoints

### **9. Performance Guidelines**

#### **Backend Optimization**
- Use **database connection pooling**
- Implement **caching** for frequently accessed data
- Use **async operations** for I/O bound tasks
- Implement **pagination** for large datasets

#### **Frontend Optimization**
- Use **React.memo** for expensive components
- Implement **code splitting** for large bundles
- Use **lazy loading** for images and components
- Optimize **bundle size** with tree shaking

### **10. Documentation Standards**

#### **Always Include**
- **Docstrings** for all functions and classes
- **Type annotations** for all parameters
- **Usage examples** in docstrings
- **API documentation** with OpenAPI specs

```python
async def process_file(
    file_id: UUID,
    processing_options: ProcessingOptions,
    db: AsyncSession
) -> ProcessedFileResult:
    """
    Process a file with the specified options.
    
    Args:
        file_id: Unique identifier for the file to process
        processing_options: Configuration for file processing
        db: Database session for data operations
        
    Returns:
        ProcessedFileResult containing processing status and metadata
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ProcessingError: If processing fails
        
    Example:
        >>> result = await process_file(
        ...     file_id=UUID("..."),
        ...     processing_options=ProcessingOptions(format="pdf"),
        ...     db=session
        ... )
    """
```

## 🚨 Critical Rules

### **Never Do**
1. **Never commit directly to main branch**
2. **Never ignore TypeScript errors**
3. **Never use `any` type without justification**
4. **Never skip error handling in async operations**
5. **Never hardcode credentials or API keys**
6. **Never modify node_modules or __pycache__ files**
7. **Never use synchronous database operations in async contexts**

### **Always Do**
1. **Always run validation scripts before committing**
2. **Always use the virtual environment for Python**
3. **Always implement proper loading states in UI**
4. **Always use absolute imports with @ aliases**
5. **Always follow the branch naming convention**
6. **Always include proper error boundaries**
7. **Always validate user input on both client and server**

## 🎯 Context-Aware Assistance

### **When Asked About**
- **"How to add a new API endpoint"**: Provide FastAPI pattern with proper validation
- **"How to create a new React component"**: Provide TypeScript component with proper types
- **"How to connect to database"**: Use async SQLAlchemy pattern
- **"How to add MCP server"**: Follow port allocation and health check patterns
- **"How to deploy"**: Reference deployment scripts and safety procedures

### **File-Specific Context**
- **In `api/` directory**: Focus on FastAPI, async patterns, database operations
- **In `web/` directory**: Focus on React, TypeScript, UI components
- **In `shared/` directory**: Focus on cross-platform utilities and types
- **Working with MCP**: Focus on protocol compliance and service communication

## 🔧 Tooling Integration

### **Development Tools**
- **Environment Validation**: Use `validate_environment.py`
- **Service Management**: Use `start_orchestra.sh` and `stop_all_services.sh`
- **Deployment**: Use `deploy_to_production.sh`
- **Branch Management**: Follow feature branch workflow

### **Quality Gates**
- **Code Formatting**: Follow project conventions
- **Type Checking**: Ensure TypeScript and Python types are correct
- **Testing**: Run relevant tests for changed code
- **Documentation**: Update documentation for API changes

This configuration ensures the Cursor agent provides contextually appropriate assistance while maintaining Orchestra AI's architectural patterns and development standards. 

## 🏗️ Core Technology Stack

### **Primary Database Layer**
- **PostgreSQL** (Primary RDBMS): 45.77.87.106:5432 - Structured data, transactions, ACID compliance
- **Redis** (Cache/Session): 45.77.87.106:6379 - Fast caching, real-time data, session management
- **Pinecone** (Vector DB): Semantic embeddings, similarity search, AI model vectors
- **Weaviate** (Vector DB): Knowledge graphs, contextual AI, schema-based vectors

### **Infrastructure & Deployment**
- **Pulumi** (Infrastructure as Code): Python-based IaC, no Terraform
- **Lambda Labs** (GPU Compute): High-performance AI model training and inference
- **Airbyte** (Data Integration): ETL/ELT pipelines, data source synchronization
- **Docker**: Containerization for all services
- **Kubernetes**: Container orchestration (via Pulumi)

### **Application Stack**
- **Backend**: FastAPI (Python 3.11+), asyncio, Pydantic, SQLAlchemy (async)
- **Frontend**: React 18+, TypeScript, Vite, Tailwind CSS, shadcn/ui
- **MCP Servers**: 5-server ecosystem (Memory, Task, Agent, Data, Monitoring)
- **API Gateway**: FastAPI with OpenAPI documentation

## 📋 Database-Centric Development Rules

### **PostgreSQL Standards**
```python
# Always use async SQLAlchemy with connection pooling
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Connection string format
DATABASE_URL = "postgresql+asyncpg://user:password@host:port/database"

# Table naming: snake_case with descriptive prefixes
class UserAccount(Base):
    __tablename__ = "user_accounts"
    
class SystemAuditLog(Base):
    __tablename__ = "system_audit_logs"

# Always include standard audit fields
created_at = Column(DateTime(timezone=True), server_default=func.now())
updated_at = Column(DateTime(timezone=True), onupdate=func.now())
version = Column(Integer, default=1)
```

### **Redis Integration Rules**
```python
# Use redis.asyncio for async operations
import redis.asyncio as redis

# Key naming convention: service:entity:id
cache_key = f"orchestra:user_session:{user_id}"
memory_key = f"mcp:memory:{memory_type}:{session_id}"

# Always set expiration for cache entries
await redis_client.setex(key, ttl_seconds, value)

# Use Redis for:
# - Session management
# - Real-time data caching
# - MCP server state
# - API rate limiting
# - Background job queues
```

### **Vector Database Standards**
```python
# Pinecone for semantic search
pinecone.init(api_key=api_key, environment=environment)
index = pinecone.Index("orchestra-embeddings")

# Weaviate for knowledge graphs
import weaviate
client = weaviate.Client(url="http://weaviate-host:8080")

# Consistent embedding dimensions (1536 for OpenAI)
EMBEDDING_DIMENSION = 1536
```

## 🚀 Pulumi Infrastructure Rules

### **Python-First Infrastructure**
```python
# Always use Python Pulumi (never Terraform)
import pulumi
import pulumi_aws as aws
import pulumi_kubernetes as k8s

# Resource naming: environment-service-purpose
resource_name = f"{environment}-orchestra-{service_type}"

# Tags for all resources
standard_tags = {
    "Project": "Orchestra-AI",
    "Environment": environment,
    "ManagedBy": "Pulumi",
    "CostCenter": "AI-Platform"
}
```

### **Environment Strategy**
- **Development**: Local services + SQLite fallback
- **Staging**: Full stack on 45.77.87.106 servers
- **Production**: Kubernetes + Lambda Labs GPU clusters
- **Infrastructure**: Pulumi stacks for each environment

## 🤖 MCP Server Architecture Rules

### **5-Server Ecosystem**
1. **Memory Management** (Port 8003): PostgreSQL + Redis + Weaviate
2. **Task Orchestration** (Port 8006): PostgreSQL + Redis scheduling
3. **Agent Coordination** (Port 8007): Multi-agent communication
4. **Data Integration** (Port 8008): Airbyte + database connectors
5. **System Monitoring** (Port 8009): Metrics + logging + alerting

### **MCP Server Standards**
```python
# All MCP servers must implement:
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "service-name",
        "port": SERVER_PORT,
        "environment": CONFIG["environment"],
        "timestamp": datetime.now().isoformat(),
        "connections": {
            "postgres": bool(db_connection),
            "redis": bool(redis_connection),
            "vector_db": bool(vector_connection)
        }
    }

# Structured logging with contextual data
import structlog
logger = structlog.get_logger(__name__)
logger.info("Operation completed", 
           user_id=user_id, 
           operation="data_sync", 
           duration_ms=duration)
```

## 💻 Frontend UI/UX Rules

### **Design System Consistency**
```typescript
// Orchestra AI color palette
const colors = {
  primary: '#2563eb',        // Orchestra Blue
  secondary: '#7c3aed',      // Purple
  accent: '#059669',         // Emerald
  gray: {
    50: '#f9fafb',
    900: '#111827'
  }
}

// Component naming: PascalCase with descriptive names
<DataIntegrationPanel />
<AIAgentCard />
<SystemMetricsDashboard />
```

### **Responsive & Accessible Standards**
- Mobile-first responsive design
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode support

## 🔧 Development Environment Rules

### **Local Development Setup**
```bash
# Virtual environment for Python dependencies
python3 -m venv venv
source venv/bin/activate

# Required for all Orchestra AI services
pip install fastapi uvicorn sqlalchemy asyncpg redis structlog pydantic

# Frontend development
cd web && npm install
npm run dev  # Vite dev server

# MCP server development
cd mcp_servers && python {server_name}.py
```

### **Code Quality Standards**
- **Python**: Black formatting, isort imports, mypy typing, pytest testing
- **TypeScript**: ESLint + Prettier, strict typing, Jest testing
- **Documentation**: Comprehensive docstrings, API documentation, README files

## 📊 Data Integration Standards

### **Airbyte Configuration**
```yaml
# All data sources through Airbyte
sources:
  - name: postgres-primary
    connector: source-postgres
    destination: data-warehouse
  
  - name: vector-embeddings
    connector: source-pinecone
    destination: analytics-db

# Sync schedules: Every 15 minutes for real-time data
sync_schedule: "*/15 * * * *"
```

### **Data Pipeline Rules**
- Extract → Transform → Load via Airbyte
- Data validation at every pipeline stage
- Comprehensive error handling and retry logic
- Monitoring and alerting for pipeline failures
- Data lineage tracking for compliance

## 🏷️ Naming Conventions

### **File & Directory Structure**
```
orchestra-dev/
├── api/                    # FastAPI backend
├── web/                    # React frontend
├── mcp_servers/           # MCP server implementations
├── pulumi/                # Infrastructure as code
├── data/                  # Data processing scripts
├── .cursor/               # Cursor AI configuration
│   ├── agents/           # Specialized AI agents
│   └── rules.md          # This file
```

### **Database Naming**
- **Tables**: `snake_case` with descriptive prefixes
- **Columns**: `snake_case`, avoid abbreviations
- **Indexes**: `idx_{table}_{column}_{type}`
- **Foreign Keys**: `fk_{table}_{reference}`

### **API Naming**
- **Endpoints**: RESTful with clear resource naming
- **Models**: PascalCase for Pydantic models
- **Functions**: `snake_case` with verb_noun pattern

## 🔒 Security & Configuration

### **Environment Variables**
```bash
# Database connections
POSTGRES_HOST=45.77.87.106
POSTGRES_PORT=5432
POSTGRES_DB=orchestra_ai
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password

REDIS_HOST=45.77.87.106
REDIS_PORT=6379

# Vector databases
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=production
WEAVIATE_HOST=45.77.87.106
WEAVIATE_PORT=8080

# Lambda Labs
LAMBDA_LABS_API_KEY=your_lambda_key
LAMBDA_LABS_SSH_KEY=path_to_ssh_key
```

### **Security Standards**
- All API endpoints require authentication
- Rate limiting on all public endpoints
- Input validation and sanitization
- SQL injection prevention
- XSS protection on frontend
- HTTPS only in production

## 🧪 Testing Standards

### **Backend Testing**
```python
# pytest with async support
@pytest.mark.asyncio
async def test_user_creation():
    # Test with real database connections
    # Mock external services appropriately
    pass

# Integration tests for MCP servers
def test_mcp_server_health():
    response = requests.get("http://localhost:8003/health")
    assert response.status_code == 200
```

### **Frontend Testing**
```typescript
// Jest + React Testing Library
describe('DataIntegrationPanel', () => {
  it('should render data sources correctly', () => {
    render(<DataIntegrationPanel />);
    expect(screen.getByText('Data Sources')).toBeInTheDocument();
  });
});

// E2E testing with Playwright
test('complete user workflow', async ({ page }) => {
  await page.goto('http://localhost:3000');
  // Test complete user journeys
});
```

## 🚀 Deployment Rules

### **Pulumi Deployment**
```python
# Environment-specific stacks
pulumi stack select development
pulumi stack select staging  
pulumi stack select production

# Always use infrastructure as code
# No manual cloud console changes
# All resources tagged and documented
```

### **Lambda Labs Integration**
- GPU instances for AI model training
- Automated scaling based on workload
- Cost optimization through scheduling
- Monitoring GPU utilization

## 📈 Monitoring & Observability

### **Logging Standards**
```python
# Structured logging throughout
logger.info("Database operation completed",
           table="user_accounts",
           operation="insert",
           duration_ms=234,
           user_id="user_123")
```

### **Metrics Collection**
- Application performance metrics
- Database connection pooling stats
- Redis cache hit rates
- Vector database query latency
- MCP server health metrics

## 🎯 Performance Optimization

### **Database Performance**
- Connection pooling for all database connections
- Proper indexing strategy
- Query optimization and monitoring
- Read replicas for analytics workloads

### **Caching Strategy**
- Redis for session and application cache
- CDN for static assets
- Database query result caching
- Vector embedding caching

## 📝 Documentation Requirements

### **Code Documentation**
- Comprehensive docstrings for all functions
- Type hints for all Python code
- API documentation via OpenAPI/Swagger
- Architecture decision records (ADRs)

### **User Documentation**
- Setup and installation guides
- API reference documentation
- User interface tutorials
- Troubleshooting guides

## 🎼 Orchestra AI Specific Rules

### **Brand Consistency**
- Use 🎼 emoji for Orchestra AI branding
- Professional, enterprise-grade aesthetic
- Consistent color scheme across all interfaces
- Musical metaphors in UI copy (conductor, orchestration, harmony)

### **AI-First Development**
- All features designed with AI enhancement in mind
- Progressive disclosure for complex AI features
- Clear indication of AI-generated content
- Fallback mechanisms for AI service failures

## ⚡ Quick Reference Commands

```bash
# Start all services
./start_orchestra.sh

# Individual service management
./start_api.sh                    # FastAPI backend
./start_frontend.sh               # React frontend
./start_mcp_memory_server.sh      # Memory Management MCP

# Development utilities
./validate_environment.py         # Environment validation
./sync_environments.sh            # Environment synchronization
python -m pytest                  # Run test suite
```

## 🔄 Continuous Integration

### **Pre-commit Hooks**
- Code formatting (Black, Prettier)
- Linting (pylint, ESLint)
- Type checking (mypy, TypeScript)
- Security scanning
- Test execution

### **Automated Deployment**
- GitHub Actions for CI/CD
- Pulumi for infrastructure deployment
- Docker image building and pushing
- Environment promotion workflows

---

**Remember**: Orchestra AI is a PostgreSQL-Redis-Vector database system with Pulumi infrastructure, focusing on enterprise-grade AI orchestration. Every decision should prioritize scalability, maintainability, and professional user experience. 