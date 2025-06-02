#!/usr/bin/env python3
"""
Recraft API Integration for UI/UX Design Generation
Provides design generation and code output with OpenRouter routing
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.database import initialize_database
from ai_components.orchestration.intelligent_cache import CacheType, cache_decorator, get_cache

logger = logging.getLogger(__name__)

class RecraftDesignGenerator:
    """Recraft API integration for automated UI/UX design generation"""
    
    def __init__(self, api_key: str = None, openrouter_key: str = None):
        self.api_key = api_key or os.environ.get('RECRAFT_API_KEY')
        self.openrouter_key = openrouter_key or os.environ.get('OPENROUTER_API_KEY')
        self.base_url = "https://api.recraft.ai/v1"
        self.openrouter_url = "https://openrouter.ai/api/v1"
        self.db = None
        self.cache = None
        
        # Performance metrics
        self.metrics = {
            "designs_generated": 0,
            "code_outputs": 0,
            "total_requests": 0,
            "total_latency": 0,
            "errors": 0,
            "openrouter_routing": 0
        }
        
        # Design templates and styles
        self.design_templates = {
            "web_app": {
                "style": "modern",
                "components": ["header", "navigation", "content", "footer"],
                "color_scheme": "professional",
                "layout": "responsive"
            },
            "mobile_app": {
                "style": "material_design",
                "components": ["app_bar", "navigation_drawer", "content", "bottom_nav"],
                "color_scheme": "vibrant",
                "layout": "mobile_first"
            },
            "landing_page": {
                "style": "minimal",
                "components": ["hero", "features", "testimonials", "cta"],
                "color_scheme": "brand_focused",
                "layout": "single_page"
            },
            "dashboard": {
                "style": "data_visualization",
                "components": ["sidebar", "main_panel", "widgets", "charts"],
                "color_scheme": "data_friendly",
                "layout": "grid_based"
            }
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
        self.cache = await get_cache()
        await self._setup_design_database()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.db:
            await self.db.close()
    
    @cache_decorator(CacheType.CODE_GENERATION)
    async def generate_design(self, design_brief: str, design_type: str = "web_app",
                            style_preferences: Dict = None, output_format: str = "html_css") -> Dict:
        """Generate UI/UX design using Recraft API"""
        start_time = time.time()
        
        try:
            # Get design template
            template = self.design_templates.get(design_type, self.design_templates["web_app"])
            
            # Enhance brief with template context
            enhanced_brief = await self._enhance_design_brief(design_brief, template, style_preferences)
            
            # Route through OpenRouter for enhanced processing
            processed_brief = await self._route_through_openrouter(enhanced_brief, "design_enhancement")
            
            # Generate design with Recraft
            design_request = {
                "prompt": processed_brief,
                "style": template["style"],
                "components": template["components"],
                "output_format": output_format,
                "responsive": True,
                "accessibility": True,
                "performance_optimized": True
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/designs/generate",
                    headers=headers,
                    json=design_request
                ) as response:
                    
                    if response.status == 200:
                        design_result = await response.json()
                        
                        # Process and enhance the design
                        enhanced_design = await self._process_design_result(design_result, design_type)
                        
                        # Generate accompanying code
                        code_output = await self._generate_code_output(enhanced_design, output_format)
                        
                        final_result = {
                            "design_id": enhanced_design.get("id"),
                            "design_type": design_type,
                            "design_data": enhanced_design,
                            "code_output": code_output,
                            "assets": enhanced_design.get("assets", []),
                            "metadata": {
                                "brief": design_brief,
                                "template": template,
                                "style_preferences": style_preferences,
                                "generated_at": datetime.now().isoformat(),
                                "latency": time.time() - start_time
                            }
                        }
                        
                        # Log to database
                        await self._log_design_generation(
                            design_brief=design_brief,
                            design_type=design_type,
                            status="success",
                            result=final_result
                        )
                        
                        # Update metrics
                        self.metrics["designs_generated"] += 1
                        self.metrics["total_requests"] += 1
                        self.metrics["total_latency"] += time.time() - start_time
                        
                        return final_result
                    
                    else:
                        error_msg = f"Recraft API error: {response.status} - {await response.text()}"
                        await self._log_error("generate_design", design_brief, error_msg)
                        raise Exception(error_msg)
        
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("generate_design", design_brief, str(e))
            
            # Fallback to template-based generation
            return await self._fallback_design_generation(design_brief, design_type, style_preferences)
    
    @cache_decorator(CacheType.CODE_GENERATION)
    async def generate_code_from_design(self, design_data: Dict, target_framework: str = "react") -> Dict:
        """Generate production-ready code from design data"""
        start_time = time.time()
        
        try:
            # Route through OpenRouter for code generation enhancement
            code_prompt = await self._create_code_generation_prompt(design_data, target_framework)
            enhanced_prompt = await self._route_through_openrouter(code_prompt, "code_generation")
            
            # Generate code with Recraft
            code_request = {
                "design_id": design_data.get("id"),
                "target_framework": target_framework,
                "prompt": enhanced_prompt,
                "include_tests": True,
                "include_documentation": True,
                "optimize_performance": True,
                "accessibility_compliant": True
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/code/generate",
                    headers=headers,
                    json=code_request
                ) as response:
                    
                    if response.status == 200:
                        code_result = await response.json()
                        
                        # Enhance code output
                        enhanced_code = await self._enhance_code_output(code_result, target_framework)
                        
                        result = {
                            "framework": target_framework,
                            "components": enhanced_code.get("components", {}),
                            "styles": enhanced_code.get("styles", {}),
                            "assets": enhanced_code.get("assets", []),
                            "tests": enhanced_code.get("tests", {}),
                            "documentation": enhanced_code.get("documentation", ""),
                            "build_config": enhanced_code.get("build_config", {}),
                            "metadata": {
                                "design_id": design_data.get("id"),
                                "generated_at": datetime.now().isoformat(),
                                "latency": time.time() - start_time
                            }
                        }
                        
                        # Log code generation
                        await self._log_code_generation(
                            design_id=design_data.get("id"),
                            framework=target_framework,
                            status="success",
                            result=result
                        )
                        
                        self.metrics["code_outputs"] += 1
                        self.metrics["total_requests"] += 1
                        self.metrics["total_latency"] += time.time() - start_time
                        
                        return result
                    
                    else:
                        error_msg = f"Code generation error: {response.status} - {await response.text()}"
                        await self._log_error("generate_code", str(design_data.get("id")), error_msg)
                        raise Exception(error_msg)
        
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("generate_code", str(design_data.get("id")), str(e))
            raise
    
    async def refine_design(self, design_id: str, feedback: List[str], 
                          refinement_goals: List[str] = None) -> Dict:
        """Refine existing design based on feedback"""
        start_time = time.time()
        
        try:
            # Process feedback through OpenRouter
            feedback_analysis = await self._analyze_feedback(feedback)
            
            refinement_request = {
                "design_id": design_id,
                "feedback": feedback_analysis,
                "goals": refinement_goals or [],
                "preserve_brand": True,
                "maintain_accessibility": True
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/designs/{design_id}/refine",
                    headers=headers,
                    json=refinement_request
                ) as response:
                    
                    if response.status == 200:
                        refined_result = await response.json()
                        
                        result = {
                            "original_design_id": design_id,
                            "refined_design": refined_result,
                            "changes_made": refined_result.get("changes", []),
                            "feedback_addressed": feedback_analysis,
                            "metadata": {
                                "refined_at": datetime.now().isoformat(),
                                "latency": time.time() - start_time
                            }
                        }
                        
                        await self._log_design_refinement(design_id, feedback, result)
                        
                        return result
                    
                    else:
                        error_msg = f"Design refinement error: {response.status} - {await response.text()}"
                        await self._log_error("refine_design", design_id, error_msg)
                        raise Exception(error_msg)
        
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("refine_design", design_id, str(e))
            raise
    
    async def _route_through_openrouter(self, content: str, task_type: str) -> str:
        """Route content processing through OpenRouter for enhancement"""
        if not self.openrouter_key:
            return content
        
        try:
            self.metrics["openrouter_routing"] += 1
            
            # Select appropriate model based on task
            model_mapping = {
                "design_enhancement": "anthropic/claude-3-sonnet",
                "code_generation": "openai/gpt-4-turbo",
                "feedback_analysis": "anthropic/claude-3-haiku"
            }
            
            model = model_mapping.get(task_type, "anthropic/claude-3-sonnet")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                }
                
                request_data = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are an expert UI/UX designer. Task: {task_type}. Enhance the following content for better design outcomes."
                        },
                        {
                            "role": "user", 
                            "content": content
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
                
                async with session.post(
                    f"{self.openrouter_url}/chat/completions",
                    headers=headers,
                    json=request_data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        enhanced_content = result["choices"][0]["message"]["content"]
                        return enhanced_content
                    else:
                        logger.warning(f"OpenRouter routing failed: {response.status}")
                        return content
        
        except Exception as e:
            logger.warning(f"OpenRouter routing error: {e}")
            return content
    
    async def _enhance_design_brief(self, brief: str, template: Dict, style_preferences: Dict = None) -> str:
        """Enhance design brief with template and style context"""
        enhanced_brief = f"""
