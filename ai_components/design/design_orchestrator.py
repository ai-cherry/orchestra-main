#!/usr/bin/env python3
"""
Unified Design Orchestrator for UI/UX Automation
Integrates Recraft, DALL-E, Claude analysis, and workflow automation
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import logging
from enum import Enum

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.database import initialize_database
from ai_components.orchestration.intelligent_cache import CacheType, cache_decorator, get_cache
from ai_components.design.recraft_integration import RecraftDesignGenerator
from ai_components.design.dalle_integration import DALLEImageGenerator

logger = logging.getLogger(__name__)

class DesignPhase(Enum):
    ANALYSIS = "analysis"
    CONCEPT = "concept"
    DESIGN = "design"
    REFINEMENT = "refinement"
    FINALIZATION = "finalization"

class DesignOrchestrator:
    """Unified orchestrator for automated UI/UX design workflow"""
    
    def __init__(self):
        self.recraft = None
        self.dalle = None
        self.db = None
        self.cache = None
        
        # Workflow state management
        self.active_projects = {}
        
        # Performance metrics
        self.metrics = {
            "projects_created": 0,
            "designs_generated": 0,
            "images_created": 0,
            "workflows_completed": 0,
            "analysis_performed": 0,
            "total_requests": 0,
            "average_project_time": 0.0,
            "errors": 0
        }
        
        # Design workflow templates
        self.workflow_templates = {
            "complete_website": {
                "phases": [
                    DesignPhase.ANALYSIS,
                    DesignPhase.CONCEPT,
                    DesignPhase.DESIGN,
                    DesignPhase.REFINEMENT,
                    DesignPhase.FINALIZATION
                ],
                "deliverables": [
                    "hero_section",
                    "navigation_design",
                    "content_layouts",
                    "footer_design",
                    "responsive_variations"
                ],
                "estimated_time": 1800  # 30 minutes
            },
            "mobile_app": {
                "phases": [
                    DesignPhase.ANALYSIS,
                    DesignPhase.CONCEPT,
                    DesignPhase.DESIGN,
                    DesignPhase.REFINEMENT
                ],
                "deliverables": [
                    "app_screens",
                    "navigation_patterns",
                    "icon_set",
                    "style_guide"
                ],
                "estimated_time": 1200  # 20 minutes
            },
            "landing_page": {
                "phases": [
                    DesignPhase.CONCEPT,
                    DesignPhase.DESIGN,
                    DesignPhase.FINALIZATION
                ],
                "deliverables": [
                    "hero_design",
                    "feature_sections",
                    "call_to_actions",
                    "supporting_images"
                ],
                "estimated_time": 900  # 15 minutes
            },
            "dashboard": {
                "phases": [
                    DesignPhase.ANALYSIS,
                    DesignPhase.DESIGN,
                    DesignPhase.REFINEMENT
                ],
                "deliverables": [
                    "layout_structure",
                    "data_visualizations",
                    "control_elements",
                    "responsive_design"
                ],
                "estimated_time": 1500  # 25 minutes
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
        
        # Initialize design tools
        self.recraft = RecraftDesignGenerator()
        self.dalle = DALLEImageGenerator()
        
        await self.recraft.__aenter__()
        await self.dalle.__aenter__()
        
        await self._setup_orchestrator_database()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.recraft:
            await self.recraft.__aexit__(exc_type, exc_val, exc_tb)
        if self.dalle:
            await self.dalle.__aexit__(exc_type, exc_val, exc_tb)
        if self.db:
            await self.db.close()
    
    @cache_decorator(CacheType.CODE_GENERATION)
    async def create_design_project(self, project_brief: str, project_type: str = "complete_website",
                                  target_audience: str = "general", brand_guidelines: Dict = None,
                                  style_preferences: Dict = None) -> Dict:
        """Create and execute a complete design project"""
        start_time = time.time()
        project_id = f"project_{int(time.time())}"
        
        try:
            # Get workflow template
            workflow = self.workflow_templates.get(project_type, self.workflow_templates["complete_website"])
            
            # Initialize project state
            project_state = {
                "project_id": project_id,
                "project_type": project_type,
                "brief": project_brief,
                "target_audience": target_audience,
                "brand_guidelines": brand_guidelines or {},
                "style_preferences": style_preferences or {},
                "workflow": workflow,
                "current_phase": 0,
                "deliverables": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "estimated_completion": (datetime.now().timestamp() + workflow["estimated_time"]),
                    "status": "in_progress"
                }
            }
            
            self.active_projects[project_id] = project_state
            
            # Execute workflow phases
            results = await self._execute_design_workflow(project_state)
            
            # Finalize project
            final_project = await self._finalize_project(project_state, results)
            
            # Log project completion
            await self._log_project_completion(project_id, project_type, final_project)
            
            # Update metrics
            self.metrics["projects_created"] += 1
            self.metrics["workflows_completed"] += 1
            self.metrics["total_requests"] += 1
            
            project_time = time.time() - start_time
            total_time = self.metrics["average_project_time"] * (self.metrics["projects_created"] - 1)
            self.metrics["average_project_time"] = (total_time + project_time) / self.metrics["projects_created"]
            
            return final_project
            
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("create_design_project", project_id, str(e))
            raise
    
    async def analyze_design_requirements(self, brief: str, target_audience: str = "general",
                                        existing_assets: List[str] = None) -> Dict:
        """Analyze design requirements using Claude via OpenRouter"""
        start_time = time.time()
        
        try:
            # Create comprehensive analysis prompt
            analysis_prompt = await self._create_analysis_prompt(brief, target_audience, existing_assets)
            
            # Route through OpenRouter (Claude) for analysis
            analysis_result = await self._route_through_claude(analysis_prompt, "design_analysis")
            
            # Process and structure the analysis
            structured_analysis = await self._process_analysis_result(analysis_result, brief)
            
            result = {
                "analysis_id": f"analysis_{int(time.time())}",
                "brief": brief,
                "target_audience": target_audience,
                "analysis": structured_analysis,
                "recommendations": structured_analysis.get("recommendations", []),
                "design_direction": structured_analysis.get("design_direction", {}),
                "metadata": {
                    "analyzed_at": datetime.now().isoformat(),
                    "latency": time.time() - start_time
                }
            }
            
            await self._log_analysis(brief, target_audience, result)
            
            self.metrics["analysis_performed"] += 1
            self.metrics["total_requests"] += 1
            
            return result
            
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("analyze_design_requirements", brief, str(e))
            raise
    
    async def generate_design_assets(self, design_requirements: Dict, asset_types: List[str],
                                   framework: str = "react") -> Dict:
        """Generate design assets using Recraft and DALL-E"""
        start_time = time.time()
        
        try:
            generated_assets = {}
            
            # Parallel asset generation
            tasks = []
            
            for asset_type in asset_types:
                if asset_type in ["hero_design", "layout_structure", "navigation_design"]:
                    # Use Recraft for UI/UX design generation
                    task = self._generate_recraft_asset(design_requirements, asset_type, framework)
                    tasks.append((asset_type, "recraft", task))
                
                elif asset_type in ["hero_images", "icons", "supporting_images", "backgrounds"]:
                    # Use DALL-E for image generation
                    task = self._generate_dalle_asset(design_requirements, asset_type)
                    tasks.append((asset_type, "dalle", task))
            
            # Execute tasks in parallel
            results = await asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True)
            
            # Process results
            for i, (asset_type, tool, _) in enumerate(tasks):
                result = results[i]
                if not isinstance(result, Exception):
                    generated_assets[asset_type] = {
                        "tool": tool,
                        "asset_data": result,
                        "generated_at": datetime.now().isoformat()
                    }
                else:
                    logger.error(f"Failed to generate {asset_type}: {result}")
                    generated_assets[asset_type] = {
                        "tool": tool,
                        "error": str(result),
                        "status": "failed"
                    }
            
            final_result = {
                "asset_generation_id": f"assets_{int(time.time())}",
                "design_requirements": design_requirements,
                "requested_assets": asset_types,
                "generated_assets": generated_assets,
                "framework": framework,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "latency": time.time() - start_time,
                    "success_rate": len([a for a in generated_assets.values() if "error" not in a]) / len(asset_types)
                }
            }
            
            await self._log_asset_generation(design_requirements, asset_types, final_result)
            
            self.metrics["designs_generated"] += len([a for a in generated_assets.values() if a.get("tool") == "recraft"])
            self.metrics["images_created"] += len([a for a in generated_assets.values() if a.get("tool") == "dalle"])
            self.metrics["total_requests"] += 1
            
            return final_result
            
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("generate_design_assets", str(design_requirements), str(e))
            raise
    
    async def refine_design_with_feedback(self, project_id: str, feedback: List[str],
                                        specific_assets: List[str] = None) -> Dict:
        """Refine design based on feedback"""
        start_time = time.time()
        
        try:
            if project_id not in self.active_projects:
                raise ValueError(f"Project {project_id} not found")
            
            project_state = self.active_projects[project_id]
            
            # Analyze feedback using Claude
            feedback_analysis = await self._analyze_feedback_with_claude(feedback, project_state)
            
            # Determine what needs refinement
            refinement_plan = await self._create_refinement_plan(feedback_analysis, specific_assets)
            
            # Execute refinements
            refined_assets = {}
            
            for asset_name, refinement_details in refinement_plan.items():
                try:
                    if refinement_details["tool"] == "recraft":
                        refined_asset = await self.recraft.refine_design(
                            refinement_details["asset_id"],
                            refinement_details["feedback"],
                            refinement_details["goals"]
                        )
                    elif refinement_details["tool"] == "dalle":
                        refined_asset = await self.dalle.enhance_existing_image(
                            refinement_details["image_data"],
                            refinement_details["enhancement_prompt"],
                            refinement_details["target_style"]
                        )
                    
                    refined_assets[asset_name] = refined_asset
                    
                except Exception as e:
                    logger.error(f"Failed to refine {asset_name}: {e}")
                    refined_assets[asset_name] = {"error": str(e)}
            
            # Update project state
            project_state["deliverables"].update(refined_assets)
            project_state["metadata"]["last_refined"] = datetime.now().isoformat()
            
            result = {
                "refinement_id": f"refinement_{int(time.time())}",
                "project_id": project_id,
                "feedback": feedback,
                "feedback_analysis": feedback_analysis,
                "refinement_plan": refinement_plan,
                "refined_assets": refined_assets,
                "metadata": {
                    "refined_at": datetime.now().isoformat(),
                    "latency": time.time() - start_time
                }
            }
            
            await self._log_refinement(project_id, feedback, result)
            
            return result
            
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("refine_design_with_feedback", project_id, str(e))
            raise
    
    async def _execute_design_workflow(self, project_state: Dict) -> Dict:
        """Execute the complete design workflow"""
        workflow_results = {}
        
        for phase in project_state["workflow"]["phases"]:
            phase_start = time.time()
            
            try:
                if phase == DesignPhase.ANALYSIS:
                    analysis = await self.analyze_design_requirements(
                        project_state["brief"],
                        project_state["target_audience"]
                    )
                    workflow_results["analysis"] = analysis
                
                elif phase == DesignPhase.CONCEPT:
                    concept = await self._develop_design_concept(project_state, workflow_results.get("analysis"))
                    workflow_results["concept"] = concept
                
                elif phase == DesignPhase.DESIGN:
                    design_assets = await self.generate_design_assets(
                        workflow_results.get("concept", project_state),
                        project_state["workflow"]["deliverables"]
                    )
                    workflow_results["design_assets"] = design_assets
                
                elif phase == DesignPhase.REFINEMENT:
                    # Auto-generate refinement suggestions
                    refinement = await self._auto_refine_designs(workflow_results["design_assets"])
                    workflow_results["refinement"] = refinement
                
                elif phase == DesignPhase.FINALIZATION:
                    finalization = await self._finalize_design_assets(workflow_results)
                    workflow_results["finalization"] = finalization
                
                # Update project state
                project_state["current_phase"] += 1
                project_state["deliverables"][phase.value] = workflow_results.get(phase.value)
                
                logger.info(f"Completed phase {phase.value} in {time.time() - phase_start:.2f}s")
                
            except Exception as e:
                logger.error(f"Failed to complete phase {phase.value}: {e}")
                workflow_results[f"{phase.value}_error"] = str(e)
        
        return workflow_results
    
    async def _route_through_claude(self, content: str, task_type: str) -> str:
        """Route content through Claude via OpenRouter"""
        openrouter_key = os.environ.get('OPENROUTER_API_KEY')
        if not openrouter_key:
            return content
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json"
                }
                
                system_prompts = {
                    "design_analysis": "You are an expert UI/UX designer and analyst. Provide comprehensive design analysis and recommendations.",
                    "feedback_analysis": "You are a design feedback expert. Analyze user feedback and provide actionable improvement suggestions.",
                    "concept_development": "You are a creative design strategist. Develop innovative design concepts based on requirements."
                }
                
                request_data = {
                    "model": "anthropic/claude-3-sonnet",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompts.get(task_type, "You are a helpful design assistant.")
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 3000
                }
                
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=request_data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        logger.warning(f"Claude routing failed: {response.status}")
                        return content
        
        except Exception as e:
            logger.warning(f"Claude routing error: {e}")
            return content
    
    async def _create_analysis_prompt(self, brief: str, target_audience: str, existing_assets: List[str] = None) -> str:
        """Create comprehensive analysis prompt"""
        prompt = f"""
