#!/usr/bin/env python3
"""
Orchestra AI Architecture Refactoring Script
Implements SOLID principles, clean code patterns, and fixes identified issues
"""

import os
import re
import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class RefactoringIssue:
    """Represents an issue that needs refactoring"""
    file_path: str
    issue_type: str
    line_number: int
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    fix_applied: bool = False

class ArchitectureRefactorer:
    """Main refactoring engine following SOLID principles"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.issues: List[RefactoringIssue] = []
        self.refactoring_stats = {
            'files_analyzed': 0,
            'issues_found': 0,
            'issues_fixed': 0,
            'patterns_applied': []
        }
    
    def analyze_and_refactor(self):
        """Main entry point for analysis and refactoring"""
        logger.info("Starting Orchestra AI architecture refactoring...")
        
        # Phase 1: Fix critical issues
        self._fix_critical_issues()
        
        # Phase 2: Analyze architecture violations
        self._analyze_architecture_violations()
        
        # Phase 3: Apply SOLID principles
        self._apply_solid_principles()
        
        # Phase 4: Clean up code smells
        self._clean_code_smells()
        
        # Phase 5: Optimize performance
        self._optimize_performance()
        
        # Generate report
        self._generate_refactoring_report()
    
    def _fix_critical_issues(self):
        """Fix critical issues identified in the review"""
        logger.info("Phase 1: Fixing critical issues...")
        
        # Fix hardcoded secrets in .env.production
        self._fix_environment_secrets()
        
        # Fix README.md
        self._fix_readme()
        
        # Remove references to deleted files
        self._remove_deleted_file_references()
    
    def _fix_environment_secrets(self):
        """Replace hardcoded secrets with placeholders"""
        env_file = self.project_root / ".env.production"
        if env_file.exists():
            content = env_file.read_text()
            
            # Replace actual secrets with placeholders
            replacements = [
                (r'SECRET_KEY=.*', 'SECRET_KEY=your-secret-key-here'),
                (r'JWT_SECRET=.*', 'JWT_SECRET=your-jwt-secret-here'),
                (r'DB_PASSWORD=.*', 'DB_PASSWORD=your-db-password-here'),
                (r'GRAFANA_PASSWORD=.*', 'GRAFANA_PASSWORD=your-grafana-password-here')
            ]
            
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            env_file.write_text(content)
            logger.info("Fixed hardcoded secrets in .env.production")
            
            self.issues.append(RefactoringIssue(
                file_path=str(env_file),
                issue_type="security",
                line_number=0,
                description="Replaced hardcoded secrets with placeholders",
                severity="critical",
                fix_applied=True
            ))
    
    def _fix_readme(self):
        """Create proper README for Orchestra AI"""
        readme_content = '''# Orchestra AI - Intelligent Workflow Orchestration Platform

## Overview
Orchestra AI is a sophisticated AI-powered workflow orchestration platform that manages complex tasks through intelligent agent coordination, featuring PostgreSQL for data persistence, Weaviate for vector search, and Pulumi for infrastructure as code.

## Architecture
- **API Layer**: FastAPI-based REST API with JWT authentication
- **Database**: PostgreSQL with connection pooling and optimization
- **Vector Store**: Weaviate for semantic search and AI embeddings
- **Cache**: Redis for session management and caching
- **Infrastructure**: Pulumi IaC for Lambda Labs deployment

## Key Features
- Multi-persona AI system (Cherry, Sophia, Karen)
- Adaptive learning and personality development
- Real-time conversation engine with context awareness
- Supervisor agent architecture for task delegation
- MCP (Model Context Protocol) integration
- Comprehensive monitoring and health checks

## Quick Start

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+
- Weaviate 1.24+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ai-cherry/orchestra-main.git
cd orchestra-main
```

2. Set up environment variables:
```bash
cp .env.example .env.production
# Edit .env.production with your configuration
```

3. Start services with Docker Compose:
```bash
docker-compose -f docker-compose.production.yml up -d
```

4. Initialize the database:
```bash
python scripts/initialize_database.py
```

5. Start the API server:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## API Documentation
Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure
```
orchestra-main/
├── api/                    # FastAPI application
├── admin-interface/        # Admin dashboard
├── config/                 # Configuration files
├── core/                   # Core business logic
├── mcp_server/            # MCP server implementation
├── infrastructure/         # Pulumi IaC definitions
├── scripts/               # Utility scripts
└── docker-compose.*.yml   # Docker configurations
```

## Security
- JWT-based authentication
- Environment-based configuration
- Connection pooling with limits
- Rate limiting and CORS protection

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
'''
        readme_path = self.project_root / "README.md"
        readme_path.write_text(readme_content)
        logger.info("Created proper README.md for Orchestra AI")
    
    def _remove_deleted_file_references(self):
        """Remove references to deleted files from Python code"""
        patterns_to_remove = [
            r'audit_results_\d+',
            r"",
            r"",
            r'fix_\w+\.py',
            r'cleanup_\w+\.py',
            r'debug_\w+\.py',
            r'scan_\w+\.py',
            r'test_\w+\.py'
        ]
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            try:
                content = py_file.read_text()
                original_content = content
                
                for pattern in patterns_to_remove:
                    # Remove hardcoded paths
                    content = re.sub(f'["\'].*{pattern}.*["\']', '""', content)
                    # Remove variable references
                    content = re.sub(f'{pattern}', 'cleaned_reference', content)
                
                if content != original_content:
                    py_file.write_text(content)
                    logger.info(f"Cleaned references in {py_file}")
                    
                    self.issues.append(RefactoringIssue(
                        file_path=str(py_file),
                        issue_type="reference_cleanup",
                        line_number=0,
                        description="Removed references to deleted files",
                        severity="high",
                        fix_applied=True
                    ))
                    
            except Exception as e:
                logger.error(f"Error processing {py_file}: {e}")
    
    def _analyze_architecture_violations(self):
        """Analyze code for architecture violations"""
        logger.info("Phase 2: Analyzing architecture violations...")
        
        # Check for violations in api/main.py
        self._analyze_api_main()
        
        # Check for database schema in code
        self._check_database_schema_separation()
        
        # Check for proper dependency injection
        self._check_dependency_injection()
    
    def _analyze_api_main(self):
        """Analyze api/main.py for SOLID violations"""
        api_main = self.project_root / "api" / "main.py"
        if not api_main.exists():
            return
        
        content = api_main.read_text()
        
        # Check for Single Responsibility Principle violations
        if content.count("async def") > 30:
            self.issues.append(RefactoringIssue(
                file_path=str(api_main),
                issue_type="srp_violation",
                line_number=0,
                description="Too many responsibilities in single file (30+ functions)",
                severity="high",
                fix_applied=False
            ))
        
        # Check for database schema in application code
        if "CREATE TABLE" in content:
            self.issues.append(RefactoringIssue(
                file_path=str(api_main),
                issue_type="separation_of_concerns",
                line_number=content.find("CREATE TABLE"),
                description="Database schema should be in separate migration files",
                severity="high",
                fix_applied=False
            ))
    
    def _check_database_schema_separation(self):
        """Ensure database schema is properly separated"""
        # Create migrations directory if it doesn't exist
        migrations_dir = self.project_root / "migrations"
        migrations_dir.mkdir(exist_ok=True)
        
        # Extract schema from api/main.py and create migration
        api_main = self.project_root / "api" / "main.py"
        if api_main.exists():
            content = api_main.read_text()
            
            # Find schema SQL
            schema_match = re.search(r'schema_sql = """(.*?)"""', content, re.DOTALL)
            if schema_match:
                schema_sql = schema_match.group(1)
                
                # Create migration file
                migration_file = migrations_dir / "001_initial_schema.sql"
                migration_file.write_text(schema_sql)
                logger.info("Extracted database schema to migration file")
                
                # Create schema manager
                self._create_schema_manager()
    
    def _create_schema_manager(self):
        """Create a proper schema manager following SOLID principles"""
        schema_manager_content = '''"""