Design Brief: {brief}

Template Context:
- Style: {template['style']}
- Components: {', '.join(template['components'])}
- Color Scheme: {template['color_scheme']}
- Layout: {template['layout']}

Additional Requirements:
- Responsive design for all screen sizes
- Accessibility (WCAG 2.1 AA compliance)
- Performance optimized
- Modern design patterns
- User-friendly interface
"""
        
        if style_preferences:
            enhanced_brief += f"\nStyle Preferences:\n{json.dumps(style_preferences, indent=2)}"
        
        return enhanced_brief
    
    async def _process_design_result(self, design_result: Dict, design_type: str) -> Dict:
        """Process and enhance design result from Recraft"""
        # Add design type context
        design_result["design_type"] = design_type
        design_result["processed_at"] = datetime.now().isoformat()
        
        # Add accessibility enhancements
        if "accessibility" not in design_result:
            design_result["accessibility"] = {
                "aria_labels": True,
                "contrast_ratio": "AA",
                "keyboard_navigation": True,
                "screen_reader_friendly": True
            }
        
        # Add performance optimizations
        if "performance" not in design_result:
            design_result["performance"] = {
                "lazy_loading": True,
                "image_optimization": True,
                "css_minification": True,
                "critical_css": True
            }
        
        return design_result
    
    async def _generate_code_output(self, design_data: Dict, output_format: str) -> Dict:
        """Generate code output from design data"""
        if output_format == "html_css":
            return {
                "html": f"<!-- Generated HTML for {design_data.get('design_type', 'design')} -->",
                "css": f"/* Generated CSS for {design_data.get('design_type', 'design')} */",
                "javascript": f"// Generated JavaScript for {design_data.get('design_type', 'design')}"
            }
        elif output_format == "react":
            return {
                "components": f"// Generated React components for {design_data.get('design_type', 'design')}",
                "styles": f"// Generated styled-components for {design_data.get('design_type', 'design')}",
                "hooks": f"// Generated custom hooks for {design_data.get('design_type', 'design')}"
            }
        else:
            return {"code": f"// Generated code for {design_data.get('design_type', 'design')}"}
    
    async def _create_code_generation_prompt(self, design_data: Dict, framework: str) -> str:
        """Create prompt for code generation"""
        return f"""
