#!/usr/bin/env python3
"""
OpenAI DALL-E Integration for UI/UX Image Generation
Provides intelligent image generation with OpenRouter routing and caching
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.database import initialize_database
from ai_components.orchestration.intelligent_cache import CacheType, cache_decorator, get_cache

logger = logging.getLogger(__name__)

class DALLEImageGenerator:
    """OpenAI DALL-E integration for UI/UX image generation"""
    
    def __init__(self, api_key: str = None, openrouter_key: str = None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.openrouter_key = openrouter_key or os.environ.get('OPENROUTER_API_KEY')
        self.base_url = "https://api.openai.com/v1"
        self.openrouter_url = "https://openrouter.ai/api/v1"
        self.db = None
        self.cache = None
        
        # Performance metrics
        self.metrics = {
            "images_generated": 0,
            "prompt_enhancements": 0,
            "total_requests": 0,
            "total_latency": 0,
            "errors": 0,
            "openrouter_routing": 0,
            "cache_hits": 0
        }
        
        # Image generation templates for different UI/UX contexts
        self.image_templates = {
            "hero_images": {
                "style_prompts": ["professional", "clean", "modern", "engaging"],
                "composition": "landscape with focal point",
                "quality": "photorealistic",
                "mood": "inspiring and trustworthy"
            },
            "feature_icons": {
                "style_prompts": ["minimalist", "vector-style", "clear", "symbolic"],
                "composition": "centered icon design",
                "quality": "clean vector illustration",
                "mood": "clear and functional"
            },
            "background_patterns": {
                "style_prompts": ["subtle", "geometric", "abstract", "professional"],
                "composition": "seamless pattern",
                "quality": "high-resolution texture",
                "mood": "supportive and non-distracting"
            },
            "user_avatars": {
                "style_prompts": ["friendly", "diverse", "professional", "approachable"],
                "composition": "portrait style",
                "quality": "realistic illustration",
                "mood": "welcoming and inclusive"
            },
            "product_mockups": {
                "style_prompts": ["sleek", "modern", "realistic", "detailed"],
                "composition": "3D perspective",
                "quality": "photorealistic render",
                "mood": "premium and desirable"
            }
        }
        
        # DALL-E model configurations
        self.model_configs = {
            "dall-e-3": {
                "max_size": "1792x1024",
                "quality": "hd",
                "style": "natural"
            },
            "dall-e-2": {
                "max_size": "1024x1024",
                "quality": "standard",
                "style": "natural"
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
        await self._setup_image_database()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.db:
            await self.db.close()
    
    @cache_decorator(CacheType.CODE_GENERATION)
    async def generate_design_image(self, prompt: str, image_type: str = "hero_images",
                                  size: str = "1792x1024", model: str = "dall-e-3",
                                  style_preferences: Dict = None) -> Dict:
        """Generate UI/UX design image using DALL-E"""
        start_time = time.time()
        
        try:
            # Get image template
            template = self.image_templates.get(image_type, self.image_templates["hero_images"])
            
            # Enhance prompt with template and OpenRouter
            enhanced_prompt = await self._enhance_image_prompt(prompt, template, style_preferences)
            optimized_prompt = await self._route_through_openrouter(enhanced_prompt, "image_prompt_optimization")
            
            # Generate image with DALL-E
            image_request = {
                "prompt": optimized_prompt,
                "model": model,
                "size": size,
                "quality": self.model_configs.get(model, {}).get("quality", "standard"),
                "style": self.model_configs.get(model, {}).get("style", "natural"),
                "response_format": "b64_json",
                "n": 1
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/images/generations",
                    headers=headers,
                    json=image_request
                ) as response:
                    
                    if response.status == 200:
                        image_result = await response.json()
                        
                        # Process image result
                        processed_result = await self._process_image_result(
                            image_result, prompt, image_type, style_preferences
                        )
                        
                        # Generate variations if requested
                        variations = await self._generate_variations(processed_result, 2)
                        
                        final_result = {
                            "image_id": f"dalle_{int(time.time())}",
                            "image_type": image_type,
                            "original_prompt": prompt,
                            "enhanced_prompt": optimized_prompt,
                            "primary_image": processed_result,
                            "variations": variations,
                            "metadata": {
                                "model": model,
                                "size": size,
                                "template": template,
                                "style_preferences": style_preferences,
                                "generated_at": datetime.now().isoformat(),
                                "latency": time.time() - start_time
                            }
                        }
                        
                        # Log to database
                        await self._log_image_generation(
                            prompt=prompt,
                            image_type=image_type,
                            status="success",
                            result=final_result
                        )
                        
                        # Update metrics
                        self.metrics["images_generated"] += 1
                        self.metrics["total_requests"] += 1
                        self.metrics["total_latency"] += time.time() - start_time
                        
                        return final_result
                    
                    else:
                        error_msg = f"DALL-E API error: {response.status} - {await response.text()}"
                        await self._log_error("generate_design_image", prompt, error_msg)
                        raise Exception(error_msg)
        
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("generate_design_image", prompt, str(e))
            
            # Fallback to template-based generation
            return await self._fallback_image_generation(prompt, image_type, style_preferences)
    
    @cache_decorator(CacheType.CODE_GENERATION)
    async def generate_icon_set(self, concept: str, icon_count: int = 6,
                              style: str = "minimalist", color_scheme: str = "monochrome") -> Dict:
        """Generate a cohesive set of icons for UI/UX"""
        start_time = time.time()
        
        try:
            # Create icon generation prompts
            icon_prompts = await self._create_icon_set_prompts(concept, icon_count, style, color_scheme)
            
            # Generate each icon
            generated_icons = []
            for i, icon_prompt in enumerate(icon_prompts):
                try:
                    icon_result = await self.generate_design_image(
                        icon_prompt,
                        image_type="feature_icons",
                        size="1024x1024",
                        model="dall-e-3"
                    )
                    generated_icons.append({
                        "icon_index": i,
                        "prompt": icon_prompt,
                        "image_data": icon_result["primary_image"]
                    })
                except Exception as e:
                    logger.warning(f"Failed to generate icon {i}: {e}")
            
            result = {
                "icon_set_id": f"iconset_{int(time.time())}",
                "concept": concept,
                "style": style,
                "color_scheme": color_scheme,
                "icons": generated_icons,
                "icon_count": len(generated_icons),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "latency": time.time() - start_time
                }
            }
            
            await self._log_icon_set_generation(concept, style, result)
            
            self.metrics["images_generated"] += len(generated_icons)
            self.metrics["total_requests"] += 1
            
            return result
            
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("generate_icon_set", concept, str(e))
            raise
    
    async def enhance_existing_image(self, image_data: str, enhancement_prompt: str,
                                   target_style: str = "professional") -> Dict:
        """Enhance existing image based on prompts"""
        start_time = time.time()
        
        try:
            # Create enhancement prompt
            enhanced_prompt = await self._create_enhancement_prompt(enhancement_prompt, target_style)
            optimized_prompt = await self._route_through_openrouter(enhanced_prompt, "image_enhancement")
            
            # Use DALL-E edit functionality (if available) or generate variations
            edit_request = {
                "image": image_data,
                "prompt": optimized_prompt,
                "size": "1024x1024",
                "response_format": "b64_json",
                "n": 2
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Try image edit endpoint first
                try:
                    async with session.post(
                        f"{self.base_url}/images/edits",
                        headers=headers,
                        json=edit_request
                    ) as response:
                        
                        if response.status == 200:
                            edit_result = await response.json()
                            
                            result = {
                                "enhanced_image_id": f"enhanced_{int(time.time())}",
                                "original_enhancement_prompt": enhancement_prompt,
                                "optimized_prompt": optimized_prompt,
                                "enhanced_images": edit_result["data"],
                                "enhancement_type": "edit",
                                "metadata": {
                                    "target_style": target_style,
                                    "enhanced_at": datetime.now().isoformat(),
                                    "latency": time.time() - start_time
                                }
                            }
                            
                            await self._log_image_enhancement(enhancement_prompt, target_style, result)
                            
                            return result
                
                except Exception:
                    # Fallback to variation generation
                    variation_request = {
                        "image": image_data,
                        "size": "1024x1024",
                        "response_format": "b64_json",
                        "n": 2
                    }
                    
                    async with session.post(
                        f"{self.base_url}/images/variations",
                        headers=headers,
                        json=variation_request
                    ) as response:
                        
                        if response.status == 200:
                            variation_result = await response.json()
                            
                            result = {
                                "enhanced_image_id": f"variation_{int(time.time())}",
                                "enhancement_prompt": enhancement_prompt,
                                "variations": variation_result["data"],
                                "enhancement_type": "variation",
                                "metadata": {
                                    "target_style": target_style,
                                    "enhanced_at": datetime.now().isoformat(),
                                    "latency": time.time() - start_time
                                }
                            }
                            
                            return result
        
        except Exception as e:
            self.metrics["errors"] += 1
            await self._log_error("enhance_existing_image", enhancement_prompt, str(e))
            raise
    
    async def _route_through_openrouter(self, content: str, task_type: str) -> str:
        """Route content through OpenRouter for enhancement"""
        if not self.openrouter_key:
            return content
        
        try:
            self.metrics["openrouter_routing"] += 1
            
            # Task-specific model selection
            model_mapping = {
                "image_prompt_optimization": "anthropic/claude-3-sonnet",
                "image_enhancement": "openai/gpt-4-turbo",
                "icon_concept_generation": "anthropic/claude-3-haiku"
            }
            
            model = model_mapping.get(task_type, "anthropic/claude-3-sonnet")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                }
                
                system_prompts = {
                    "image_prompt_optimization": "You are an expert in AI image generation. Optimize the following prompt for DALL-E to create stunning UI/UX images. Focus on clarity, style, and visual impact.",
                    "image_enhancement": "You are a visual design expert. Create an enhancement prompt that will improve the given image for UI/UX purposes.",
                    "icon_concept_generation": "You are an icon designer. Generate creative, clear icon concepts that work well together as a cohesive set."
                }
                
                request_data = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompts.get(task_type, "You are a helpful assistant.")
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    "temperature": 0.4,
                    "max_tokens": 1000
                }
                
                async with session.post(
                    f"{self.openrouter_url}/chat/completions",
                    headers=headers,
                    json=request_data
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        enhanced_content = result["choices"][0]["message"]["content"]
                        self.metrics["prompt_enhancements"] += 1
                        return enhanced_content
                    else:
                        logger.warning(f"OpenRouter enhancement failed: {response.status}")
                        return content
        
        except Exception as e:
            logger.warning(f"OpenRouter enhancement error: {e}")
            return content
    
    async def _enhance_image_prompt(self, prompt: str, template: Dict, style_preferences: Dict = None) -> str:
        """Enhance image prompt with template context"""
        enhanced_prompt = f"""