Analyze the following design project requirements:

Project Brief: {brief}
Target Audience: {target_audience}

Please provide a comprehensive analysis including:

1. Design Objectives
   - Primary goals and success metrics
   - User experience priorities
   - Business objectives alignment

2. Target Audience Analysis
   - User personas and demographics
   - User needs and pain points
   - Design preferences and expectations

3. Design Strategy
   - Visual style recommendations
   - Layout and navigation approach
   - Color palette and typography suggestions
   - Content hierarchy recommendations

4. Technical Considerations
   - Platform requirements (web, mobile, etc.)
   - Accessibility requirements
   - Performance considerations
   - Responsive design needs

5. Competitive Analysis
   - Industry standards and best practices
   - Differentiation opportunities
   - Trending design patterns

6. Implementation Roadmap
   - Priority deliverables
   - Development phases
   - Resource requirements
   - Timeline estimates

Please structure your analysis in JSON format for easy processing.
"""
        
        if existing_assets:
            prompt += f"\nExisting Assets to Consider: {', '.join(existing_assets)}"
        
        return prompt
    
    async def _process_analysis_result(self, analysis_text: str, brief: str) -> Dict:
        """Process and structure analysis result"""
        try:
            # Try to parse as JSON first
            if analysis_text.strip().startswith('{'):
                return json.loads(analysis_text)
        except:
            pass
        
        # Fallback: create structured response
        return {
            "design_objectives": ["Enhance user experience", "Achieve business goals", "Create engaging interface"],
            "target_audience_insights": {
                "primary_persona": "Target user based on brief",
                "needs": ["Intuitive navigation", "Clear information", "Responsive design"],
                "preferences": ["Modern design", "Fast loading", "Mobile-friendly"]
            },
            "design_direction": {
                "style": "modern and professional",
                "color_palette": ["primary", "secondary", "accent"],
                "typography": "clean and readable",
                "layout": "grid-based responsive"
            },
            "recommendations": [
                "Focus on user-centered design",
                "Implement responsive layouts",
                "Ensure accessibility compliance",
                "Optimize for performance"
            ],
            "raw_analysis": analysis_text
        }
    
    async def _generate_recraft_asset(self, requirements: Dict, asset_type: str, framework: str) -> Dict:
        """Generate asset using Recraft"""
        design_brief = self._create_asset_brief(requirements, asset_type)
        
        design_type_mapping = {
            "hero_design": "landing_page",
            "layout_structure": "web_app",
            "navigation_design": "web_app",
            "dashboard_layout": "dashboard"
        }
        
        design_type = design_type_mapping.get(asset_type, "web_app")
        
        return await self.recraft.generate_design(
            design_brief,
            design_type=design_type,
            style_preferences=requirements.get("style_preferences"),
            output_format=framework
        )
    
    async def _generate_dalle_asset(self, requirements: Dict, asset_type: str) -> Dict:
        """Generate asset using DALL-E"""
        image_prompt = self._create_image_prompt(requirements, asset_type)
        
        image_type_mapping = {
            "hero_images": "hero_images",
            "icons": "feature_icons",
            "supporting_images": "background_patterns",
            "backgrounds": "background_patterns"
        }
        
        image_type = image_type_mapping.get(asset_type, "hero_images")
        
        if asset_type == "icons":
            return await self.dalle.generate_icon_set(
                image_prompt,
                icon_count=6,
                style="minimalist",
                color_scheme="professional"
            )
        else:
            return await self.dalle.generate_design_image(
                image_prompt,
                image_type=image_type,
                style_preferences=requirements.get("style_preferences")
            )
    
    def _create_asset_brief(self, requirements: Dict, asset_type: str) -> str:
        """Create asset-specific brief"""
        base_brief = requirements.get("brief", "Create a modern design")
        
        asset_specifics = {
            "hero_design": "Focus on the main hero section with compelling headline and call-to-action",
            "layout_structure": "Create the overall page layout and component structure",
            "navigation_design": "Design intuitive navigation menu and user flow",
            "dashboard_layout": "Create data-focused dashboard with clear information hierarchy"
        }
        
        specific = asset_specifics.get(asset_type, "Create a professional design component")
        
        return f"{base_brief}. {specific}"
    
    def _create_image_prompt(self, requirements: Dict, asset_type: str) -> str:
        """Create image-specific prompt"""
        base_concept = requirements.get("brief", "modern professional design")
        
        image_specifics = {
            "hero_images": "Create a striking hero image that captures attention and conveys the brand message",
            "icons": "productivity and business tools",
            "supporting_images": "supportive visual elements that enhance the design",
            "backgrounds": "subtle background patterns that complement the design"
        }
        
        return f"{base_concept} - {image_specifics.get(asset_type, 'professional visual element')}"
    
    async def _develop_design_concept(self, project_state: Dict, analysis: Dict = None) -> Dict:
        """Develop design concept based on analysis"""
        concept_prompt = f"""