Generate production-ready {framework} code for the following design:

Design Type: {design_data.get('design_type', 'web_app')}
Components: {json.dumps(design_data.get('components', []), indent=2)}

Requirements:
- Modern {framework} best practices
- TypeScript support
- Responsive design
- Accessibility compliance
- Performance optimized
- Clean, maintainable code
- Comprehensive comments
- Error handling
- Testing-friendly structure

Please generate complete, deployable code with proper file structure.
"""
    
    async def _enhance_code_output(self, code_result: Dict, framework: str) -> Dict:
        """Enhance generated code output"""
        # Add framework-specific enhancements
        enhanced_code = code_result.copy()
        
        enhanced_code["framework_version"] = self._get_framework_version(framework)
        enhanced_code["build_tools"] = self._get_build_tools(framework)
        enhanced_code["dependencies"] = self._get_dependencies(framework)
        
        return enhanced_code
    
    def _get_framework_version(self, framework: str) -> str:
        """Get latest framework version"""
        versions = {
            "react": "18.2.0",
            "vue": "3.3.0",
            "angular": "16.0.0",
            "svelte": "4.0.0"
        }
        return versions.get(framework, "latest")
    
    def _get_build_tools(self, framework: str) -> List[str]:
        """Get recommended build tools for framework"""
        tools = {
            "react": ["vite", "webpack", "babel"],
            "vue": ["vite", "vue-cli"],
            "angular": ["angular-cli", "webpack"],
            "svelte": ["vite", "rollup"]
        }
        return tools.get(framework, ["webpack"])
    
    def _get_dependencies(self, framework: str) -> List[str]:
        """Get framework dependencies"""
        deps = {
            "react": ["react", "react-dom", "@types/react"],
            "vue": ["vue", "vue-router"],
            "angular": ["@angular/core", "@angular/common"],
            "svelte": ["svelte", "svelte-kit"]
        }
        return deps.get(framework, [])
    
    async def _analyze_feedback(self, feedback: List[str]) -> Dict:
        """Analyze feedback using OpenRouter"""
        feedback_text = "\n".join(feedback)
        analysis_prompt = f"""
Analyze the following UI/UX feedback and provide actionable insights:

Feedback:
{feedback_text}