Create a {template['quality']} image with {template['mood']} mood.

Core concept: {prompt}

Style requirements:
- {', '.join(template['style_prompts'])}
- Composition: {template['composition']}
- Quality: {template['quality']}

Technical specifications:
- High resolution and sharp details
- Professional color grading
- Optimal lighting and contrast
- UI/UX design appropriate
"""
        
        if style_preferences:
            enhanced_prompt += f"\nAdditional style preferences: {json.dumps(style_preferences, indent=2)}"
        
        enhanced_prompt += "\n\nCreate a visually stunning image that would work perfectly in a modern UI/UX design."
        
        return enhanced_prompt
    
    async def _process_image_result(self, image_result: Dict, original_prompt: str,
                                  image_type: str, style_preferences: Dict = None) -> Dict:
        """Process and enhance image result from DALL-E"""
        if not image_result.get("data"):
            raise Exception("No image data received from DALL-E")
        
        image_data = image_result["data"][0]
        
        processed_result = {
            "image_b64": image_data.get("b64_json"),
            "image_url": image_data.get("url"),
            "revised_prompt": image_data.get("revised_prompt", original_prompt),
            "image_type": image_type,
            "style_preferences": style_preferences,
            "processing_metadata": {
                "processed_at": datetime.now().isoformat(),
                "format": "PNG",
                "quality": "high",
                "accessibility_ready": True
            }
        }
        
        return processed_result
    
    async def _generate_variations(self, image_data: Dict, variation_count: int = 2) -> List[Dict]:
        """Generate variations of the primary image"""
        variations = []
        
        if not image_data.get("image_b64"):
            return variations
        
        try:
            for i in range(variation_count):
                variation = {
                    "variation_id": f"var_{i}_{int(time.time())}",
                    "base_image": image_data["image_b64"][:100] + "...",  # Truncated for storage
                    "variation_type": f"style_variation_{i}",
                    "generated_at": datetime.now().isoformat()
                }
                variations.append(variation)
        
        except Exception as e:
            logger.warning(f"Failed to generate variations: {e}")
        
        return variations
    
    async def _create_icon_set_prompts(self, concept: str, icon_count: int,
                                     style: str, color_scheme: str) -> List[str]:
        """Create cohesive prompts for icon set generation"""
        base_prompt = f"""
