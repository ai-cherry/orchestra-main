"""
AI Context Loader for Orchestra Platform
Provides unified context to AI coding agents (Cursor, Manus, Factory AI, etc.)
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()

class AIContextLoader:
    """Loads and manages context for AI coding agents"""
    
    def __init__(self):
        self.root_path = Path(__file__).parent.parent
        self.context_cache = {}
        
    def load_agent_context(self) -> Dict[str, Any]:
        """Load comprehensive context for AI agents"""
        return {
            "project_meta": self._get_project_meta(),
            "infrastructure": self._get_infrastructure_context(),
            "database_schemas": self._get_database_schemas(),
            "vector_configs": self._get_vector_configs(),
            "api_endpoints": self._get_api_endpoints(),
            "deployment_info": self._get_deployment_info(),
            "coding_standards": self._get_coding_standards(),
            "active_issues": self._get_active_issues()
        }
    
    def _get_project_meta(self) -> Dict[str, Any]:
        """Project metadata and structure"""
        return {
            "name": "Orchestra AI Platform",
            "type": "monorepo",
            "primary_language": "python",
            "deployment_target": "vercel",
            "infrastructure": "pulumi",
            "ai_providers": ["portkey", "openrouter"],
            "vector_dbs": ["pinecone", "weaviate"],
            "services": {
                "api": "FastAPI at port 8000",
                "mcp_server": "Memory management at port 8003",
                "frontend": "React/Vite at port 3000"
            }
        }
    
    def _get_infrastructure_context(self) -> Dict[str, Any]:
        """Pulumi and infrastructure context"""
        try:
            # Read Pulumi configuration
            pulumi_config = {}
            if (self.root_path / "Pulumi.yaml").exists():
                with open(self.root_path / "Pulumi.yaml") as f:
                    pulumi_config = yaml.safe_load(f)
            
            return {
                "provider": "pulumi",
                "stack": os.getenv("PULUMI_STACK", "development"),
                "resources": {
                    "lambda": "Lambda Labs GPU instances",
                    "databases": ["PostgreSQL", "Redis"],
                    "vector_stores": ["Pinecone", "Weaviate"]
                },
                "config": pulumi_config
            }
        except Exception as e:
            logger.error("Failed to load infrastructure context", error=str(e))
            return {}
    
    def _get_database_schemas(self) -> Dict[str, Any]:
        """Database schema information"""
        schemas = {}
        
        # PostgreSQL schemas
        schema_file = self.root_path / "database" / "unified_schema.sql"
        if schema_file.exists():
            schemas["postgresql"] = {
                "location": str(schema_file),
                "tables": ["users", "agents", "conversations", "memories", "files"]
            }
        
        # Vector DB schemas
        schemas["vector_stores"] = {
            "pinecone": {
                "indexes": ["embeddings", "documents"],
                "dimensions": 1536
            },
            "weaviate": {
                "classes": ["Document", "Memory", "Agent"],
                "vectorizer": "text2vec-openai"
            }
        }
        
        return schemas
    
    def _get_vector_configs(self) -> Dict[str, Any]:
        """Vector database configurations"""
        return {
            "pinecone": {
                "api_key_env": "PINECONE_API_KEY",
                "environment": "us-east-1",
                "index_name": "orchestra-embeddings"
            },
            "weaviate": {
                "url": os.getenv("WEAVIATE_URL", "http://localhost:8080"),
                "embedded": True,
                "modules": ["text2vec-openai", "qna-openai"]
            }
        }
    
    def _get_api_endpoints(self) -> List[Dict[str, str]]:
        """Available API endpoints"""
        return [
            {"path": "/api/health", "method": "GET", "description": "Health check"},
            {"path": "/api/agents", "method": "GET", "description": "List agents"},
            {"path": "/api/agents", "method": "POST", "description": "Create agent"},
            {"path": "/api/conversations", "method": "POST", "description": "Start conversation"},
            {"path": "/api/files/upload", "method": "POST", "description": "Upload file"},
            {"path": "/memory", "method": "POST", "description": "Store memory (MCP)"},
            {"path": "/memory/search", "method": "POST", "description": "Search memories (MCP)"}
        ]
    
    def _get_deployment_info(self) -> Dict[str, Any]:
        """Deployment configuration"""
        return {
            "platform": "vercel",
            "build_command": "npm run build",
            "output_directory": "dist",
            "environment_variables": [
                "DATABASE_URL",
                "REDIS_URL",
                "PINECONE_API_KEY",
                "WEAVIATE_URL",
                "PORTKEY_API_KEY",
                "OPENROUTER_API_KEY"
            ],
            "functions": {
                "api": "api/index.py",
                "maxDuration": 30
            }
        }
    
    def _get_coding_standards(self) -> Dict[str, Any]:
        """Coding standards and conventions"""
        return {
            "python": {
                "formatter": "black",
                "linter": "mypy",
                "docstring_style": "google",
                "type_hints": "required"
            },
            "typescript": {
                "formatter": "prettier",
                "linter": "eslint",
                "style": "airbnb"
            },
            "git": {
                "branch_naming": "feature/*, fix/*, chore/*",
                "commit_style": "conventional"
            }
        }
    
    def _get_active_issues(self) -> List[Dict[str, str]]:
        """Current known issues from status reports"""
        issues = []
        
        # Read from CRITICAL_FIXES_NEEDED.md if exists
        fixes_file = self.root_path / "CRITICAL_FIXES_NEEDED.md"
        if fixes_file.exists():
            issues.append({
                "type": "critical",
                "source": "CRITICAL_FIXES_NEEDED.md",
                "summary": "Docker build failures, API module imports"
            })
        
        # Read from ISSUES_SUMMARY.md
        issues_file = self.root_path / "ISSUES_SUMMARY.md"
        if issues_file.exists():
            issues.append({
                "type": "blocking",
                "source": "ISSUES_SUMMARY.md",
                "summary": "Frontend build failures, missing dependencies"
            })
        
        return issues
    
    def export_for_cursor(self) -> None:
        """Export context in Cursor-friendly format"""
        context = self.load_agent_context()
        cursor_dir = self.root_path / ".cursor"
        cursor_dir.mkdir(exist_ok=True)
        
        with open(cursor_dir / "project_context.json", "w") as f:
            json.dump(context, f, indent=2)
        
        logger.info("Exported AI context for Cursor", path=str(cursor_dir))
    
    def stream_to_agents(self) -> None:
        """Stream real-time context updates to agents"""
        # This would integrate with your MCP servers
        pass

# Singleton instance
ai_context = AIContextLoader()

if __name__ == "__main__":
    # Generate context file
    ai_context.export_for_cursor()
    print("AI context exported successfully!") 