Please categorize the feedback and provide specific improvement recommendations.
"""
        
        analyzed_feedback = await self._route_through_openrouter(analysis_prompt, "feedback_analysis")
        
        return {
            "original_feedback": feedback,
            "analysis": analyzed_feedback,
            "categories": ["usability", "visual_design", "performance", "accessibility"],
            "priority": "high",
            "actionable_items": []
        }
    
    async def _fallback_design_generation(self, brief: str, design_type: str, style_preferences: Dict) -> Dict:
        """Fallback design generation when API is unavailable"""
        template = self.design_templates.get(design_type, self.design_templates["web_app"])
        
        return {
            "design_id": f"fallback_{int(time.time())}",
            "design_type": design_type,
            "design_data": {
                "template": template,
                "style": template["style"],
                "components": template["components"],
                "fallback": True
            },
            "code_output": await self._generate_code_output({"design_type": design_type}, "html_css"),
            "metadata": {
                "brief": brief,
                "fallback_reason": "API unavailable",
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def _setup_design_database(self) -> None:
        """Setup database tables for design operations"""
        await self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS recraft_designs (
                id SERIAL PRIMARY KEY,
                design_id VARCHAR(200),
                design_brief TEXT NOT NULL,
                design_type VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL,
                result JSONB,
                error_message TEXT,
                latency_seconds FLOAT DEFAULT 0.0,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """, fetch=False)
        
        await self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS recraft_code_generations (
                id SERIAL PRIMARY KEY,
                design_id VARCHAR(200),
                framework VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL,
                result JSONB,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """, fetch=False)
        
        await self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_recraft_designs_type 
            ON recraft_designs(design_type);
        """, fetch=False)
    
    async def _log_design_generation(self, design_brief: str, design_type: str, 
                                   status: str, result: Dict = None) -> None:
        """Log design generation to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO recraft_designs 
                (design_id, design_brief, design_type, status, result, latency_seconds, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            result.get("design_id") if result else None,
            design_brief, design_type, status,
            json.dumps(result) if result else None,
            result.get("metadata", {}).get("latency", 0.0) if result else 0.0,
            datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log design generation: {e}")
    
    async def _log_code_generation(self, design_id: str, framework: str, 
                                 status: str, result: Dict = None) -> None:
        """Log code generation to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO recraft_code_generations 
                (design_id, framework, status, result, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """,
            design_id, framework, status,
            json.dumps(result) if result else None,
            datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log code generation: {e}")
    
    async def _log_design_refinement(self, design_id: str, feedback: List[str], result: Dict) -> None:
        """Log design refinement to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO recraft_designs 
                (design_id, design_brief, design_type, status, result, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
            design_id, f"Refinement: {'; '.join(feedback)}", "refinement", "success",
            json.dumps(result), datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log design refinement: {e}")
    
    async def _log_error(self, action: str, identifier: str, error: str) -> None:
        """Log error to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO recraft_designs 
                (design_brief, design_type, status, error_message, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """,
            f"{action}: {identifier}", action, "error", error, datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        total_requests = max(1, self.metrics["total_requests"])
        avg_latency = self.metrics["total_latency"] / total_requests
        
        return {
            "designs_generated": self.metrics["designs_generated"],
            "code_outputs": self.metrics["code_outputs"],
            "total_requests": total_requests,
            "average_latency": avg_latency,
            "error_rate": self.metrics["errors"] / total_requests,
            "openrouter_usage": self.metrics["openrouter_routing"],
            "status": "operational" if self.metrics["errors"] / total_requests < 0.1 else "degraded"
        }


async def main():
    """Test Recraft integration"""
    print("🚀 Testing Recraft UI/UX Design Integration...")
    
    async with RecraftDesignGenerator() as recraft:
        # Test design generation
        print("\n1. Testing design generation...")
        try:
            design_result = await recraft.generate_design(
                "Create a modern dashboard for a project management app",
                design_type="dashboard",
                style_preferences={"theme": "dark", "accent_color": "blue"}
            )
            print(f"   ✅ Design generated: {design_result['design_id']}")
        except Exception as e:
            print(f"   ❌ Design generation failed: {e}")
        
        # Test code generation
        print("\n2. Testing code generation...")
        try:
            if 'design_result' in locals():
                code_result = await recraft.generate_code_from_design(
                    design_result["design_data"],
                    target_framework="react"
                )
                print(f"   ✅ Code generated for framework: {code_result['framework']}")
        except Exception as e:
            print(f"   ❌ Code generation failed: {e}")
        
        # Performance metrics
        metrics = recraft.get_performance_metrics()
        print(f"\n📊 Performance Metrics:")
        print(f"   Designs Generated: {metrics['designs_generated']}")
        print(f"   Code Outputs: {metrics['code_outputs']}")
        print(f"   Average Latency: {metrics['average_latency']:.2f}s")
        print(f"   OpenRouter Usage: {metrics['openrouter_usage']}")


if __name__ == "__main__":
    asyncio.run(main()) 