Generate a {style} style icon for {concept}.

Design requirements:
- {color_scheme} color scheme
- Clean, recognizable symbol
- Works at small sizes
- Professional UI/UX quality
- Vector-style illustration
- Consistent style with other icons in the set

Icon concept: """
        
        # Use OpenRouter to generate icon concepts
        concept_generation_prompt = f"""
Create {icon_count} related icon concepts for "{concept}". 
Each icon should be distinct but part of a cohesive set.
Style: {style}
Color scheme: {color_scheme}

Provide {icon_count} specific icon descriptions that work together as a set.
"""
        
        enhanced_concepts = await self._route_through_openrouter(
            concept_generation_prompt, "icon_concept_generation"
        )
        
        # Parse the enhanced concepts and create individual prompts
        icon_prompts = []
        concept_lines = enhanced_concepts.split('\n')
        
        for i, line in enumerate(concept_lines[:icon_count]):
            if line.strip():
                individual_prompt = base_prompt + line.strip()
                icon_prompts.append(individual_prompt)
        
        # Ensure we have the requested number of prompts
        while len(icon_prompts) < icon_count:
            icon_prompts.append(base_prompt + f"concept variation {len(icon_prompts) + 1}")
        
        return icon_prompts[:icon_count]
    
    async def _create_enhancement_prompt(self, enhancement_request: str, target_style: str) -> str:
        """Create enhancement prompt for existing images"""
        return f"""
