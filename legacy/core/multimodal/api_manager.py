"""
Multi-Modal API Integration Service
Handles all external API integrations for content creation
"""

import asyncio
import aiohttp
import json
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import base64
from io import BytesIO
from PIL import Image

# API Configuration
MUREKA_API_KEY = "op_mbkpsraqJaxJwogegdQyJcwQKJrUPc9"
VENICE_API_KEY = "C5P0F61_IwoU6kGK2F4RVLT_p_N414oHQ6S5fJWBqP"
STABILITY_API_KEY = "sk-d3ym0y0RKM841TtSRLst4LNcGc5Ke4WMNLnjmKLcLtQqkVy5"
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY', '')  # User to provide

# API Base URLs
MUREKA_BASE_URL = "https://api.mureka.ai/v1"
VENICE_BASE_URL = "https://api.venice.ai/api/v1"
STABILITY_BASE_URL = "https://api.stability.ai/v2beta"
TOGETHER_BASE_URL = "https://api.together.ai/v1"

@dataclass
class CreationRequest:
    """Standard creation request format"""
    type: str  # song, image, video, story, edit
    prompt: str
    parameters: Dict[str, Any]
    persona_context: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class CreationResult:
    """Standard creation result format"""
    id: str
    type: str
    status: str  # processing, completed, failed
    output_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    cost_usd: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str = None
    completed_at: Optional[str] = None

