#!/usr/bin/env python3
"""
Claude Project Analyzer Integration
Provides comprehensive project analysis and code generation using Claude/Claude Max
"""

import os
import sys
import json
import time
import asyncio
import anthropic
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.database import initialize_database
from ai_components.orchestration.ai_orchestrator import WeaviateManager

logger = logging.getLogger(__name__)

class ClaudeAnalyzer:
    """Claude-based project analyzer and code generator"""
    
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.db = None
        self.weaviate_manager = WeaviateManager()
        
        self.performance_metrics = {
            'requests_made': 0,
            'total_tokens': 0,
            'total_latency': 0,
            'errors': 0,
            'cache_hits': 0
        }
        
        # Claude Max model mapping
        self.model_configs = {
            "claude-max": "claude-3-opus-20240229",
            "claude-sonnet": "claude-3-5-sonnet-20241022",
            "claude-haiku": "claude-3-haiku-20240307"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Initialize database
        postgres_url = os.environ.get(
            'POSTGRES_URL',
            'postgresql://postgres:password@localhost:5432/orchestra'
        )
        weaviate_url = os.environ.get('WEAVIATE_URL', 'http://localhost:8080')
        weaviate_api_key = os.environ.get('WEAVIATE_API_KEY')
        
        self.db = await initialize_database(postgres_url, weaviate_url, weaviate_api_key)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.db:
            await self.db.close()
    
    async def analyze_project(self, project_path: str, analysis_type: str = "comprehensive") -> Dict:
        """Comprehensive project analysis using Claude"""
        start_time = time.time()
        
        try:
            # Gather project context
            project_context = await self._gather_project_context(project_path)
            
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(project_context, analysis_type)
            
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ]
            )
            
            # Process response
            analysis_result = {
                "analysis_type": analysis_type,
                "project_path": project_path,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat(),
                "analysis": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "latency": time.time() - start_time
            }
            
            # Parse structured analysis if possible
            try:
                if "```json" in response.content[0].text:
                    json_start = response.content[0].text.find("```json") + 7
                    json_end = response.content[0].text.find("```", json_start)
                    json_content = response.content[0].text[json_start:json_end].strip()
                    analysis_result["structured_analysis"] = json.loads(json_content)
            except json.JSONDecodeError:
                logger.warning("Could not parse structured analysis from Claude response")
            
            # Log to database
            await self._log_analysis(
                analysis_type=analysis_type,
                project_path=project_path,
                status="success",
                result=analysis_result
            )
            
            # Update Weaviate
            await self._update_weaviate_context(
                "claude_project_analysis",
                project_path,
                analysis_result
            )
            
            # Update metrics
            self.performance_metrics['requests_made'] += 1
            self.performance_metrics['total_tokens'] += analysis_result["usage"]["total_tokens"]
            self.performance_metrics['total_latency'] += analysis_result["latency"]
            
            return analysis_result
            
        except Exception as e:
            self.performance_metrics['errors'] += 1
            await self._log_error("analyze_project", project_path, str(e))
            raise
    
    async def generate_code(self, prompt: str, context: Dict = None, 
                          code_type: str = "implementation") -> Dict:
        """Generate code using Claude"""
        start_time = time.time()
        
        try:
            # Enhance prompt with context
            enhanced_prompt = self._create_code_generation_prompt(prompt, context, code_type)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ]
            )
            
            generation_result = {
                "prompt": prompt,
                "code_type": code_type,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat(),
                "generated_code": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "latency": time.time() - start_time
            }
            
            # Extract code blocks
            code_blocks = self._extract_code_blocks(response.content[0].text)
            if code_blocks:
                generation_result["code_blocks"] = code_blocks
            
            await self._log_analysis(
                analysis_type="code_generation",
                project_path=prompt[:100],  # Use truncated prompt as identifier
                status="success",
                result=generation_result
            )
            
            await self._update_weaviate_context(
                "claude_code_generation",
                prompt,
                generation_result
            )
            
            self.performance_metrics['requests_made'] += 1
            self.performance_metrics['total_tokens'] += generation_result["usage"]["total_tokens"]
            self.performance_metrics['total_latency'] += generation_result["latency"]
            
            return generation_result
            
        except Exception as e:
            self.performance_metrics['errors'] += 1
            await self._log_error("generate_code", prompt[:100], str(e))
            raise
    
    async def refactor_code(self, code_content: str, refactor_goals: List[str],
                          file_path: str = None) -> Dict:
        """Refactor code using Claude"""
        start_time = time.time()
        
        try:
            refactor_prompt = self._create_refactor_prompt(code_content, refactor_goals, file_path)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": refactor_prompt
                    }
                ]
            )
            
            refactor_result = {
                "original_file": file_path,
                "refactor_goals": refactor_goals,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat(),
                "refactored_code": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "latency": time.time() - start_time
            }
            
            # Extract refactored code
            code_blocks = self._extract_code_blocks(response.content[0].text)
            if code_blocks:
                refactor_result["refactored_code_blocks"] = code_blocks
            
            await self._log_analysis(
                analysis_type="code_refactoring",
                project_path=file_path or "unknown",
                status="success",
                result=refactor_result
            )
            
            await self._update_weaviate_context(
                "claude_code_refactoring",
                file_path or "unknown",
                refactor_result
            )
            
            self.performance_metrics['requests_made'] += 1
            self.performance_metrics['total_tokens'] += refactor_result["usage"]["total_tokens"]
            self.performance_metrics['total_latency'] += refactor_result["latency"]
            
            return refactor_result
            
        except Exception as e:
            self.performance_metrics['errors'] += 1
            await self._log_error("refactor_code", file_path or "unknown", str(e))
            raise
    
    async def _gather_project_context(self, project_path: str) -> Dict:
        """Gather comprehensive project context"""
        context = {
            "project_path": project_path,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            project_root = Path(project_path)
            
            # Get project structure
            context["structure"] = self._get_project_structure(project_root)
            
            # Read key configuration files
            config_files = [
                "requirements.txt", "pyproject.toml", "package.json", 
                "README.md", ".env.example", "Dockerfile", ".cursorrules"
            ]
            
            context["config_files"] = {}
            for config_file in config_files:
                config_path = project_root / config_file
                if config_path.exists() and config_path.stat().st_size < 10000:  # Limit size
                    try:
                        context["config_files"][config_file] = config_path.read_text(encoding='utf-8')
                    except Exception:
                        context["config_files"][config_file] = "[Could not read file]"
            
            # Get recent git commits if available
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "log", "--oneline", "-10"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    context["recent_commits"] = result.stdout.strip().split('\n')
            except Exception:
                pass
            
            # Get MCP context from memory server
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://localhost:8003/context/project_analysis",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            context["mcp_memory"] = await response.json()
            except Exception:
                pass
                
        except Exception as e:
            logger.warning(f"Error gathering project context: {e}")
            context["context_error"] = str(e)
        
        return context
    
    def _get_project_structure(self, project_root: Path, max_depth: int = 3) -> Dict:
        """Get project directory structure"""
        def scan_directory(path: Path, current_depth: int = 0) -> Dict:
            if current_depth > max_depth:
                return {"...": "max_depth_reached"}
            
            structure = {}
            try:
                for item in sorted(path.iterdir()):
                    if item.name.startswith('.') and item.name not in ['.env.example', '.cursorrules']:
                        continue
                    
                    if item.is_dir():
                        # Skip large directories
                        if item.name in ['node_modules', '__pycache__', '.git', 'venv', '.venv']:
                            structure[f"{item.name}/"] = "[skipped]"
                        else:
                            structure[f"{item.name}/"] = scan_directory(item, current_depth + 1)
                    else:
                        # Include file size for context
                        try:
                            size = item.stat().st_size
                            structure[item.name] = f"{size} bytes"
                        except:
                            structure[item.name] = "unknown size"
            except PermissionError:
                structure["[permission_denied]"] = True
            
            return structure
        
        return scan_directory(project_root)
    
    def _create_analysis_prompt(self, context: Dict, analysis_type: str) -> str:
        """Create comprehensive analysis prompt for Claude"""
        base_prompt = f"""
You are an expert software architect and code analyst. Analyze the following project comprehensively.

Project Context:
{json.dumps(context, indent=2)}

Analysis Type: {analysis_type}

Provide a detailed analysis including:

1. **Architecture Overview**
   - System design patterns
   - Component relationships
   - Data flow analysis

2. **Code Quality Assessment**
   - Code organization and structure
   - Adherence to best practices
   - Potential technical debt

3. **Performance Considerations**
   - Bottlenecks and optimization opportunities
   - Scalability concerns
   - Resource utilization

4. **Security Analysis**
   - Potential vulnerabilities
   - Security best practices compliance
   - Authentication and authorization patterns

5. **Maintainability**
   - Documentation quality
   - Testing coverage
   - Code complexity metrics

6. **Recommendations**
   - Priority improvements
   - Architectural enhancements
   - Performance optimizations

Please provide both a narrative analysis and a structured JSON summary at the end with the following format:

```json
{{
  "overall_score": 0-100,
  "architecture_score": 0-100,
  "code_quality_score": 0-100,
  "performance_score": 0-100,
  "security_score": 0-100,
  "maintainability_score": 0-100,
  "key_strengths": ["strength1", "strength2"],
  "critical_issues": ["issue1", "issue2"],
  "recommendations": [
    {{
      "priority": "high|medium|low",
      "category": "architecture|performance|security|maintainability",
      "description": "detailed recommendation",
      "effort": "low|medium|high"
    }}
  ]
}}
```
"""
        return base_prompt
    
    def _create_code_generation_prompt(self, prompt: str, context: Dict, code_type: str) -> str:
        """Create code generation prompt with context"""
        enhanced_prompt = f"""
You are an expert Python developer. Generate high-quality, production-ready code.

Request: {prompt}
Code Type: {code_type}
Context: {json.dumps(context, indent=2) if context else 'None'}

Requirements:
1. Use Python 3.10+ features and syntax
2. Include comprehensive type hints (PEP 484)
3. Add Google-style docstrings
4. Follow Black formatting standards
5. Include error handling and logging
6. Add performance considerations
7. Include unit tests when appropriate

Please provide:
1. The main code implementation
2. Any necessary imports
3. Usage examples
4. Brief explanation of design decisions

Format your response with clear code blocks and explanations.
"""
        return enhanced_prompt
    
    def _create_refactor_prompt(self, code_content: str, refactor_goals: List[str], 
                              file_path: str = None) -> str:
        """Create refactoring prompt"""
        goals_text = "\n".join(f"- {goal}" for goal in refactor_goals)
        
        refactor_prompt = f"""
You are an expert Python developer. Refactor the following code to achieve these goals:

{goals_text}

Original Code:
```python
{code_content}
```

File Path: {file_path or "Unknown"}

Requirements for refactoring:
1. Preserve all existing functionality
2. Improve code readability and maintainability
3. Add type hints where missing
4. Optimize performance where possible
5. Follow Python best practices
6. Add comprehensive docstrings
7. Ensure error handling is robust

Please provide:
1. The refactored code with explanations
2. Summary of changes made
3. Performance improvements achieved
4. Any breaking changes (should be minimal)

Format your response with clear code blocks and explanations.
"""
        return refactor_prompt
    
    def _extract_code_blocks(self, text: str) -> List[Dict]:
        """Extract code blocks from Claude response"""
        code_blocks = []
        lines = text.split('\n')
        
        in_code_block = False
        current_block = []
        current_language = None
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    code_blocks.append({
                        "language": current_language,
                        "code": '\n'.join(current_block)
                    })
                    current_block = []
                    in_code_block = False
                else:
                    # Start of code block
                    current_language = line.strip()[3:].strip() or "text"
                    in_code_block = True
            elif in_code_block:
                current_block.append(line)
        
        return code_blocks
    
    async def _log_analysis(self, analysis_type: str, project_path: str, 
                           status: str, result: Dict = None) -> None:
        """Log analysis to PostgreSQL"""
        try:
            await self.db.execute_query(
                """
                INSERT INTO claude_analysis_logs 
                (analysis_type, project_path, status, model_used, result, 
                 input_tokens, output_tokens, latency_seconds, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                analysis_type, project_path, status, self.model,
                json.dumps(result) if result else None,
                result.get("usage", {}).get("input_tokens", 0) if result else 0,
                result.get("usage", {}).get("output_tokens", 0) if result else 0,
                result.get("latency", 0.0) if result else 0.0,
                datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to log analysis: {e}")
    
    async def _log_error(self, action: str, identifier: str, error: str) -> None:
        """Log error to PostgreSQL"""
        try:
            await self.db.execute_query(
                """
                INSERT INTO claude_analysis_logs 
                (analysis_type, project_path, status, error_message, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                action, identifier, "error", error, datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    async def _update_weaviate_context(self, context_type: str, identifier: str, 
                                     data: Dict) -> None:
        """Update Weaviate with analysis results"""
        try:
            self.weaviate_manager.store_context(
                workflow_id="claude_analysis_operations",
                task_id=f"{context_type}_{int(time.time())}",
                context_type=context_type,
                content=json.dumps(data),
                metadata={
                    "identifier": identifier,
                    "timestamp": datetime.now().isoformat(),
                    "tool": "claude",
                    "model": self.model
                }
            )
        except Exception as e:
            logger.error(f"Failed to update Weaviate: {e}")
    
    async def get_performance_metrics(self) -> Dict:
        """Get Claude performance metrics"""
        avg_latency = (
            self.performance_metrics['total_latency'] / 
            self.performance_metrics['requests_made']
            if self.performance_metrics['requests_made'] > 0 else 0
        )
        
        error_rate = (
            self.performance_metrics['errors'] / 
            self.performance_metrics['requests_made']
            if self.performance_metrics['requests_made'] > 0 else 0
        )
        
        avg_tokens = (
            self.performance_metrics['total_tokens'] / 
            self.performance_metrics['requests_made']
            if self.performance_metrics['requests_made'] > 0 else 0
        )
        
        return {
            "requests_made": self.performance_metrics['requests_made'],
            "average_latency": avg_latency,
            "error_rate": error_rate,
            "total_tokens_used": self.performance_metrics['total_tokens'],
            "average_tokens_per_request": avg_tokens,
            "cache_hits": self.performance_metrics['cache_hits'],
            "status": "operational" if error_rate < 0.05 else "degraded",
            "model_used": self.model
        }
    
    async def compare_with_cursor_ai(self, test_prompt: str) -> Dict:
        """Compare Claude performance with Cursor AI"""
        comparison_results = {
            "test_prompt": test_prompt,
            "timestamp": datetime.now().isoformat(),
            "claude_results": {},
            "cursor_ai_results": {},
            "comparison": {}
        }
        
        try:
            # Test Claude
            claude_start = time.time()
            claude_result = await self.generate_code(test_prompt, {"comparison_test": True})
            claude_latency = time.time() - claude_start
            
            comparison_results["claude_results"] = {
                "latency": claude_latency,
                "tokens_used": claude_result.get("usage", {}).get("total_tokens", 0),
                "success": True,
                "model": self.model
            }
            
            # Test Cursor AI (if available)
            try:
                from ai_components.cursor_ai.cursor_integration_enhanced import CursorAIClient
                
                async with CursorAIClient() as cursor_client:
                    cursor_start = time.time()
                    cursor_result = await cursor_client.generate_code(test_prompt, {"comparison_test": True})
                    cursor_latency = time.time() - cursor_start
                    
                    comparison_results["cursor_ai_results"] = {
                        "latency": cursor_latency,
                        "success": not cursor_result.get("error", False),
                        "fallback": cursor_result.get("fallback", False)
                    }
                    
            except Exception as e:
                comparison_results["cursor_ai_results"] = {
                    "error": str(e),
                    "success": False
                }
            
            # Generate comparison
            if comparison_results["cursor_ai_results"].get("success"):
                comparison_results["comparison"] = {
                    "claude_faster": claude_latency < comparison_results["cursor_ai_results"]["latency"],
                    "latency_difference": abs(claude_latency - comparison_results["cursor_ai_results"]["latency"]),
                    "recommendation": "claude" if claude_latency < 2.0 else "cursor_ai"
                }
            else:
                comparison_results["comparison"] = {
                    "claude_available": True,
                    "cursor_ai_available": False,
                    "recommendation": "claude"
                }
            
        except Exception as e:
            comparison_results["error"] = str(e)
        
        return comparison_results


async def setup_claude_database():
    """Setup database tables for Claude integration"""
    # Get database URL from environment or use default
    postgres_url = os.environ.get(
        'POSTGRES_URL',
        'postgresql://postgres:password@localhost:5432/orchestra'
    )
    
    weaviate_url = os.environ.get('WEAVIATE_URL', 'http://localhost:8080')
    weaviate_api_key = os.environ.get('WEAVIATE_API_KEY')
    
    db = await initialize_database(postgres_url, weaviate_url, weaviate_api_key)
    
    try:
        print("🗄️  Setting up Claude analysis database tables...")
        
        await db.execute_query("""
            CREATE TABLE IF NOT EXISTS claude_analysis_logs (
                id SERIAL PRIMARY KEY,
                analysis_type VARCHAR(100) NOT NULL,
                project_path TEXT,
                status VARCHAR(50) NOT NULL,
                model_used VARCHAR(100),
                result JSONB,
                error_message TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                latency_seconds FLOAT DEFAULT 0.0,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """, fetch=False)
        
        # Create indexes
        await db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_claude_analysis_type 
            ON claude_analysis_logs(analysis_type);
        """, fetch=False)
        
        await db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_claude_analysis_created_at 
            ON claude_analysis_logs(created_at DESC);
        """, fetch=False)
        
        print("✅ Claude analysis database tables created!")
    
    finally:
        await db.close()


async def main():
    """Test Claude integration"""
    print("🚀 Testing Claude Project Analyzer Integration...")
    
    # Setup database
    await setup_claude_database()
    
    async with ClaudeAnalyzer() as analyzer:
        # Test project analysis
        print("\n🔍 Testing project analysis...")
        try:
            analysis_result = await analyzer.analyze_project(".", "comprehensive")
            print("✅ Project analysis completed")
            print(f"Tokens used: {analysis_result['usage']['total_tokens']}")
            print(f"Latency: {analysis_result['latency']:.2f}s")
        except Exception as e:
            print(f"❌ Project analysis failed: {e}")
        
        # Test code generation
        print("\n🏗️  Testing code generation...")
        try:
            code_result = await analyzer.generate_code(
                "Create a Python function to calculate the factorial of a number with error handling",
                {"language": "python", "style": "production"}
            )
            print("✅ Code generation completed")
            print(f"Tokens used: {code_result['usage']['total_tokens']}")
        except Exception as e:
            print(f"❌ Code generation failed: {e}")
        
        # Test comparison with Cursor AI
        print("\n⚖️  Testing comparison with Cursor AI...")
        try:
            comparison = await analyzer.compare_with_cursor_ai(
                "Create a simple Python class for managing a shopping cart"
            )
            print("✅ Comparison completed")
            print(f"Recommendation: {comparison['comparison'].get('recommendation', 'unknown')}")
        except Exception as e:
            print(f"❌ Comparison failed: {e}")
        
        # Get performance metrics
        metrics = await analyzer.get_performance_metrics()
        print(f"\n📈 Performance Metrics:")
        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    asyncio.run(main()) 