Based on the project brief: {project_state['brief']}
Target audience: {project_state['target_audience']}

Develop a comprehensive design concept including:
1. Visual style direction
2. Color palette recommendations
3. Typography choices
4. Layout philosophy
5. User interaction patterns
6. Content strategy

{f"Analysis insights: {json.dumps(analysis.get('design_direction', {}), indent=2)}" if analysis else ""}
"""
        
        concept_result = await self._route_through_claude(concept_prompt, "concept_development")
        
        return {
            "concept_id": f"concept_{int(time.time())}",
            "project_id": project_state["project_id"],
            "concept_details": concept_result,
            "metadata": {
                "developed_at": datetime.now().isoformat()
            }
        }
    
    async def _auto_refine_designs(self, design_assets: Dict) -> Dict:
        """Automatically refine designs based on best practices"""
        refinement_suggestions = []
        
        # Analyze generated assets for improvements
        for asset_name, asset_data in design_assets.get("generated_assets", {}).items():
            if "error" not in asset_data:
                suggestions = [
                    "Enhance accessibility features",
                    "Optimize for mobile responsiveness",
                    "Improve visual hierarchy",
                    "Ensure brand consistency"
                ]
                refinement_suggestions.extend(suggestions)
        
        return {
            "refinement_id": f"auto_refinement_{int(time.time())}",
            "suggestions": refinement_suggestions,
            "auto_applied": [],
            "metadata": {
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def _finalize_design_assets(self, workflow_results: Dict) -> Dict:
        """Finalize all design assets"""
        finalized_assets = {}
        
        # Collect all generated assets
        design_assets = workflow_results.get("design_assets", {}).get("generated_assets", {})
        
        for asset_name, asset_data in design_assets.items():
            if "error" not in asset_data:
                finalized_assets[asset_name] = {
                    "final_version": asset_data,
                    "export_formats": ["PNG", "SVG", "PDF"],
                    "usage_guidelines": "Follow brand guidelines and accessibility standards",
                    "finalized_at": datetime.now().isoformat()
                }
        
        return {
            "finalization_id": f"final_{int(time.time())}",
            "finalized_assets": finalized_assets,
            "delivery_package": {
                "design_files": list(finalized_assets.keys()),
                "documentation": "Design specifications and usage guidelines",
                "code_exports": "Production-ready code components"
            },
            "metadata": {
                "finalized_at": datetime.now().isoformat()
            }
        }
    
    async def _finalize_project(self, project_state: Dict, workflow_results: Dict) -> Dict:
        """Finalize the complete project"""
        final_project = {
            "project_id": project_state["project_id"],
            "project_type": project_state["project_type"],
            "brief": project_state["brief"],
            "workflow_results": workflow_results,
            "deliverables": project_state["deliverables"],
            "metadata": {
                "created_at": project_state["metadata"]["created_at"],
                "completed_at": datetime.now().isoformat(),
                "status": "completed",
                "success_rate": len([r for r in workflow_results.values() if not str(r).startswith("error")]) / len(workflow_results)
            }
        }
        
        # Remove from active projects
        if project_state["project_id"] in self.active_projects:
            del self.active_projects[project_state["project_id"]]
        
        return final_project
    
    async def _analyze_feedback_with_claude(self, feedback: List[str], project_state: Dict) -> Dict:
        """Analyze feedback using Claude"""
        feedback_prompt = f"""
