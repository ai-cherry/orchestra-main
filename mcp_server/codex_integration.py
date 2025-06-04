#!/usr/bin/env python3
"""
Enhanced OpenAI Codex Integration for Cherry AI
Provides direct code editing capabilities through OpenAI Codex API with Cherry AI context
"""

import openai
import os
import json
import asyncio
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cherry-ai-codex")

@dataclass
class CodeContext:
    """Context information for code generation"""
    file_path: str
    language: str
    existing_code: str
    cursor_position: int
    project_context: Dict[str, Any]

class CherryAICodex:
    """Enhanced OpenAI Codex integration for intelligent code editing"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Codex with API key and Cherry AI context"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Load Cherry AI project context
        self.project_context = self._load_project_context()
        
        # Initialize code patterns and templates
        self.code_patterns = self._load_code_patterns()
        
    def _load_project_context(self) -> Dict[str, Any]:
        """Load comprehensive Cherry AI project context"""
        context = {
            "project_name": "Cherry AI Orchestrator",
            "description": "AI-powered infrastructure management system with three personas",
            "architecture": {
                "frontend": "HTML5, CSS3, Vanilla JavaScript",
                "backend": "Python 3.11, Flask, FastAPI",
                "databases": ["PostgreSQL", "Redis", "Weaviate", "Pinecone"],
                "infrastructure": ["Vultr", "Pulumi IaC", "GitHub Actions"],
                "ai_services": ["OpenAI", "Anthropic", "Google Gemini", "Perplexity"]
            },
            "personas": {
                "cherry": {
                    "name": "Cherry Personal",
                    "description": "Personal AI assistant for individual tasks",
                    "port": 8001,
                    "capabilities": ["personal_scheduling", "email_management", "task_automation"]
                },
                "sophia": {
                    "name": "Sophia Business",
                    "description": "Business AI assistant for professional tasks",
                    "port": 8002,
                    "capabilities": ["business_analytics", "crm_integration", "workflow_automation"]
                },
                "karen": {
                    "name": "Karen Healthcare",
                    "description": "Healthcare AI assistant for medical tasks",
                    "port": 8003,
                    "capabilities": ["patient_management", "medical_records", "appointment_scheduling"]
                }
            },
            "key_components": [
                "MCP servers for AI tool integration",
                "Admin interface with three personas",
                "Database layer with multiple backends",
                "Infrastructure automation and monitoring",
                "Vector databases for semantic search",
                "Real-time deployment pipeline"
            ],
            "coding_standards": {
                "python": {
                    "style": "Black formatter, PEP 8 compliant",
                    "type_hints": "Required for all functions",
                    "docstrings": "Google-style docstrings",
                    "testing": "pytest with comprehensive coverage",
                    "error_handling": "Structured logging with proper exceptions",
                    "async": "Use async/await for I/O operations"
                },
                "javascript": {
                    "style": "ES6+ features, modern syntax",
                    "framework": "Vanilla JS with modern APIs",
                    "responsive": "Mobile-first design",
                    "accessibility": "ARIA labels and semantic HTML"
                }
            },
            "security": {
                "api_keys": "Environment variables only",
                "authentication": "JWT tokens with refresh",
                "authorization": "Role-based access control",
                "encryption": "TLS 1.3 for all communications"
            }
        }
        return context
    
    def _load_code_patterns(self) -> Dict[str, str]:
        """Load common code patterns for Cherry AI project"""
        patterns = {
            "python_class": '''
class {class_name}:
    """
    {description}
    
    Attributes:
        {attributes}
    """
    
    def __init__(self, {init_params}):
        """Initialize {class_name}"""
        {init_body}
    
    async def {method_name}(self, {method_params}) -> {return_type}:
        """
        {method_description}
        
        Args:
            {method_args}
            
        Returns:
            {return_description}
            
        Raises:
            {exceptions}
        """
        try:
            {method_body}
        except Exception as e:
            logger.error(f"Error in {method_name}: {{e}}")
            raise
''',
            "fastapi_endpoint": '''
@app.{http_method}("/{endpoint_path}")
async def {function_name}({parameters}) -> {return_type}:
    """
    {description}
    
    Args:
        {args_description}
        
    Returns:
        {return_description}
    """
    try:
        {endpoint_body}
        return {{"status": "success", "data": result}}
    except Exception as e:
        logger.error(f"Error in {function_name}: {{e}}")
        raise HTTPException(status_code=500, detail=str(e))
''',
            "mcp_server_tool": '''
@server.call_tool()
async def {tool_name}(arguments: dict) -> List[types.TextContent]:
    """
    {tool_description}
    
    Args:
        arguments: Tool arguments containing {arg_description}
        
    Returns:
        List of text content with tool results
    """
    try:
        {tool_implementation}
        
        return [
            types.TextContent(
                type="text",
                text=json.dumps({{
                    "status": "success",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }}, indent=2)
            )
        ]
    except Exception as e:
        logger.error(f"Error in {tool_name}: {{e}}")
        return [
            types.TextContent(
                type="text", 
                text=json.dumps({{
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }}, indent=2)
            )
        ]
''',
            "javascript_api_client": '''
class {class_name} {{
    constructor(baseURL, apiKey) {{
        this.baseURL = baseURL;
        this.apiKey = apiKey;
        this.headers = {{
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${{apiKey}}`
        }};
    }}
    
    async {method_name}({parameters}) {{
        try {{
            const response = await fetch(`${{this.baseURL}}/{endpoint}`, {{
                method: '{http_method}',
                headers: this.headers,
                body: JSON.stringify({{
                    {request_body}
                }})
            }});
            
            if (!response.ok) {{
                throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
            }}
            
            return await response.json();
        }} catch (error) {{
            console.error('API request failed:', error);
            throw error;
        }}
    }}
}}
'''
        }
        return patterns
    
    async def generate_code(
        self, 
        prompt: str, 
        context: Optional[CodeContext] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> str:
        """Generate code using Codex with Cherry AI context"""
        
        # Build context-aware prompt
        system_prompt = self._build_system_prompt(context)
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 as Codex is deprecated
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.95
            )
            
            generated_code = response.choices[0].message.content
            
            # Post-process the generated code
            processed_code = self._post_process_code(generated_code, context)
            
            return processed_code
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            raise
    
    def _build_system_prompt(self, context: Optional[CodeContext] = None) -> str:
        """Build comprehensive system prompt with Cherry AI context"""
        
        base_prompt = f"""You are an expert AI coding assistant for the Cherry AI Orchestrator project.

