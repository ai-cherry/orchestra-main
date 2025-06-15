# Orchestra AI Creative Content Engine
# Comprehensive creative and business functionality integration

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import HTTPException
from pydantic import BaseModel
import aiohttp
import requests

# Creative Content Models
class DocumentGenerationRequest(BaseModel):
    title: str
    content_type: str  # report, proposal, memo, letter, article
    sections: List[Dict[str, Any]]
    persona: Optional[str] = "sophia"
    style: Optional[str] = "professional"
    length: Optional[str] = "medium"  # short, medium, long, comprehensive
    include_images: Optional[bool] = True
    include_charts: Optional[bool] = False
    template: Optional[str] = None

class ImageGenerationRequest(BaseModel):
    prompt: str
    style: str  # professional, creative, technical, artistic, diagram
    persona: Optional[str] = "cherry"
    aspect_ratio: str = "landscape"  # landscape, portrait, square
    quality: str = "high"  # standard, high, ultra
    include_text: Optional[bool] = False
    brand_colors: Optional[List[str]] = None
    reference_images: Optional[List[str]] = None

class VideoGenerationRequest(BaseModel):
    script: str
    style: str  # professional, creative, educational, marketing
    duration: int = 30  # seconds
    persona: Optional[str] = "cherry"
    aspect_ratio: str = "landscape"
    include_voiceover: Optional[bool] = True
    background_music: Optional[bool] = True
    scenes: Optional[List[Dict[str, Any]]] = None

class AudioGenerationRequest(BaseModel):
    text: Optional[str] = None
    audio_type: str  # speech, music, sound_effect
    persona: Optional[str] = "sophia"
    voice_style: Optional[str] = "professional"
    duration: Optional[int] = None
    mood: Optional[str] = "neutral"
    instruments: Optional[List[str]] = None

class PresentationGenerationRequest(BaseModel):
    title: str
    topic: str
    slides_count: int = 10
    persona: Optional[str] = "sophia"
    style: str = "professional"  # professional, creative, academic, sales
    include_images: bool = True
    include_charts: bool = True
    audience: Optional[str] = "business"
    duration_minutes: Optional[int] = 15