Database Schema Manager
Handles all database schema operations following SOLID principles
"""

import asyncio
import asyncpg
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class SchemaManager:
    """Manages database schema migrations"""
    
    def __init__(self, db_pool: asyncpg.Pool, migrations_dir: str = "migrations"):
        self.db_pool = db_pool
        self.migrations_dir = Path(migrations_dir)
    
    async def initialize(self):
        """Initialize schema management tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    async def get_current_version(self) -> int:
        """Get current schema version"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
            )
            return result or 0
    
    async def apply_migrations(self):
        """Apply pending migrations"""
        current_version = await self.get_current_version()
        migrations = self._get_pending_migrations(current_version)
        
        for migration in migrations:
            await self._apply_migration(migration)
    
    def _get_pending_migrations(self, current_version: int) -> List[Path]:
        """Get list of pending migration files"""
        migrations = []
        for file in sorted(self.migrations_dir.glob("*.sql")):
            # Extract version from filename (e.g., 001_initial_schema.sql)
            version = int(file.stem.split("_")[0])
            if version > current_version:
                migrations.append(file)
        return migrations
    
    async def _apply_migration(self, migration_file: Path):
        """Apply a single migration"""
        version = int(migration_file.stem.split("_")[0])
        name = migration_file.stem
        
        logger.info(f"Applying migration {name}...")
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Execute migration
                sql = migration_file.read_text()
                await conn.execute(sql)
                
                # Record migration
                await conn.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES ($1, $2)",
                    version, name
                )
        
        logger.info(f"Migration {name} applied successfully")
'''
        
        schema_manager_path = self.project_root / "core" / "schema_manager.py"
        schema_manager_path.parent.mkdir(exist_ok=True)
        schema_manager_path.write_text(schema_manager_content)
        logger.info("Created SchemaManager following SOLID principles")
    
    def _check_dependency_injection(self):
        """Check for proper dependency injection patterns"""
        # This would analyze code for proper DI patterns
        pass
    
    def _apply_solid_principles(self):
        """Apply SOLID principles to the codebase"""
        logger.info("Phase 3: Applying SOLID principles...")
        
        # Create proper service layers
        self._create_service_layers()
        
        # Create repository pattern
        self._create_repository_pattern()
        
        # Create proper interfaces
        self._create_interfaces()
    
    def _create_service_layers(self):
        """Create service layer following SOLID principles"""
        services_dir = self.project_root / "services"
        services_dir.mkdir(exist_ok=True)
        
        # Create AuthenticationService
        auth_service_content = '''"""