class MultiModalAPIManager:
    """Manages all multi-modal API integrations"""
    
    def __init__(self):
        self.session = None
        self.active_creations = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    # MUREKA MUSIC API INTEGRATION
    async def create_song(self, request: CreationRequest) -> CreationResult:
        """Create a song using Mureka API"""
        creation_id = str(uuid.uuid4())
        
        try:
            # Prepare Mureka request
            mureka_payload = {
                "lyrics": request.parameters.get('lyrics', request.prompt),
                "model": request.parameters.get('model', 'auto'),
                "prompt": request.parameters.get('style', 'melodic, emotional')
            }
            
            # Add reference if provided
            if request.parameters.get('reference_id'):
                mureka_payload["reference_id"] = request.parameters['reference_id']
            
            headers = {
                "Authorization": f"Bearer {MUREKA_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{MUREKA_BASE_URL}/song/generate",
                json=mureka_payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    result = CreationResult(
                        id=creation_id,
                        type="song",
                        status="processing",
                        metadata={
                            "mureka_task_id": data.get("id"),
                            "trace_id": data.get("trace_id"),
                            "model": data.get("model"),
                            "lyrics": mureka_payload["lyrics"][:100] + "..." if len(mureka_payload["lyrics"]) > 100 else mureka_payload["lyrics"],
                            "style": mureka_payload["prompt"]
                        },
                        created_at=datetime.utcnow().isoformat()
                    )
                    
                    # Store for status tracking
                    self.active_creations[creation_id] = {
                        "mureka_task_id": data.get("id"),
                        "type": "song",
                        "result": result
                    }
                    
                    # Start background polling
                    asyncio.create_task(self._poll_mureka_status(creation_id))
                    
                    return result
                    
                else:
                    error_data = await response.json()
                    return CreationResult(
                        id=creation_id,
                        type="song",
                        status="failed",
                        error_message=error_data.get("error", {}).get("message", "Unknown error"),
                        created_at=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            return CreationResult(
                id=creation_id,
                type="song",
                status="failed",
                error_message=str(e),
                created_at=datetime.utcnow().isoformat()
            )
    
    async def _poll_mureka_status(self, creation_id: str):
        """Poll Mureka API for task completion"""
        creation_data = self.active_creations.get(creation_id)
        if not creation_data:
            return
            
        mureka_task_id = creation_data["mureka_task_id"]
        headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}
        
        max_attempts = 60  # 5 minutes with 5-second intervals
        attempt = 0
        
        while attempt < max_attempts:
            try:
                async with self.session.get(
                    f"{MUREKA_BASE_URL}/song/query",
                    params={"id": mureka_task_id},
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status")
                        
                        if status == "completed":
                            # Update result with completion data
                            result = creation_data["result"]
                            result.status = "completed"
                            result.output_url = data.get("output_url")
                            result.completed_at = datetime.utcnow().isoformat()
                            result.metadata.update({
                                "duration_seconds": data.get("duration"),
                                "file_size_mb": data.get("file_size"),
                                "generation_time_ms": data.get("generation_time")
                            })
                            
                            # Estimate cost (placeholder - adjust based on actual pricing)
                            result.cost_usd = 0.10  # $0.10 per song generation
                            
                            break
                            
                        elif status == "failed":
                            result = creation_data["result"]
                            result.status = "failed"
                            result.error_message = data.get("error_message", "Generation failed")
                            break
                            
                await asyncio.sleep(5)  # Poll every 5 seconds
                attempt += 1
                
            except Exception as e:
                print(f"Error polling Mureka status: {e}")
                await asyncio.sleep(5)
                attempt += 1
    
    # VENICE AI IMAGE GENERATION
    async def create_image_venice(self, request: CreationRequest) -> CreationResult:
        """Create uncensored image using Venice AI"""
        creation_id = str(uuid.uuid4())
        
        try:
            # Venice AI uses OpenAI-compatible format
            venice_payload = {
                "prompt": request.prompt,
                "n": 1,
                "size": request.parameters.get('size', '1024x1024'),
                "quality": request.parameters.get('quality', 'standard'),
                "style": request.parameters.get('style', 'natural')
            }
            
            headers = {
                "Authorization": f"Bearer {VENICE_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{VENICE_BASE_URL}/images/generations",
                json=venice_payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    image_data = data.get("data", [{}])[0]
                    
                    return CreationResult(
                        id=creation_id,
                        type="image",
                        status="completed",
                        output_url=image_data.get("url"),
                        metadata={
                            "provider": "venice_ai",
                            "size": venice_payload["size"],
                            "quality": venice_payload["quality"],
                            "style": venice_payload["style"],
                            "prompt": request.prompt,
                            "uncensored": True
                        },
                        cost_usd=0.02,  # Estimated cost
                        created_at=datetime.utcnow().isoformat(),
                        completed_at=datetime.utcnow().isoformat()
                    )
                    
                else:
                    error_data = await response.json()
                    return CreationResult(
                        id=creation_id,
                        type="image",
                        status="failed",
                        error_message=error_data.get("error", {}).get("message", "Unknown error"),
                        created_at=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            return CreationResult(
                id=creation_id,
                type="image",
                status="failed",
                error_message=str(e),
                created_at=datetime.utcnow().isoformat()
            )
    
    # STABILITY AI IMAGE GENERATION
    async def create_image_stability(self, request: CreationRequest) -> CreationResult:
        """Create professional image using Stability AI"""
        creation_id = str(uuid.uuid4())
        
        try:
            # Stability AI v2beta format
            stability_payload = {
                "prompt": request.prompt,
                "aspect_ratio": request.parameters.get('aspect_ratio', '1:1'),
                "model": request.parameters.get('model', 'sd3-large'),
                "output_format": "png"
            }
            
            # Add negative prompt if provided
            if request.parameters.get('negative_prompt'):
                stability_payload["negative_prompt"] = request.parameters['negative_prompt']
            
            headers = {
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with self.session.post(
                f"{STABILITY_BASE_URL}/stable-image/generate/ultra",
                json=stability_payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Stability returns base64 image data
                    image_data = data.get("image")
                    if image_data:
                        # Save image and return URL (in production, upload to CDN)
                        image_url = await self._save_base64_image(image_data, creation_id, "png")
                        
                        return CreationResult(
                            id=creation_id,
                            type="image",
                            status="completed",
                            output_url=image_url,
                            metadata={
                                "provider": "stability_ai",
                                "model": stability_payload["model"],
                                "aspect_ratio": stability_payload["aspect_ratio"],
                                "prompt": request.prompt,
                                "professional": True,
                                "seed": data.get("seed")
                            },
                            cost_usd=0.05,  # Estimated cost
                            created_at=datetime.utcnow().isoformat(),
                            completed_at=datetime.utcnow().isoformat()
                        )
                    
                else:
                    error_data = await response.json()
                    return CreationResult(
                        id=creation_id,
                        type="image",
                        status="failed",
                        error_message=error_data.get("message", "Unknown error"),
                        created_at=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            return CreationResult(
                id=creation_id,
                type="image",
                status="failed",
                error_message=str(e),
                created_at=datetime.utcnow().isoformat()
            )
    
    # TOGETHER AI SERVICES
    async def enhance_search_ranking(self, query: str, results: List[Dict]) -> List[Dict]:
        """Use Together AI rerank models to improve search relevance"""
        if not TOGETHER_API_KEY or not results:
            return results
            
        try:
            # Prepare documents for reranking
            documents = [
                result.get('content', result.get('description', ''))[:500]
                for result in results
            ]
            
            rerank_payload = {
                "model": "BAAI/bge-reranker-v2-m3",
                "query": query,
                "documents": documents,
                "top_k": min(len(documents), 20)
            }
            
            headers = {
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{TOGETHER_BASE_URL}/rerank",
                json=rerank_payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    reranked_results = []
                    
                    for item in data.get("results", []):
                        original_index = item.get("index")
                        relevance_score = item.get("relevance_score", 0)
                        
                        if original_index < len(results):
                            result = results[original_index].copy()
                            result["relevance_score"] = relevance_score
                            result["reranked"] = True
                            reranked_results.append(result)
                    
                    return reranked_results
                    
        except Exception as e:
            print(f"Reranking failed: {e}")
            
        return results
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Together AI"""
        if not TOGETHER_API_KEY:
            return []
            
        try:
            embedding_payload = {
                "model": "BAAI/bge-large-en-v1.5",
                "input": texts
            }
            
            headers = {
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{TOGETHER_BASE_URL}/embeddings",
                json=embedding_payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return [item["embedding"] for item in data.get("data", [])]
                    
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            
        return []
    
    async def create_story(self, request: CreationRequest) -> CreationResult:
        """Create story using Together AI"""
        creation_id = str(uuid.uuid4())
        
        if not TOGETHER_API_KEY:
            return CreationResult(
                id=creation_id,
                type="story",
                status="failed",
                error_message="Together AI API key not configured",
                created_at=datetime.utcnow().isoformat()
            )
        
        try:
            # Prepare story generation prompt
            length_map = {
                "short": "500 words",
                "medium": "1500 words", 
                "long": "3000+ words"
            }
            
            length = request.parameters.get('length', 'short')
            voice = request.parameters.get('voice', 'cherry')
            
            # Persona-specific system prompts
            voice_prompts = {
                "cherry": "Write in a playful, warm, and engaging style with creative flair and emotional depth.",
                "sophia": "Write in a professional, analytical style with clear structure and business insight.",
                "karen": "Write in a precise, clinical style with attention to detail and evidence-based approach."
            }
            
            system_prompt = voice_prompts.get(voice, voice_prompts["cherry"])
            user_prompt = f"Write a {length_map[length]} story about: {request.prompt}"
            
            story_payload = {
                "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 4000,
                "temperature": 0.8
            }
            
            headers = {
                "Authorization": f"Bearer {TOGETHER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{TOGETHER_BASE_URL}/chat/completions",
                json=story_payload,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    story_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    # Save story content (in production, save to database/file storage)
                    story_url = await self._save_story_content(story_content, creation_id)
                    
                    return CreationResult(
                        id=creation_id,
                        type="story",
                        status="completed",
                        output_url=story_url,
                        metadata={
                            "provider": "together_ai",
                            "model": "Meta-Llama-3.1-70B",
                            "length": length,
                            "voice": voice,
                            "word_count": len(story_content.split()),
                            "theme": request.prompt
                        },
                        cost_usd=0.03,  # Estimated cost
                        created_at=datetime.utcnow().isoformat(),
                        completed_at=datetime.utcnow().isoformat()
                    )
                    
                else:
                    error_data = await response.json()
                    return CreationResult(
                        id=creation_id,
                        type="story",
                        status="failed",
                        error_message=error_data.get("error", {}).get("message", "Unknown error"),
                        created_at=datetime.utcnow().isoformat()
                    )
                    
        except Exception as e:
            return CreationResult(
                id=creation_id,
                type="story",
                status="failed",
                error_message=str(e),
                created_at=datetime.utcnow().isoformat()
            )
    
    # UTILITY METHODS
    async def _save_base64_image(self, base64_data: str, creation_id: str, format: str) -> str:
        """Save base64 image data and return URL"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_data))
            
            # Save to local storage (in production, upload to CDN)
            filename = f"{creation_id}.{format}"
            filepath = f"/tmp/generated_images/{filename}"
            
            # Ensure directory exists
            os.makedirs("/tmp/generated_images", exist_ok=True)
            
            image.save(filepath)
            
            # Return URL (in production, return CDN URL)
            return f"https://cdn.cherry-ai.com/generations/{filename}"
            
        except Exception as e:
            print(f"Error saving image: {e}")
            return None
    
    async def _save_story_content(self, content: str, creation_id: str) -> str:
        """Save story content and return URL"""
        try:
            # Save to local storage (in production, save to database)
            filename = f"{creation_id}.txt"
            filepath = f"/tmp/generated_stories/{filename}"
            
            # Ensure directory exists
            os.makedirs("/tmp/generated_stories", exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Return URL (in production, return proper URL)
            return f"https://cdn.cherry-ai.com/stories/{filename}"
            
        except Exception as e:
            print(f"Error saving story: {e}")
            return None
    
    # MAIN CREATION ROUTER
    async def create_content(self, request: CreationRequest) -> CreationResult:
        """Main content creation router"""
        
        if request.type == "song":
            return await self.create_song(request)
            
        elif request.type == "image":
            # Route to appropriate image provider
            provider = request.parameters.get('provider', 'stability')
            if provider == 'venice':
                return await self.create_image_venice(request)
            else:
                return await self.create_image_stability(request)
                
        elif request.type == "story":
            return await self.create_story(request)
            
        elif request.type == "video":
            # Placeholder for video generation (could integrate with Runway, etc.)
            return CreationResult(
                id=str(uuid.uuid4()),
                type="video",
                status="failed",
                error_message="Video generation not yet implemented",
                created_at=datetime.utcnow().isoformat()
            )
            
        elif request.type == "edit":
            # Placeholder for image editing
            return CreationResult(
                id=str(uuid.uuid4()),
                type="edit",
                status="failed",
                error_message="Image editing not yet implemented",
                created_at=datetime.utcnow().isoformat()
            )
            
        else:
            return CreationResult(
                id=str(uuid.uuid4()),
                type=request.type,
                status="failed",
                error_message=f"Unknown creation type: {request.type}",
                created_at=datetime.utcnow().isoformat()
            )
    
    def get_creation_status(self, creation_id: str) -> Optional[CreationResult]:
        """Get status of active creation"""
        creation_data = self.active_creations.get(creation_id)
        if creation_data:
            return creation_data["result"]
        return None

# Global instance
api_manager = MultiModalAPIManager()