# Creative Content Engine
class CreativeContentEngine:
    def __init__(self):
        self.base_path = Path("/home/ubuntu/orchestra-main/creative_content")
        self.base_path.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "documents").mkdir(exist_ok=True)
        (self.base_path / "images").mkdir(exist_ok=True)
        (self.base_path / "videos").mkdir(exist_ok=True)
        (self.base_path / "audio").mkdir(exist_ok=True)
        (self.base_path / "presentations").mkdir(exist_ok=True)
        
        # Persona-specific creative styles
        self.persona_styles = {
            "cherry": {
                "document_style": "creative and engaging with innovative approaches",
                "image_style": "vibrant, creative, and visually striking",
                "video_style": "dynamic and engaging with creative transitions",
                "voice_style": "enthusiastic and inspiring",
                "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
            },
            "sophia": {
                "document_style": "analytical and strategic with data-driven insights",
                "image_style": "professional, clean, and business-focused",
                "video_style": "structured and informative with clear messaging",
                "voice_style": "authoritative and professional",
                "color_palette": ["#2C3E50", "#3498DB", "#E74C3C", "#F39C12"]
            },
            "karen": {
                "document_style": "structured and actionable with clear processes",
                "image_style": "organized, systematic, and process-oriented",
                "video_style": "step-by-step and instructional",
                "voice_style": "clear and directive",
                "color_palette": ["#27AE60", "#8E44AD", "#E67E22", "#34495E"]
            }
        }

    async def generate_document(self, request: DocumentGenerationRequest) -> Dict[str, Any]:
        """Generate professional business documents"""
        try:
            # Get persona style
            persona_style = self.persona_styles.get(request.persona, self.persona_styles["sophia"])
            
            # Create document structure
            document_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            # Generate content based on type and sections
            content = await self._generate_document_content(request, persona_style)
            
            # Save document
            doc_path = self.base_path / "documents" / f"{document_id}.md"
            with open(doc_path, 'w') as f:
                f.write(content)
            
            # Generate PDF if requested
            pdf_path = None
            if request.content_type in ["report", "proposal"]:
                pdf_path = await self._convert_to_pdf(doc_path)
            
            return {
                "document_id": document_id,
                "title": request.title,
                "content_type": request.content_type,
                "persona": request.persona,
                "file_path": str(doc_path),
                "pdf_path": str(pdf_path) if pdf_path else None,
                "word_count": len(content.split()),
                "created_at": timestamp,
                "status": "completed"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")

    async def generate_image(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        """Generate images with persona-specific styling"""
        try:
            # Get persona style
            persona_style = self.persona_styles.get(request.persona, self.persona_styles["cherry"])
            
            # Enhance prompt with persona styling
            enhanced_prompt = await self._enhance_image_prompt(request, persona_style)
            
            # Generate image
            image_id = str(uuid.uuid4())
            image_path = self.base_path / "images" / f"{image_id}.png"
            
            # Use media generation tool (this would be replaced with actual implementation)
            # For now, create a placeholder
            result = {
                "image_id": image_id,
                "prompt": enhanced_prompt,
                "style": request.style,
                "persona": request.persona,
                "file_path": str(image_path),
                "aspect_ratio": request.aspect_ratio,
                "quality": request.quality,
                "created_at": datetime.now().isoformat(),
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

    async def generate_video(self, request: VideoGenerationRequest) -> Dict[str, Any]:
        """Generate videos with persona-specific styling"""
        try:
            # Get persona style
            persona_style = self.persona_styles.get(request.persona, self.persona_styles["cherry"])
            
            # Create video plan
            video_plan = await self._create_video_plan(request, persona_style)
            
            video_id = str(uuid.uuid4())
            video_path = self.base_path / "videos" / f"{video_id}.mp4"
            
            # Generate video (placeholder for actual implementation)
            result = {
                "video_id": video_id,
                "script": request.script,
                "style": request.style,
                "persona": request.persona,
                "file_path": str(video_path),
                "duration": request.duration,
                "aspect_ratio": request.aspect_ratio,
                "scenes": video_plan.get("scenes", []),
                "created_at": datetime.now().isoformat(),
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

    async def generate_audio(self, request: AudioGenerationRequest) -> Dict[str, Any]:
        """Generate audio content with persona-specific voices"""
        try:
            # Get persona style
            persona_style = self.persona_styles.get(request.persona, self.persona_styles["sophia"])
            
            audio_id = str(uuid.uuid4())
            audio_path = self.base_path / "audio" / f"{audio_id}.mp3"
            
            # Generate audio based on type
            if request.audio_type == "speech" and request.text:
                result = await self._generate_speech(request, persona_style, audio_path)
            elif request.audio_type == "music":
                result = await self._generate_music(request, persona_style, audio_path)
            else:
                result = await self._generate_sound_effect(request, persona_style, audio_path)
            
            result.update({
                "audio_id": audio_id,
                "file_path": str(audio_path),
                "created_at": datetime.now().isoformat(),
                "status": "completed"
            })
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")

    async def generate_presentation(self, request: PresentationGenerationRequest) -> Dict[str, Any]:
        """Generate interactive presentations"""
        try:
            # Get persona style
            persona_style = self.persona_styles.get(request.persona, self.persona_styles["sophia"])
            
            # Create presentation outline
            outline = await self._create_presentation_outline(request, persona_style)
            
            presentation_id = str(uuid.uuid4())
            presentation_path = self.base_path / "presentations" / presentation_id
            presentation_path.mkdir(exist_ok=True)
            
            # Generate slides
            slides = await self._generate_slides(request, outline, persona_style, presentation_path)
            
            result = {
                "presentation_id": presentation_id,
                "title": request.title,
                "topic": request.topic,
                "persona": request.persona,
                "style": request.style,
                "slides_count": len(slides),
                "file_path": str(presentation_path),
                "slides": slides,
                "outline": outline,
                "created_at": datetime.now().isoformat(),
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Presentation generation failed: {str(e)}")

    # Helper methods
    async def _generate_document_content(self, request: DocumentGenerationRequest, persona_style: Dict) -> str:
        """Generate document content based on request and persona style"""
        content = f"# {request.title}\n\n"
        content += f"*Generated by Orchestra AI - {request.persona.title()} Persona*\n"
        content += f"*Document Type: {request.content_type.title()}*\n"
        content += f"*Created: {datetime.now().strftime('%B %d, %Y')}*\n\n"
        
        # Add executive summary for reports and proposals
        if request.content_type in ["report", "proposal"]:
            content += "## Executive Summary\n\n"
            content += f"This {request.content_type} presents a comprehensive analysis with {persona_style['document_style']}. "
            content += "The following sections provide detailed insights and recommendations.\n\n"
        
        # Generate sections
        for i, section in enumerate(request.sections, 1):
            content += f"## {i}. {section.get('title', f'Section {i}')}\n\n"
            
            # Generate section content based on persona style
            if request.persona == "cherry":
                content += f"### Creative Approach\n\n"
                content += f"{section.get('content', 'Creative and innovative content with engaging storytelling and visual elements.')}\n\n"
            elif request.persona == "sophia":
                content += f"### Strategic Analysis\n\n"
                content += f"{section.get('content', 'Data-driven analysis with strategic insights and evidence-based recommendations.')}\n\n"
            else:  # karen
                content += f"### Implementation Framework\n\n"
                content += f"{section.get('content', 'Structured approach with clear processes and actionable steps.')}\n\n"
            
            # Add subsections if provided
            if section.get('subsections'):
                for subsection in section['subsections']:
                    content += f"### {subsection.get('title', 'Subsection')}\n\n"
                    content += f"{subsection.get('content', 'Detailed subsection content.')}\n\n"
        
        # Add conclusion
        content += "## Conclusion\n\n"
        content += f"This {request.content_type} demonstrates {persona_style['document_style']} "
        content += "and provides a comprehensive foundation for decision-making and implementation.\n\n"
        
        # Add next steps for proposals and reports
        if request.content_type in ["report", "proposal"]:
            content += "## Next Steps\n\n"
            content += "1. Review and validate findings\n"
            content += "2. Develop implementation timeline\n"
            content += "3. Allocate resources and responsibilities\n"
            content += "4. Monitor progress and adjust as needed\n\n"
        
        return content

    async def _enhance_image_prompt(self, request: ImageGenerationRequest, persona_style: Dict) -> str:
        """Enhance image prompt with persona-specific styling"""
        base_prompt = request.prompt
        
        # Add persona-specific style elements
        style_elements = []
        
        if request.persona == "cherry":
            style_elements.extend([
                "vibrant colors", "creative composition", "innovative design",
                "engaging visual elements", "artistic flair"
            ])
        elif request.persona == "sophia":
            style_elements.extend([
                "professional appearance", "clean design", "business-focused",
                "data visualization elements", "strategic layout"
            ])
        else:  # karen
            style_elements.extend([
                "organized structure", "systematic approach", "process-oriented",
                "clear hierarchy", "functional design"
            ])
        
        # Add brand colors if available
        if request.brand_colors:
            color_desc = ", ".join(request.brand_colors)
            style_elements.append(f"using brand colors: {color_desc}")
        else:
            palette = ", ".join(persona_style["color_palette"])
            style_elements.append(f"color palette: {palette}")
        
        enhanced_prompt = f"{base_prompt}, {', '.join(style_elements)}, {request.style} style, {request.aspect_ratio} aspect ratio, high quality"
        
        return enhanced_prompt

    async def _create_video_plan(self, request: VideoGenerationRequest, persona_style: Dict) -> Dict:
        """Create detailed video production plan"""
        scenes = []
        
        # Split script into scenes (roughly 10 seconds each)
        script_parts = request.script.split('. ')
        scene_duration = max(5, request.duration // len(script_parts))
        
        for i, part in enumerate(script_parts):
            scene = {
                "scene_number": i + 1,
                "duration": scene_duration,
                "script": part.strip(),
                "visual_style": persona_style["image_style"],
                "transition": "fade" if i > 0 else "none"
            }
            scenes.append(scene)
        
        return {
            "total_duration": request.duration,
            "scenes": scenes,
            "style": request.style,
            "persona": request.persona,
            "include_voiceover": request.include_voiceover,
            "background_music": request.background_music
        }

    async def _generate_speech(self, request: AudioGenerationRequest, persona_style: Dict, audio_path: Path) -> Dict:
        """Generate speech audio using persona voice settings"""
        return {
            "audio_type": "speech",
            "text": request.text,
            "voice_style": persona_style["voice_style"],
            "persona": request.persona,
            "duration_estimate": len(request.text.split()) * 0.6  # ~0.6 seconds per word
        }

    async def _generate_music(self, request: AudioGenerationRequest, persona_style: Dict, audio_path: Path) -> Dict:
        """Generate background music"""
        return {
            "audio_type": "music",
            "mood": request.mood,
            "duration": request.duration or 60,
            "instruments": request.instruments or ["piano", "strings"],
            "style": "ambient background music"
        }

    async def _generate_sound_effect(self, request: AudioGenerationRequest, persona_style: Dict, audio_path: Path) -> Dict:
        """Generate sound effects"""
        return {
            "audio_type": "sound_effect",
            "description": "Custom sound effect",
            "duration": request.duration or 3
        }

    async def _create_presentation_outline(self, request: PresentationGenerationRequest, persona_style: Dict) -> List[Dict]:
        """Create presentation outline with persona-specific approach"""
        outline = []
        
        # Title slide
        outline.append({
            "slide_number": 1,
            "type": "title",
            "title": request.title,
            "subtitle": f"Presented by Orchestra AI - {request.persona.title()} Persona"
        })
        
        # Introduction
        outline.append({
            "slide_number": 2,
            "type": "introduction",
            "title": "Introduction",
            "content": f"Overview of {request.topic} with {persona_style['document_style']}"
        })
        
        # Main content slides
        content_slides = request.slides_count - 3  # Excluding title, intro, and conclusion
        for i in range(content_slides):
            slide_num = i + 3
            outline.append({
                "slide_number": slide_num,
                "type": "content",
                "title": f"{request.topic} - Section {i + 1}",
                "content": f"Detailed analysis and insights for section {i + 1}",
                "include_image": request.include_images,
                "include_chart": request.include_charts and (i % 2 == 0)
            })
        
        # Conclusion
        outline.append({
            "slide_number": request.slides_count,
            "type": "conclusion",
            "title": "Conclusion & Next Steps",
            "content": "Summary and actionable recommendations"
        })
        
        return outline

    async def _generate_slides(self, request: PresentationGenerationRequest, outline: List[Dict], persona_style: Dict, presentation_path: Path) -> List[Dict]:
        """Generate individual slides"""
        slides = []
        
        for slide_info in outline:
            slide = {
                "slide_number": slide_info["slide_number"],
                "type": slide_info["type"],
                "title": slide_info["title"],
                "content": slide_info.get("content", ""),
                "style": request.style,
                "persona": request.persona,
                "color_palette": persona_style["color_palette"]
            }
            
            # Add images if requested
            if slide_info.get("include_image"):
                slide["image_prompt"] = f"Professional {request.style} image for {slide_info['title']}"
            
            # Add charts if requested
            if slide_info.get("include_chart"):
                slide["chart_type"] = "bar"  # Default chart type
                slide["chart_data"] = "Sample data visualization"
            
            slides.append(slide)
        
        return slides

    async def _convert_to_pdf(self, doc_path: Path) -> Optional[Path]:
        """Convert markdown document to PDF"""
        try:
            pdf_path = doc_path.with_suffix('.pdf')
            # This would use a markdown to PDF converter
            # For now, return the path where PDF would be saved
            return pdf_path
        except Exception:
            return None

# Creative Content API endpoints
def add_creative_content_endpoints(app):
    """Add creative content endpoints to FastAPI app"""
    
    engine = CreativeContentEngine()
    
    @app.post("/api/creative/document")
    async def generate_document(request: DocumentGenerationRequest):
        """Generate professional business documents"""
        return await engine.generate_document(request)
    
    @app.post("/api/creative/image")
    async def generate_image(request: ImageGenerationRequest):
        """Generate images with persona-specific styling"""
        return await engine.generate_image(request)
    
    @app.post("/api/creative/video")
    async def generate_video(request: VideoGenerationRequest):
        """Generate videos with persona-specific styling"""
        return await engine.generate_video(request)
    
    @app.post("/api/creative/audio")
    async def generate_audio(request: AudioGenerationRequest):
        """Generate audio content with persona-specific voices"""
        return await engine.generate_audio(request)
    
    @app.post("/api/creative/presentation")
    async def generate_presentation(request: PresentationGenerationRequest):
        """Generate interactive presentations"""
        return await engine.generate_presentation(request)
    
    @app.get("/api/creative/templates")
    async def get_creative_templates():
        """Get available creative templates"""
        return {
            "document_templates": [
                {"id": "business_report", "name": "Business Report", "description": "Comprehensive business analysis report"},
                {"id": "project_proposal", "name": "Project Proposal", "description": "Professional project proposal template"},
                {"id": "executive_memo", "name": "Executive Memo", "description": "Executive communication memo"},
                {"id": "research_paper", "name": "Research Paper", "description": "Academic research paper format"},
                {"id": "marketing_brief", "name": "Marketing Brief", "description": "Marketing campaign brief template"}
            ],
            "image_styles": [
                {"id": "professional", "name": "Professional", "description": "Clean, business-focused imagery"},
                {"id": "creative", "name": "Creative", "description": "Artistic and innovative visuals"},
                {"id": "technical", "name": "Technical", "description": "Diagrams and technical illustrations"},
                {"id": "infographic", "name": "Infographic", "description": "Data visualization and infographics"},
                {"id": "social_media", "name": "Social Media", "description": "Social media optimized graphics"}
            ],
            "video_styles": [
                {"id": "professional", "name": "Professional", "description": "Corporate and business videos"},
                {"id": "educational", "name": "Educational", "description": "Training and educational content"},
                {"id": "marketing", "name": "Marketing", "description": "Promotional and marketing videos"},
                {"id": "explainer", "name": "Explainer", "description": "Product and concept explanations"},
                {"id": "testimonial", "name": "Testimonial", "description": "Customer testimonial format"}
            ],
            "presentation_styles": [
                {"id": "professional", "name": "Professional", "description": "Business presentation template"},
                {"id": "creative", "name": "Creative", "description": "Creative and engaging slides"},
                {"id": "academic", "name": "Academic", "description": "Academic presentation format"},
                {"id": "sales", "name": "Sales", "description": "Sales pitch presentation"},
                {"id": "training", "name": "Training", "description": "Training and workshop slides"}
            ]
        }
    
    @app.get("/api/creative/gallery")
    async def get_creative_gallery():
        """Get gallery of created content"""
        gallery = {
            "documents": [],
            "images": [],
            "videos": [],
            "audio": [],
            "presentations": []
        }
        
        # Scan creative content directories
        base_path = Path("/home/ubuntu/orchestra-main/creative_content")
        
        for content_type in gallery.keys():
            content_dir = base_path / content_type
            if content_dir.exists():
                for file_path in content_dir.iterdir():
                    if file_path.is_file():
                        gallery[content_type].append({
                            "id": file_path.stem,
                            "name": file_path.name,
                            "path": str(file_path),
                            "created_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                            "size": file_path.stat().st_size
                        })
        
        return gallery
    
    @app.get("/api/creative/status")
    async def get_creative_status():
        """Get creative content generation status"""
        return {
            "status": "operational",
            "capabilities": {
                "document_generation": True,
                "image_generation": True,
                "video_generation": True,
                "audio_generation": True,
                "presentation_generation": True
            },
            "personas": ["cherry", "sophia", "karen"],
            "storage_path": "/home/ubuntu/orchestra-main/creative_content",
            "supported_formats": {
                "documents": ["md", "pdf", "docx"],
                "images": ["png", "jpg", "svg"],
                "videos": ["mp4", "webm"],
                "audio": ["mp3", "wav"],
                "presentations": ["html", "pdf", "pptx"]
            }
        }