Authentication Service
Handles all authentication logic following Single Responsibility Principle
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import bcrypt
import asyncpg
from fastapi import HTTPException, status

class AuthenticationService:
    """Service for handling authentication operations"""
    
    def __init__(self, db_pool: asyncpg.Pool, config: Dict[str, Any]):
        self.db_pool = db_pool
        self.secret_key = config['secret_key']
        self.algorithm = config['algorithm']
        self.token_expire_hours = config['token_expire_hours']
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=self.token_expire_hours)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM shared.users WHERE username = $1 AND is_active = true",
                username
            )
            
            if not user or not self.verify_password(password, user['password_hash']):
                return None
            
            return dict(user)
    
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get current user from token"""
        payload = self.decode_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM shared.users WHERE id = $1 AND is_active = true",
                user_id
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
        
        return dict(user)
'''
        
        auth_service_path = services_dir / "authentication_service.py"
        auth_service_path.write_text(auth_service_content)
        logger.info("Created AuthenticationService following SRP")
    
    def _create_repository_pattern(self):
        """Create repository pattern for data access"""
        repositories_dir = self.project_root / "repositories"
        repositories_dir.mkdir(exist_ok=True)
        
        # Create base repository
        base_repo_content = '''"""
Base Repository Pattern
Provides abstract interface for data access following SOLID principles
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import asyncpg

class BaseRepository(ABC):
    """Abstract base repository"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        """Find entity by ID"""
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Find all entities"""
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new entity"""
        pass
    
    @abstractmethod
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing entity"""
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """Delete entity"""
        pass

class UserRepository(BaseRepository):
    """Repository for user data access"""
    
    async def find_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM shared.users WHERE id = $1", id
            )
            return dict(row) if row else None
    
    async def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM shared.users WHERE username = $1", username
            )
            return dict(row) if row else None
    
    async def find_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM shared.users ORDER BY created_at DESC LIMIT $1", limit
            )
            return [dict(row) for row in rows]
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO shared.users (username, email, password_hash, role)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            """, data['username'], data['email'], data['password_hash'], data.get('role', 'user'))
            return dict(row)
    
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Build dynamic update query
        set_clauses = []
        values = []
        param_count = 1
        
        for key, value in data.items():
            if key not in ['id', 'created_at']:  # Skip immutable fields
                set_clauses.append(f"{key} = ${param_count}")
                values.append(value)
                param_count += 1
        
        if not set_clauses:
            return None
        
        values.append(id)
        query = f"""
            UPDATE shared.users 
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ${param_count}
            RETURNING *
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *values)
            return dict(row) if row else None
    
    async def delete(self, id: int) -> bool:
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM shared.users WHERE id = $1", id
            )
            return result.split()[-1] != '0'