PROJECT CONTEXT:
{json.dumps(self.project_context, indent=2)}

CODING GUIDELINES:
- Follow Cherry AI coding standards and patterns
- Use type hints and comprehensive docstrings
- Implement proper error handling and logging
- Consider the three-persona architecture (Cherry, Sophia, Karen)
- Ensure compatibility with existing infrastructure
- Use environment variables for configuration
- Write production-ready, scalable code

CURRENT TASK:
Generate high-quality code that integrates seamlessly with the Cherry AI ecosystem."""

        if context:
            base_prompt += f"""

FILE CONTEXT:
- File: {context.file_path}
- Language: {context.language}
- Existing code length: {len(context.existing_code)} characters

EXISTING CODE:
```{context.language}
{context.existing_code[:500]}...
```"""

        return base_prompt
    
    def _post_process_code(self, code: str, context: Optional[CodeContext] = None) -> str:
        """Post-process generated code for Cherry AI standards"""
        
        # Remove markdown code blocks if present
        if code.startswith("```"):
            lines = code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            code = "\n".join(lines)
        
        # Add Cherry AI specific imports if needed
        if context and context.language == "python":
            if "logging" in code and "import logging" not in code:
                code = "import logging\n" + code
            if "async def" in code and "import asyncio" not in code:
                code = "import asyncio\n" + code
        
        return code.strip()
    
    async def explain_code(self, code: str, language: str = "python") -> str:
        """Explain code in the context of Cherry AI project"""
        
        prompt = f"""Explain this {language} code in the context of the Cherry AI Orchestrator project:

```{language}
{code}
```

Please provide:
1. What this code does
2. How it fits into the Cherry AI architecture
3. Any potential improvements or concerns
4. Integration points with other Cherry AI components"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error explaining code: {e}")
            raise
    
    async def suggest_improvements(self, code: str, language: str = "python") -> List[str]:
        """Suggest improvements for code following Cherry AI standards"""
        
        prompt = f"""Analyze this {language} code and suggest improvements following Cherry AI Orchestrator standards:

```{language}
{code}
```

Focus on:
- Code quality and maintainability
- Performance optimizations
- Security considerations
- Integration with Cherry AI architecture
- Error handling and logging
- Type hints and documentation"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
                temperature=0.1
            )
            
            suggestions = response.choices[0].message.content
            return suggestions.split("\n") if suggestions else []
            
        except Exception as e:
            logger.error(f"Error suggesting improvements: {e}")
            raise
    
    async def generate_tests(self, code: str, language: str = "python") -> str:
        """Generate comprehensive tests for the given code"""
        
        prompt = f"""Generate comprehensive tests for this {language} code using Cherry AI testing standards:

```{language}
{code}
```

Requirements:
- Use pytest for Python tests
- Include unit tests and integration tests
- Test error conditions and edge cases
- Mock external dependencies appropriately
- Follow Cherry AI naming conventions
- Include docstrings for test functions"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating tests: {e}")
            raise

# CLI interface for direct usage
async def main():
    """CLI interface for Cherry AI Codex"""
    import sys
    
    if len(sys.argv) < 2:
        print("Cherry AI Codex - OpenAI Code Generation")
        print("Usage: python codex_integration.py <command> [args]")
        print("\nCommands:")
        print("  generate <prompt>     - Generate code from prompt")
        print("  explain <file>        - Explain code in file")
        print("  improve <file>        - Suggest improvements")
        print("  test <file>           - Generate tests")
        return
    
    codex = CherryAICodex()
    command = sys.argv[1]
    
    if command == "generate" and len(sys.argv) > 2:
        prompt = " ".join(sys.argv[2:])
        result = await codex.generate_code(prompt)
        print(result)
    
    elif command == "explain" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                code = f.read()
            result = await codex.explain_code(code)
            print(result)
        else:
            print(f"File not found: {file_path}")
    
    elif command == "improve" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                code = f.read()
            suggestions = await codex.suggest_improvements(code)
            for suggestion in suggestions:
                print(f"• {suggestion}")
        else:
            print(f"File not found: {file_path}")
    
    elif command == "test" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                code = f.read()
            result = await codex.generate_tests(code)
            print(result)
        else:
            print(f"File not found: {file_path}")
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    asyncio.run(main())

