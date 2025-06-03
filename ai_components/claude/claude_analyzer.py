# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Claude-based project analyzer and code generator"""
    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.db = None
        # Remove WeaviateManager dependency for now to avoid client issues
        self.weaviate_manager = None
        
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
            logger.warning(f"Database initialization failed: {e}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
    async def analyze_project(self, project_path: str, analysis_type: str = "comprehensive") -> Dict:
        """Comprehensive project analysis using Claude"""
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

                pass
                if "```json" in response.content[0].text:
                    json_start = response.content[0].text.find("```json") + 7
                    json_end = response.content[0].text.find("```", json_start)
                    json_content = response.content[0].text[json_start:json_end].strip()
                    analysis_result["structured_analysis"] = json.loads(json_content)
            except Exception:

                pass
                logger.warning("Could not parse structured analysis from Claude response")
            
            # Log to database
            await self._log_analysis(
                analysis_type=analysis_type,
                project_path=project_path,
                status="success",
                result=analysis_result
            )
            
            # Update Weaviate (if available)
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
            
        except Exception:

            
            pass
            self.performance_metrics['errors'] += 1
            await self._log_error("analyze_project", project_path, str(e))
            raise
    
    async def generate_code(self, prompt: str, context: Dict = None, 
                          code_type: str = "implementation") -> Dict:
        """Generate code using Claude"""
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
            
        except Exception:

            
            pass
            self.performance_metrics['errors'] += 1
            await self._log_error("generate_code", prompt[:100], str(e))
            raise
    
    async def refactor_code(self, code_content: str, refactor_goals: List[str],
                          file_path: str = None) -> Dict:
        """Refactor code using Claude"""
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
            
        except Exception:

            
            pass
            self.performance_metrics['errors'] += 1
            await self._log_error("refactor_code", file_path or "unknown", str(e))
            raise
    
    async def _gather_project_context(self, project_path: str) -> Dict:
        """Gather comprehensive project context"""
            "project_path": project_path,
            "timestamp": datetime.now().isoformat()
        }
        
        try:

        
            pass
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

                        pass
                        context["config_files"][config_file] = config_path.read_text(encoding='utf-8')
                    except Exception:

                        pass
                        context["config_files"][config_file] = "[Could not read file]"
            
            # Get recent git commits if available
            try:

                pass
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
                pass
            
            # Get MCP context from memory server
            try:

                pass
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
                pass
                
        except Exception:

                
            pass
            logger.warning(f"Error gathering project context: {e}")
            context["context_error"] = str(e)
        
        return context
    
    def _get_project_structure(self, project_root: Path, max_depth: int = 3) -> Dict:
        """Get project directory structure"""
                return {"...": "max_depth_reached"}
            
            structure = {}
            try:

                pass
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

                            pass
                            size = item.stat().st_size
                            structure[item.name] = f"{size} bytes"
                        except Exception:

                            pass
                            structure[item.name] = "unknown size"
            except Exception:

                pass
                structure["[permission_denied]"] = True
            
            return structure
        
        return scan_directory(project_root)
    
    def _create_analysis_prompt(self, context: Dict, analysis_type: str) -> str:
        """Create comprehensive analysis prompt for Claude"""
        base_prompt = f"""
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
        """Create code generation prompt with context"""
        enhanced_prompt = f"""
"""
        """Create refactoring prompt"""
        goals_text = "\n".join(f"- {goal}" for goal in refactor_goals)
        
        refactor_prompt = f"""
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
        """Extract code blocks from Claude response"""
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
                """
                """
                result.get("usage", {}).get("input_tokens", 0) if result else 0,
                result.get("usage", {}).get("output_tokens", 0) if result else 0,
                result.get("latency", 0.0) if result else 0.0,
                datetime.now()
            )
        except Exception:

            pass
            logger.error(f"Failed to log analysis: {e}")
    
    async def _log_error(self, action: str, identifier: str, error: str) -> None:
        """Log error to PostgreSQL"""
                """
                """
                action, identifier, "error", error, datetime.now()
            )
        except Exception:

            pass
            logger.error(f"Failed to log error: {e}")
    
    async def _update_weaviate_context(self, context_type: str, identifier: str, 
                                     data: Dict) -> None:
        """Update Weaviate with analysis results"""
            return
            
        try:

            
            pass
            # This would be implemented when WeaviateManager is fixed
            pass
        except Exception:

            pass
            logger.error(f"Failed to update Weaviate: {e}")
    
    async def get_performance_metrics(self) -> Dict:
        """Get Claude performance metrics"""
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
            "test_prompt": test_prompt,
            "timestamp": datetime.now().isoformat(),
            "claude_results": {},
            "cursor_ai_results": {},
            "comparison": {}
        }
        
        try:

        
            pass
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

                pass
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
                    
            except Exception:

                    
                pass
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
            
        except Exception:

            
            pass
            comparison_results["error"] = str(e)
        
        return comparison_results


async def setup_claude_database():
    """Setup database tables for Claude integration"""
        print("🗄️  Setting up Claude analysis database tables...")
        
        await db.execute_query("""
        """
        await db.execute_query("""
        """
        await db.execute_query("""
        """
        print("✅ Claude analysis database tables created!")
    
    finally:
        await db.close()


async def main():
    """Example usage of Claude analyzer"""
                project_path="/root/orchestra-main",
                analysis_type="architecture"
            )
            print("Analysis Result:")
            print(json.dumps(result, indent=2, default=str))
            
            # Test code generation
            code_result = await analyzer.generate_code(
                prompt="Create a FastAPI endpoint for user authentication",
                context={"framework": "FastAPI", "database": "PostgreSQL"},
                code_type="api_endpoint"
            )
            print("\nCode Generation Result:")
            print(json.dumps(code_result, indent=2, default=str))
            
    except Exception:

            
        pass
        logger.error(f"Error in main: {e}")

# Add alias for consistent naming
ClaudeProjectAnalyzer = ClaudeAnalyzer

if __name__ == "__main__":
    asyncio.run(main()) 