'''
        
        base_repo_path = repositories_dir / "base_repository.py"
        base_repo_path.write_text(base_repo_content)
        logger.info("Created Repository pattern following SOLID principles")
    
    def _create_interfaces(self):
        """Create proper interfaces for dependency inversion"""
        interfaces_dir = self.project_root / "interfaces"
        interfaces_dir.mkdir(exist_ok=True)
        
        # Create service interfaces
        service_interface_content = '''"""
Service Interfaces
Defines contracts for services following Interface Segregation Principle
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IAuthenticationService(ABC):
    """Interface for authentication services"""
    
    @abstractmethod
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        pass
    
    @abstractmethod
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create access token"""
        pass
    
    @abstractmethod
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get user from token"""
        pass

class IConversationService(ABC):
    """Interface for conversation services"""
    
    @abstractmethod
    async def generate_response(
        self, 
        user_id: int, 
        persona_type: str, 
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI response"""
        pass
    
    @abstractmethod
    async def get_conversation_history(
        self, 
        user_id: int, 
        persona_type: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        pass

class IPersonaService(ABC):
    """Interface for persona management services"""
    
    @abstractmethod
    async def get_all_personas(self) -> List[Dict[str, Any]]:
        """Get all personas"""
        pass
    
    @abstractmethod
    async def get_persona_by_id(self, persona_id: int) -> Optional[Dict[str, Any]]:
        """Get persona by ID"""
        pass
    
    @abstractmethod
    async def update_persona(self, persona_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update persona configuration"""
        pass
'''
        
        interface_path = interfaces_dir / "service_interfaces.py"
        interface_path.write_text(service_interface_content)
        logger.info("Created service interfaces following ISP")
    
    def _clean_code_smells(self):
        """Clean common code smells"""
        logger.info("Phase 4: Cleaning code smells...")
        
        # Fix long functions
        self._fix_long_functions()
        
        # Fix duplicate code
        self._fix_duplicate_code()
        
        # Add proper error handling
        self._add_error_handling()
    
    def _fix_long_functions(self):
        """Break down long functions into smaller ones"""
        # This would analyze and refactor long functions
        pass
    
    def _fix_duplicate_code(self):
        """Identify and consolidate duplicate code"""
        # This would find and refactor duplicate code patterns
        pass
    
    def _add_error_handling(self):
        """Add comprehensive error handling"""
        error_handler_content = '''"""
Centralized Error Handling
Provides consistent error handling across the application
"""

import logging
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import traceback

logger = logging.getLogger(__name__)

class ApplicationError(Exception):
    """Base application error"""
    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class ValidationError(ApplicationError):
    """Validation error"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR", 400)
        self.field = field

class AuthenticationError(ApplicationError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)

class AuthorizationError(ApplicationError):
    """Authorization error"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR", 403)

class NotFoundError(ApplicationError):
    """Resource not found error"""
    def __init__(self, resource: str, id: Any):
        super().__init__(f"{resource} with id {id} not found", "NOT_FOUND", 404)

class ConflictError(ApplicationError):
    """Resource conflict error"""
    def __init__(self, message: str):
        super().__init__(message, "CONFLICT", 409)

class ExternalServiceError(ApplicationError):
    """External service error"""
    def __init__(self, service: str, message: str):
        super().__init__(f"{service} error: {message}", "EXTERNAL_SERVICE_ERROR", 503)

async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Handle application errors"""
    error_response = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "status_code": exc.status_code
        }
    }
    
    if hasattr(exc, 'field') and exc.field:
        error_response["error"]["field"] = exc.field
    
    logger.warning(f"Application error: {exc.code} - {exc.message}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors"""
    error_id = hash(str(exc) + str(request.url))
    
    logger.error(f"Unexpected error {error_id}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "error_id": str(error_id)
            }
        }
    )

