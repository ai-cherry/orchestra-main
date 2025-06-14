"""
AI Directives and Embedded Prompts
Provides decorators and utilities for embedding AI-friendly prompts in code
"""
from functools import wraps
from typing import Callable, Dict, Any, List, Optional
import inspect
import json

class AIPrompt:
    """Decorator for embedding AI prompts in functions"""
    
    def __init__(
        self,
        template: str,
        required_context: List[str] = None,
        examples: List[Dict[str, Any]] = None,
        constraints: List[str] = None,
        preferred_tools: List[str] = None
    ):
        self.template = template
        self.required_context = required_context or []
        self.examples = examples or []
        self.constraints = constraints or []
        self.preferred_tools = preferred_tools or []
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Attach AI metadata to function
        wrapper._ai_prompt = {
            "template": self.template,
            "required_context": self.required_context,
            "examples": self.examples,
            "constraints": self.constraints,
            "preferred_tools": self.preferred_tools,
            "function_name": func.__name__,
            "module": func.__module__,
            "docstring": inspect.getdoc(func)
        }
        
        return wrapper

# Convenience decorators for common patterns
def ai_infrastructure(description: str):
    """Decorator for infrastructure-related functions"""
    return AIPrompt(
        template=f"Infrastructure task: {description}",
        required_context=["pulumi_stack", "lambda_config"],
        preferred_tools=["pulumi", "terraform"],
        constraints=["Must validate with pulumi preview before applying"]
    )

def ai_database(operation: str):
    """Decorator for database operations"""
    return AIPrompt(
        template=f"Database operation: {operation}",
        required_context=["database_schemas", "connection_strings"],
        constraints=["Must use transactions", "Include error handling"]
    )

def ai_vector_search(index_type: str):
    """Decorator for vector search operations"""
    return AIPrompt(
        template=f"Vector search in {index_type}",
        required_context=["vector_configs", "embedding_model"],
        preferred_tools=["pinecone", "weaviate"],
        examples=[{
            "query": "Find similar documents",
            "expected_output": "List of document IDs with scores"
        }]
    )

def ai_api_endpoint(method: str, path: str):
    """Decorator for API endpoints"""
    return AIPrompt(
        template=f"{method} {path} endpoint implementation",
        required_context=["api_schemas", "auth_requirements"],
        constraints=["Must validate input", "Return proper HTTP status codes"],
        examples=[{
            "request": {"sample": "data"},
            "response": {"status": 200, "data": {}}
        }]
    )

# Example usage patterns for AI agents
class AIDirectiveExamples:
    """Examples showing how to use AI directives"""
    
    @ai_infrastructure("Deploy new Lambda function with GPU support")
    def deploy_gpu_lambda(self, function_name: str, gpu_type: str = "A100"):
        """
        Deploy a Lambda Labs GPU instance for AI workloads
        
        AI Agent Instructions:
        1. Check available GPU types in Lambda Labs
        2. Configure Pulumi stack with appropriate resources
        3. Set up networking and security groups
        4. Deploy and validate
        """
        pass
    
    @ai_database("Migrate vector embeddings to new schema")
    def migrate_embeddings(self, source_table: str, target_table: str):
        """
        Migrate embeddings between database tables
        
        AI Agent Instructions:
        1. Create migration transaction
        2. Batch process embeddings (1000 at a time)
        3. Validate data integrity
        4. Update indexes
        """
        pass
    
    @ai_vector_search("pinecone")
    def semantic_search(self, query: str, top_k: int = 10):
        """
        Perform semantic search using Pinecone
        
        AI Agent Instructions:
        1. Generate embedding for query using OpenAI
        2. Search Pinecone index
        3. Post-process results with metadata
        4. Return ranked results
        """
        pass
    
    @ai_api_endpoint("POST", "/api/agents/create")
    def create_agent_endpoint(self, agent_data: Dict[str, Any]):
        """
        Create a new AI agent
        
        AI Agent Instructions:
        1. Validate agent configuration
        2. Store in PostgreSQL
        3. Initialize vector space in Weaviate
        4. Return agent ID and status
        """
        pass

# Prompt collection utility
class PromptCollector:
    """Collects all AI prompts in the codebase"""
    
    @staticmethod
    def collect_prompts(module_path: str) -> List[Dict[str, Any]]:
        """Scan codebase for AI prompts"""
        prompts = []
        # Implementation would scan Python files for decorated functions
        return prompts
    
    @staticmethod
    def export_to_cursor(prompts: List[Dict[str, Any]], output_path: str):
        """Export prompts in Cursor-friendly format"""
        cursor_prompts = {
            "version": "1.0",
            "prompts": prompts,
            "metadata": {
                "project": "Orchestra AI",
                "generated": "auto"
            }
        }
        with open(output_path, 'w') as f:
            json.dump(cursor_prompts, f, indent=2)

# Meta-prompts for AI agents
META_PROMPTS = {
    "code_generation": """
    When generating code for Orchestra AI:
    1. Always use type hints in Python
    2. Include comprehensive error handling
    3. Add logging with structlog
    4. Follow the project's async patterns
    5. Integrate with existing MCP servers when applicable
    """,
    
    "infrastructure": """
    When working with infrastructure:
    1. Use Pulumi for all IaC needs
    2. Target Lambda Labs for GPU workloads
    3. Ensure Vercel compatibility for deployments
    4. Use environment variables for configuration
    5. Always run pulumi preview before pulumi up
    """,
    
    "database": """
    When working with databases:
    1. PostgreSQL for relational data
    2. Redis for caching and queues
    3. Pinecone/Weaviate for vector storage
    4. Always use connection pooling
    5. Include migration scripts
    """,
    
    "testing": """
    When writing tests:
    1. Use pytest for Python tests
    2. Mock external services
    3. Test both success and failure paths
    4. Include integration tests for API endpoints
    5. Validate vector search accuracy
    """
} 