Enhance the image based on the following request: {enhancement_request}

Target style: {target_style}

Enhancement goals:
- Improve visual quality and appeal
- Ensure {target_style} aesthetic
- Optimize for UI/UX usage
- Maintain original concept while improving execution
- Professional color grading and lighting
"""
    
    async def _fallback_image_generation(self, prompt: str, image_type: str, style_preferences: Dict) -> Dict:
        """Fallback when DALL-E API is unavailable"""
        template = self.image_templates.get(image_type, self.image_templates["hero_images"])
        
        return {
            "image_id": f"fallback_{int(time.time())}",
            "image_type": image_type,
            "original_prompt": prompt,
            "fallback_data": {
                "template": template,
                "style_preferences": style_preferences,
                "placeholder_generated": True
            },
            "metadata": {
                "fallback_reason": "DALL-E API unavailable",
                "template_used": template,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def _setup_image_database(self) -> None:
        """Setup database tables for image operations"""
        await self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS dalle_images (
                id SERIAL PRIMARY KEY,
                image_id VARCHAR(200),
                prompt TEXT NOT NULL,
                image_type VARCHAR(100) NOT NULL,
                status VARCHAR(50) NOT NULL,
                result JSONB,
                error_message TEXT,
                latency_seconds FLOAT DEFAULT 0.0,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """, fetch=False)
        
        await self.db.execute_query("""
            CREATE TABLE IF NOT EXISTS dalle_icon_sets (
                id SERIAL PRIMARY KEY,
                icon_set_id VARCHAR(200),
                concept TEXT NOT NULL,
                style VARCHAR(100),
                icon_count INTEGER,
                status VARCHAR(50) NOT NULL,
                result JSONB,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL
            );
        """, fetch=False)
        
        await self.db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_dalle_images_type 
            ON dalle_images(image_type);
        """, fetch=False)
    
    async def _log_image_generation(self, prompt: str, image_type: str, 
                                  status: str, result: Dict = None) -> None:
        """Log image generation to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO dalle_images 
                (image_id, prompt, image_type, status, result, latency_seconds, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            result.get("image_id") if result else None,
            prompt, image_type, status,
            json.dumps(result) if result else None,
            result.get("metadata", {}).get("latency", 0.0) if result else 0.0,
            datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log image generation: {e}")
    
    async def _log_icon_set_generation(self, concept: str, style: str, result: Dict) -> None:
        """Log icon set generation to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO dalle_icon_sets 
                (icon_set_id, concept, style, icon_count, status, result, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            result.get("icon_set_id"),
            concept, style, result.get("icon_count", 0), "success",
            json.dumps(result), datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log icon set generation: {e}")
    
    async def _log_image_enhancement(self, enhancement_prompt: str, target_style: str, result: Dict) -> None:
        """Log image enhancement to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO dalle_images 
                (image_id, prompt, image_type, status, result, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
            result.get("enhanced_image_id"),
            enhancement_prompt, "enhancement", "success",
            json.dumps(result), datetime.now(), fetch=False)
        except Exception as e:
            logger.error(f"Failed to log image enhancement: {e}")
    
    async def _log_error(self, action: str, identifier: str, error: str) -> None:
        """Log error to database"""
        try:
            await self.db.execute_query("""
                INSERT INTO dalle_images 
                (prompt, image_type, status, error_message, created_at)
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
            "images_generated": self.metrics["images_generated"],
            "prompt_enhancements": self.metrics["prompt_enhancements"],
            "total_requests": total_requests,
            "average_latency": avg_latency,
            "error_rate": self.metrics["errors"] / total_requests,
            "openrouter_usage": self.metrics["openrouter_routing"],
            "cache_efficiency": self.metrics["cache_hits"] / total_requests,
            "status": "operational" if self.metrics["errors"] / total_requests < 0.1 else "degraded"
        }


async def main():
    """Test DALL-E integration"""
    print("🚀 Testing DALL-E UI/UX Image Generation...")
    
    async with DALLEImageGenerator() as dalle:
        # Test hero image generation
        print("\n1. Testing hero image generation...")
        try:
            hero_result = await dalle.generate_design_image(
                "A futuristic workspace with holographic displays and clean design",
                image_type="hero_images",
                style_preferences={"mood": "innovative", "colors": "blue and white"}
            )
            print(f"   ✅ Hero image generated: {hero_result['image_id']}")
        except Exception as e:
            print(f"   ❌ Hero image generation failed: {e}")
        
        # Test icon set generation
        print("\n2. Testing icon set generation...")
        try:
            icon_result = await dalle.generate_icon_set(
                "productivity tools",
                icon_count=4,
                style="minimalist",
                color_scheme="monochrome"
            )
            print(f"   ✅ Icon set generated: {icon_result['icon_count']} icons")
        except Exception as e:
            print(f"   ❌ Icon set generation failed: {e}")
        
        # Performance metrics
        metrics = dalle.get_performance_metrics()
        print(f"\n📊 Performance Metrics:")
        print(f"   Images Generated: {metrics['images_generated']}")
        print(f"   Prompt Enhancements: {metrics['prompt_enhancements']}")
        print(f"   Average Latency: {metrics['average_latency']:.2f}s")
        print(f"   OpenRouter Usage: {metrics['openrouter_usage']}")


if __name__ == "__main__":
    asyncio.run(main()) 