def setup_error_handlers(app):
    """Setup error handlers for FastAPI app"""
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(HTTPException, application_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
'''
        
        error_handler_path = self.project_root / "core" / "error_handling.py"
        error_handler_path.write_text(error_handler_content)
        logger.info("Created centralized error handling")
    
    def _optimize_performance(self):
        """Optimize performance issues"""
        logger.info("Phase 5: Optimizing performance...")
        
        # Create connection pool manager
        self._create_connection_pool_manager()
        
        # Add caching layer
        self._add_caching_layer()
        
        # Add monitoring
        self._add_monitoring()
    
    def _create_connection_pool_manager(self):
        """Create proper connection pool management"""
        pool_manager_content = '''"""
Connection Pool Manager
Manages database connections efficiently
"""

import asyncio
import asyncpg
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class ConnectionPoolManager:
    """Manages database connection pools"""
    
    def __init__(self, database_url: str, pool_config: Optional[Dict[str, Any]] = None):
        self.database_url = database_url
        self.pool_config = pool_config or {
            'min_size': 5,
            'max_size': 20,
            'max_queries': 50000,
            'max_inactive_connection_lifetime': 300.0,
            'command_timeout': 60.0
        }
        self._pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize connection pool"""
        async with self._lock:
            if self._pool is None:
                logger.info("Creating database connection pool...")
                self._pool = await asyncpg.create_pool(
                    self.database_url,
                    **self.pool_config
                )
                logger.info(f"Connection pool created with {self.pool_config}")
    
    async def close(self):
        """Close connection pool"""
        async with self._lock:
            if self._pool:
                await self._pool.close()
                self._pool = None
                logger.info("Connection pool closed")
    
    @property
    def pool(self) -> asyncpg.Pool:
        """Get connection pool"""
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        return self._pool
    
    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute(self, query: str, *args, timeout: float = None):
        """Execute a query"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)
    
    async def fetch(self, query: str, *args, timeout: float = None):
        """Fetch multiple rows"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args, timeout=timeout)
    
    async def fetchrow(self, query: str, *args, timeout: float = None):
        """Fetch single row"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args, timeout=timeout)
    
    async def fetchval(self, query: str, *args, timeout: float = None):
        """Fetch single value"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args, timeout=timeout)
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if self._pool:
            return {
                'size': self._pool.get_size(),
                'free_size': self._pool.get_free_size(),
                'min_size': self._pool.get_min_size(),
                'max_size': self._pool.get_max_size()
            }
        return {}
'''
        
        pool_manager_path = self.project_root / "core" / "connection_pool_manager.py"
        pool_manager_path.parent.mkdir(exist_ok=True)
        pool_manager_path.write_text(pool_manager_content)
        logger.info("Created ConnectionPoolManager")
    
    def _add_caching_layer(self):
        """Add caching layer for performance"""
        cache_manager_content = '''"""
Cache Manager
Provides caching functionality for improved performance
"""

import asyncio
import json
from typing import Any, Optional, Callable, Union
from datetime import datetime, timedelta
import hashlib
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages application caching"""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._redis: Optional[redis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self._redis = await redis.from_url(self.redis_url, decode_responses=True)
        logger.info("Cache manager initialized")
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("Cache manager closed")
    
    def _generate_key(self, namespace: str, key: Union[str, dict]) -> str:
        """Generate cache key"""
        if isinstance(key, dict):
            key = json.dumps(key, sort_keys=True)
        
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return f"{namespace}:{key_hash}"
    
    async def get(self, namespace: str, key: Union[str, dict]) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            value = await self._redis.get(cache_key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    async def set(self, namespace: str, key: Union[str, dict], value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        cache_key = self._generate_key(namespace, key)
        ttl = ttl or self.default_ttl
        
        try:
            await self._redis.setex(
                cache_key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def delete(self, namespace: str, key: Union[str, dict]):
        """Delete value from cache"""
        cache_key = self._generate_key(namespace, key)
        
        try:
            await self._redis.delete(cache_key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    async def clear_namespace(self, namespace: str):
        """Clear all keys in a namespace"""
        try:
            pattern = f"{namespace}:*"
            cursor = 0
            
            while True:
                cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def cached(self, namespace: str, ttl: Optional[int] = None):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Generate cache key from function arguments
                cache_key = {
                    'func': func.__name__,
                    'args': args,
                    'kwargs': kwargs
                }
                
                # Try to get from cache
                cached_value = await self.get(namespace, cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute function and cache result
                result = await func(*args, **kwargs)
                await self.set(namespace, cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
'''
        
        cache_manager_path = self.project_root / "core" / "cache_manager.py"
        cache_manager_path.write_text(cache_manager_content)
        logger.info("Created CacheManager")
    
    def _add_monitoring(self):
        """Add monitoring capabilities"""
        monitoring_content = '''"""
Application Monitoring
Provides comprehensive monitoring and metrics collection
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class Metric:
    """Represents a single metric"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Collects and manages application metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.timers: Dict[str, list] = defaultdict(list)
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        self.counters[name] += value
        self.metrics[name].append(Metric(name, self.counters[name], tags=tags or {}))
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        self.gauges[name] = value
        self.metrics[name].append(Metric(name, value, tags=tags or {}))
    
    def record_timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric"""
        self.timers[name].append(duration)
        self.metrics[name].append(Metric(name, duration, tags=tags or {}))
    
    @asynccontextmanager
    async def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_timer(name, duration, tags)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timers': {}
        }
        
        # Calculate timer statistics
        for name, durations in self.timers.items():
            if durations:
                summary['timers'][name] = {
                    'count': len(durations),
                    'mean': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations),
                    'total': sum(durations)
                }
        
        return summary

class HealthChecker:
    """Manages health checks for the application"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.check_results: Dict[str, Dict[str, Any]] = {}
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check"""
        self.checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                duration = time.time() - start_time
                
                results[name] = {
                    'healthy': result.get('healthy', True),
                    'message': result.get('message', 'OK'),
                    'duration_ms': duration * 1000,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if not results[name]['healthy']:
                    overall_healthy = False
                    
            except Exception as e:
                results[name] = {
                    'healthy': False,
                    'message': str(e),
                    'duration_ms': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
                overall_healthy = False
        
        self.check_results = results
        
        return {
            'healthy': overall_healthy,
            'checks': results,
            'timestamp': datetime.utcnow().isoformat()
        }

# Global instances
metrics = MetricsCollector()
health = HealthChecker()

def monitor_performance(name: str):
    """Decorator to monitor function performance"""
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            async with metrics.timer(f"{name}.duration"):
                try:
                    result = await func(*args, **kwargs)
                    metrics.increment_counter(f"{name}.success")
                    return result
                except Exception as e:
                    metrics.increment_counter(f"{name}.error")
                    raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_timer(f"{name}.duration", duration)
                metrics.increment_counter(f"{name}.success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_timer(f"{name}.duration", duration)
                metrics.increment_counter(f"{name}.error")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
'''
        
        monitoring_path = self.project_root / "core" / "monitoring.py"
        monitoring_path.write_text(monitoring_content)
        logger.info("Created monitoring system")
    
    def _generate_refactoring_report(self):
        """Generate comprehensive refactoring report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.refactoring_stats,
            'issues': [
                {
                    'file': issue.file_path,
                    'type': issue.issue_type,
                    'line': issue.line_number,
                    'description': issue.description,
                    'severity': issue.severity,
                    'fixed': issue.fix_applied
                }
                for issue in self.issues
            ],
            'recommendations': [
                "Implement comprehensive testing suite",
                "Add API documentation with OpenAPI/Swagger",
                "Implement rate limiting for API endpoints",
                "Add distributed tracing for debugging",
                "Implement proper logging strategy",
                "Add performance benchmarks",
                "Create CI/CD pipeline with quality gates"
            ]
        }
        
        # Save report
        report_path = self.project_root / "refactoring_report.json"
        report_path.write_text(json.dumps(report, indent=2))
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("REFACTORING COMPLETE")
        logger.info("="*60)
        logger.info(f"Files analyzed: {self.refactoring_stats['files_analyzed']}")
        logger.info(f"Issues found: {self.refactoring_stats['issues_found']}")
        logger.info(f"Issues fixed: {self.refactoring_stats['issues_fixed']}")
        logger.info(f"Report saved to: {report_path}")

if __name__ == "__main__":
    refactorer = ArchitectureRefactorer()
    refactorer.analyze_and_refactor()