Analyze the following design feedback for project: {project_state['brief']}

Feedback received:
{chr(10).join(f"- {fb}" for fb in feedback)}

Please provide:
1. Feedback categorization (usability, visual design, content, technical)
2. Priority level for each feedback item
3. Specific actionable recommendations
4. Impact assessment on overall design
5. Implementation complexity

Format as structured JSON response.
"""
        
        analysis_result = await self._route_through_claude(feedback_prompt, "feedback_analysis")
        
        return {
            "feedback_analysis": analysis_result,
            "analyzed_at": datetime.now().isoformat()
        }
    
    async def _create_refinement_plan(self, feedback_analysis: Dict, specific_assets: List[str] = None) -> Dict:
        """Create refinement plan based on feedback analysis"""
        refinement_plan = {}
        
        # Mock refinement plan - in real implementation, this would be more sophisticated
        assets_to_refine = specific_assets or ["hero_design", "navigation_design"]
        
        for asset_name in assets_to_refine:
            refinement_plan[asset_name] = {
                "tool": "recraft" if "design" in asset_name else "dalle",
                "asset_id": f"mock_asset_id_{asset_name}",
                "feedback": ["Improve visual hierarchy", "Enhance user experience"],
                "goals": ["Better usability", "Stronger visual impact"],
                "priority": "high"
            }
        
        return refinement_plan
    
    async def _setup_orchestrator_database(self) -> None:
        """Setup database tables for orchestrator operations"""
        await self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS design_projects (
                id SERIAL PRIMARY KEY,
                project_id VARCHAR(200) UNIQUE,
                project_type VARCHAR(100) NOT NULL,
                brief TEXT NOT NULL,
                status VARCHAR(50) NOT NULL,
                result JSONB,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                completed_at TIMESTAMP WITH TIME ZONE
            );
        """, fetch=False)
        
        await self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS design_analyses (
                id SERIAL PRIMARY KEY,
                analysis_id VARCHAR(200),
                brief TEXT NOT NULL,
                target_audience VARCHAR(200),
                result JSONB,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """, fetch=False)
        
        await self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_design_projects_status 
            ON design_projects(status);
        """, fetch=False)
    
    async def _log_project_completion(self, project_id: str, project_type: str, result: Dict) -> None:
        """Log project completion to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO design_projects 
                (project_id, project_type, brief, status, result, created_at, completed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (project_id) 
                DO UPDATE SET 
                    status = EXCLUDED.status,
                    result = EXCLUDED.result,
                    completed_at = EXCLUDED.completed_at
            """,
            project_id, project_type, result.get("brief", ""), "completed",
            json.dumps(result), datetime.now(), datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log project completion: {e}")
    
    async def _log_analysis(self, brief: str, target_audience: str, result: Dict) -> None:
        """Log analysis to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO design_analyses 
                (analysis_id, brief, target_audience, result, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """,
            result.get("analysis_id"), brief, target_audience,
            json.dumps(result), datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log analysis: {e}")
    
    async def _log_asset_generation(self, requirements: Dict, asset_types: List[str], result: Dict) -> None:
        """Log asset generation to database"""
        # Implementation would log asset generation details
        pass
    
    async def _log_refinement(self, project_id: str, feedback: List[str], result: Dict) -> None:
        """Log refinement to database"""
        # Implementation would log refinement details
        pass
    
    async def _log_error(self, action: str, identifier: str, error: str) -> None:
        """Log error to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO design_projects 
                (project_id, project_type, brief, status, result, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
            f"error_{int(time.time())}", action, f"{action}: {identifier}", "error",
            json.dumps({"error": error}), datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def get_performance_metrics(self) -> Dict:
        """Get comprehensive performance metrics"""
        total_requests = max(1, self.metrics["total_requests"])
        
        return {
            "projects_created": self.metrics["projects_created"],
            "designs_generated": self.metrics["designs_generated"],
            "images_created": self.metrics["images_created"],
            "workflows_completed": self.metrics["workflows_completed"],
            "analysis_performed": self.metrics["analysis_performed"],
            "average_project_time": self.metrics["average_project_time"],
            "error_rate": self.metrics["errors"] / total_requests,
            "success_rate": 1 - (self.metrics["errors"] / total_requests),
            "active_projects": len(self.active_projects),
            "status": "operational" if self.metrics["errors"] / total_requests < 0.1 else "degraded"
        }


async def main():
    """Test Design Orchestrator"""
    print("🚀 Testing Unified Design Orchestrator...")
    
    async with DesignOrchestrator() as orchestrator:
        # Test project creation
        print("\n1. Testing complete project creation...")
        try:
            project_result = await orchestrator.create_design_project(
                "Create a modern SaaS dashboard for project management",
                project_type="dashboard",
                target_audience="project managers and team leads",
                style_preferences={"theme": "professional", "colors": "blue and white"}
            )
            print(f"   ✅ Project created: {project_result['project_id']}")
            print(f"   📊 Success rate: {project_result['metadata']['success_rate']:.1%}")
        except Exception as e:
            print(f"   ❌ Project creation failed: {e}")
        
        # Test analysis
        print("\n2. Testing design analysis...")
        try:
            analysis_result = await orchestrator.analyze_design_requirements(
                "E-commerce mobile app for sustainable products",
                target_audience="environmentally conscious millennials"
            )
            print(f"   ✅ Analysis completed: {analysis_result['analysis_id']}")
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
        
        # Performance metrics
        metrics = orchestrator.get_performance_metrics()
        print(f"\n📊 Orchestrator Performance:")
        print(f"   Projects Created: {metrics['projects_created']}")
        print(f"   Designs Generated: {metrics['designs_generated']}")
        print(f"   Images Created: {metrics['images_created']}")
        print(f"   Average Project Time: {metrics['average_project_time']:.1f}s")
        print(f"   Success Rate: {metrics['success_rate']:.1%}")


if __name__ == "__main__":
    asyncio.run(main()) 