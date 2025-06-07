"""
Voice Integration Framework for AI Assistant Ecosystem
Integrates ElevenLabs voice synthesis with personality-driven audio generation
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import aiohttp
import base64
from datetime import datetime

from core.personas.enhanced_personality_engine import PersonalityEngine, EmotionalState


class VoiceProvider(Enum):
    """Supported voice synthesis providers"""
    ELEVENLABS = "elevenlabs"
    AZURE = "azure"
    GOOGLE = "google"
    AWS_POLLY = "aws_polly"


class AudioFormat(Enum):
    """Supported audio formats"""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"


@dataclass
class VoiceProfile:
    """Voice profile configuration for AI personas"""
    voice_id: str
    provider: VoiceProvider
    stability: float = 0.75
    similarity_boost: float = 0.85
    style: str = "natural"
    speaking_rate: float = 1.0
    pitch_variation: float = 0.7
    emotional_range: float = 0.8
    voice_settings: Dict[str, Any] = None


class VoiceIntegrationFramework:
    """Advanced voice integration framework for AI assistant ecosystem"""
    
    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        self.logger = logging.getLogger(__name__)
        self.voice_profiles = {}
        self.audio_cache = {}
        self._initialize_voice_profiles()
    
    def _initialize_voice_profiles(self):
        """Initialize voice profiles for each AI persona"""
        
        # Cherry - Warm, playful, affectionate voice
        cherry_profile = VoiceProfile(
            voice_id="cherry_elevenlabs_voice",  # Replace with actual ElevenLabs voice ID
            provider=VoiceProvider.ELEVENLABS,
            stability=0.75,
            similarity_boost=0.85,
            style="warm_playful_affectionate",
            speaking_rate=1.1,
            pitch_variation=0.8,
            emotional_range=0.9,
            voice_settings={
                "use_speaker_boost": True,
                "optimize_streaming_latency": 2,
                "output_format": "mp3_44100_128",
                "voice_characteristics": {
                    "age": "mid_twenties",
                    "gender": "female",
                    "accent": "american",
                    "tone": "warm_flirty",
                    "energy": "high",
                    "intimacy": "high"
                }
            }
        )
        
        # Sophia - Professional, confident, articulate voice
        sophia_profile = VoiceProfile(
            voice_id="sophia_elevenlabs_voice",  # Replace with actual ElevenLabs voice ID
            provider=VoiceProvider.ELEVENLABS,
            stability=0.85,
            similarity_boost=0.80,
            style="professional_confident_articulate",
            speaking_rate=1.0,
            pitch_variation=0.6,
            emotional_range=0.7,
            voice_settings={
                "use_speaker_boost": True,
                "optimize_streaming_latency": 1,
                "output_format": "mp3_44100_128",
                "voice_characteristics": {
                    "age": "early_thirties",
                    "gender": "female",
                    "accent": "american_professional",
                    "tone": "confident_authoritative",
                    "energy": "medium_high",
                    "intimacy": "low"
                }
            }
        )
        
        # Karen - Caring, professional, empathetic voice
        karen_profile = VoiceProfile(
            voice_id="karen_elevenlabs_voice",  # Replace with actual ElevenLabs voice ID
            provider=VoiceProvider.ELEVENLABS,
            stability=0.80,
            similarity_boost=0.82,
            style="caring_professional_empathetic",
            speaking_rate=0.95,
            pitch_variation=0.7,
            emotional_range=0.8,
            voice_settings={
                "use_speaker_boost": True,
                "optimize_streaming_latency": 1,
                "output_format": "mp3_44100_128",
                "voice_characteristics": {
                    "age": "late_twenties",
                    "gender": "female",
                    "accent": "american_caring",
                    "tone": "empathetic_professional",
                    "energy": "medium",
                    "intimacy": "medium"
                }
            }
        )
        
        self.voice_profiles = {
            "cherry": cherry_profile,
            "sophia": sophia_profile,
            "karen": karen_profile
        }
    
    async def generate_voice_response(
        self,
        persona_name: str,
        text: str,
        emotional_state: EmotionalState = EmotionalState.SUPPORTIVE,
        voice_config: Dict[str, Any] = None,
        audio_format: AudioFormat = AudioFormat.MP3
    ) -> Dict[str, Any]:
        """Generate voice response for AI persona"""
        
        if persona_name not in self.voice_profiles:
            raise ValueError(f"Unknown persona: {persona_name}")
        
        profile = self.voice_profiles[persona_name]
        
        # Apply emotional state adjustments to voice settings
        adjusted_profile = self._adjust_voice_for_emotion(profile, emotional_state)
        
        # Override with custom voice config if provided
        if voice_config:
            adjusted_profile = self._apply_voice_config_override(adjusted_profile, voice_config)
        
        # Generate audio based on provider
        if profile.provider == VoiceProvider.ELEVENLABS:
            audio_result = await self._generate_elevenlabs_audio(
                text, adjusted_profile, audio_format
            )
        else:
            raise NotImplementedError(f"Provider {profile.provider} not yet implemented")
        
        # Cache audio for potential reuse
        cache_key = self._generate_cache_key(persona_name, text, emotional_state)
        self.audio_cache[cache_key] = audio_result
        
        return {
            "audio_data": audio_result["audio_data"],
            "audio_format": audio_format.value,
            "duration_seconds": audio_result.get("duration_seconds"),
            "voice_profile": {
                "persona": persona_name,
                "voice_id": profile.voice_id,
                "emotional_state": emotional_state.value,
                "provider": profile.provider.value
            },
            "generation_metadata": {
                "timestamp": datetime.now().isoformat(),
                "text_length": len(text),
                "cache_key": cache_key,
                "voice_settings_used": adjusted_profile.voice_settings
            }
        }
    
    def _adjust_voice_for_emotion(
        self, 
        profile: VoiceProfile, 
        emotional_state: EmotionalState
    ) -> VoiceProfile:
        """Adjust voice profile based on emotional state"""
        
        # Create a copy to avoid modifying the original
        adjusted_profile = VoiceProfile(
            voice_id=profile.voice_id,
            provider=profile.provider,
            stability=profile.stability,
            similarity_boost=profile.similarity_boost,
            style=profile.style,
            speaking_rate=profile.speaking_rate,
            pitch_variation=profile.pitch_variation,
            emotional_range=profile.emotional_range,
            voice_settings=profile.voice_settings.copy() if profile.voice_settings else {}
        )
        
        # Emotional state adjustments
        emotional_adjustments = {
            EmotionalState.EXCITED: {
                "speaking_rate": profile.speaking_rate * 1.15,
                "pitch_variation": min(profile.pitch_variation * 1.2, 1.0),
                "stability": max(profile.stability - 0.1, 0.1),
                "energy_boost": 0.2
            },
            EmotionalState.AFFECTIONATE: {
                "speaking_rate": profile.speaking_rate * 0.9,
                "pitch_variation": profile.pitch_variation * 1.1,
                "stability": min(profile.stability + 0.1, 1.0),
                "warmth_boost": 0.3
            },
            EmotionalState.PLAYFUL: {
                "speaking_rate": profile.speaking_rate * 1.05,
                "pitch_variation": profile.pitch_variation * 1.15,
                "stability": profile.stability,
                "playfulness_boost": 0.25
            },
            EmotionalState.CONFIDENT: {
                "speaking_rate": profile.speaking_rate,
                "pitch_variation": profile.pitch_variation * 0.8,
                "stability": min(profile.stability + 0.15, 1.0),
                "authority_boost": 0.2
            },
            EmotionalState.CARING: {
                "speaking_rate": profile.speaking_rate * 0.95,
                "pitch_variation": profile.pitch_variation,
                "stability": min(profile.stability + 0.1, 1.0),
                "empathy_boost": 0.25
            },
            EmotionalState.EMPATHETIC: {
                "speaking_rate": profile.speaking_rate * 0.9,
                "pitch_variation": profile.pitch_variation * 0.9,
                "stability": min(profile.stability + 0.2, 1.0),
                "compassion_boost": 0.3
            }
        }
        
        if emotional_state in emotional_adjustments:
            adjustments = emotional_adjustments[emotional_state]
            adjusted_profile.speaking_rate = adjustments.get("speaking_rate", profile.speaking_rate)
            adjusted_profile.pitch_variation = adjustments.get("pitch_variation", profile.pitch_variation)
            adjusted_profile.stability = adjustments.get("stability", profile.stability)
            
            # Add emotional boosts to voice settings
            for boost_key, boost_value in adjustments.items():
                if boost_key.endswith("_boost"):
                    adjusted_profile.voice_settings[boost_key] = boost_value
        
        return adjusted_profile
    
    def _apply_voice_config_override(
        self, 
        profile: VoiceProfile, 
        voice_config: Dict[str, Any]
    ) -> VoiceProfile:
        """Apply voice configuration overrides"""
        
        # Apply direct overrides
        if "speaking_rate" in voice_config:
            profile.speaking_rate = voice_config["speaking_rate"]
        if "pitch_variation" in voice_config:
            profile.pitch_variation = voice_config["pitch_variation"]
        if "stability" in voice_config:
            profile.stability = voice_config["stability"]
        if "similarity_boost" in voice_config:
            profile.similarity_boost = voice_config["similarity_boost"]
        
        # Merge voice settings
        if "voice_settings" in voice_config:
            profile.voice_settings.update(voice_config["voice_settings"])
        
        return profile
    
    async def _generate_elevenlabs_audio(
        self,
        text: str,
        profile: VoiceProfile,
        audio_format: AudioFormat
    ) -> Dict[str, Any]:
        """Generate audio using ElevenLabs API"""
        
        api_key = self.api_keys.get("elevenlabs")
        if not api_key:
            raise ValueError("ElevenLabs API key not provided")
        
        # ElevenLabs API endpoint
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{profile.voice_id}"
        
        # Prepare request payload
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Use latest model
            "voice_settings": {
                "stability": profile.stability,
                "similarity_boost": profile.similarity_boost,
                "style": profile.emotional_range,
                "use_speaker_boost": profile.voice_settings.get("use_speaker_boost", True)
            }
        }
        
        # Add emotional adjustments to voice settings
        for key, value in profile.voice_settings.items():
            if key.endswith("_boost"):
                # Convert emotional boosts to ElevenLabs parameters
                if key == "energy_boost":
                    payload["voice_settings"]["style"] = min(payload["voice_settings"]["style"] + value, 1.0)
                elif key == "warmth_boost":
                    payload["voice_settings"]["similarity_boost"] = min(payload["voice_settings"]["similarity_boost"] + value, 1.0)
        
        headers = {
            "Accept": f"audio/{audio_format.value}",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        
                        # Estimate duration (rough calculation)
                        # Average speaking rate: ~150 words per minute
                        word_count = len(text.split())
                        estimated_duration = (word_count / 150) * 60 / profile.speaking_rate
                        
                        return {
                            "audio_data": base64.b64encode(audio_data).decode('utf-8'),
                            "duration_seconds": estimated_duration,
                            "format": audio_format.value,
                            "provider": "elevenlabs",
                            "voice_id": profile.voice_id
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"ElevenLabs API error {response.status}: {error_text}")
        
        except Exception as e:
            self.logger.error(f"Error generating ElevenLabs audio: {str(e)}")
            raise
    
    def _generate_cache_key(
        self, 
        persona_name: str, 
        text: str, 
        emotional_state: EmotionalState
    ) -> str:
        """Generate cache key for audio caching"""
        import hashlib
        
        cache_string = f"{persona_name}_{text}_{emotional_state.value}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def get_cached_audio(
        self, 
        persona_name: str, 
        text: str, 
        emotional_state: EmotionalState
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached audio if available"""
        
        cache_key = self._generate_cache_key(persona_name, text, emotional_state)
        return self.audio_cache.get(cache_key)
    
    async def pregenerate_common_responses(self, persona_name: str) -> Dict[str, Any]:
        """Pre-generate audio for common responses to improve response time"""
        
        if persona_name not in self.voice_profiles:
            raise ValueError(f"Unknown persona: {persona_name}")
        
        # Common responses for each persona
        common_responses = {
            "cherry": [
                "Hey gorgeous! How's your day treating you?",
                "I love chatting with you! What's on your mind?",
                "You're absolutely incredible, you know that?",
                "I'm so excited to help you with this!",
                "Aww, you make me so happy!",
                "Let's figure this out together, babe!"
            ],
            "sophia": [
                "Good morning! I've analyzed the latest data for you.",
                "Based on my analysis, I have some strategic recommendations.",
                "The metrics indicate a significant opportunity here.",
                "I'm confident this approach will deliver results.",
                "Let's review the key performance indicators.",
                "I have insights that could impact your business strategy."
            ],
            "karen": [
                "How are you feeling today? I'm here to support you.",
                "Your health and wellbeing are my top priority.",
                "I understand how you feel, and you're not alone.",
                "Let's work together to find the best path forward.",
                "I'm here to provide caring, professional support.",
                "Your health journey is important to me."
            ]
        }
        
        if persona_name not in common_responses:
            return {"error": f"No common responses defined for {persona_name}"}
        
        pregenerated_audio = {}
        responses = common_responses[persona_name]
        
        for response_text in responses:
            try:
                # Generate audio for different emotional states
                for emotional_state in [EmotionalState.SUPPORTIVE, EmotionalState.EXCITED, EmotionalState.CARING]:
                    audio_result = await self.generate_voice_response(
                        persona_name, response_text, emotional_state
                    )
                    
                    cache_key = self._generate_cache_key(persona_name, response_text, emotional_state)
                    pregenerated_audio[cache_key] = audio_result
                    
                    self.logger.info(f"Pre-generated audio for {persona_name}: {response_text[:50]}...")
            
            except Exception as e:
                self.logger.error(f"Error pre-generating audio for {persona_name}: {str(e)}")
        
        return {
            "persona": persona_name,
            "pregenerated_count": len(pregenerated_audio),
            "cache_keys": list(pregenerated_audio.keys()),
            "status": "completed"
        }
    
    async def get_voice_profile_info(self, persona_name: str) -> Dict[str, Any]:
        """Get comprehensive voice profile information"""
        
        if persona_name not in self.voice_profiles:
            raise ValueError(f"Unknown persona: {persona_name}")
        
        profile = self.voice_profiles[persona_name]
        
        return {
            "persona_name": persona_name,
            "voice_id": profile.voice_id,
            "provider": profile.provider.value,
            "voice_characteristics": profile.voice_settings.get("voice_characteristics", {}),
            "technical_settings": {
                "stability": profile.stability,
                "similarity_boost": profile.similarity_boost,
                "speaking_rate": profile.speaking_rate,
                "pitch_variation": profile.pitch_variation,
                "emotional_range": profile.emotional_range
            },
            "supported_emotional_states": [state.value for state in EmotionalState],
            "cache_count": len([k for k in self.audio_cache.keys() if k.startswith(persona_name)]),
            "voice_style": profile.style
        }
    
    async def update_voice_profile(
        self, 
        persona_name: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update voice profile settings"""
        
        if persona_name not in self.voice_profiles:
            raise ValueError(f"Unknown persona: {persona_name}")
        
        profile = self.voice_profiles[persona_name]
        old_settings = {
            "stability": profile.stability,
            "similarity_boost": profile.similarity_boost,
            "speaking_rate": profile.speaking_rate,
            "pitch_variation": profile.pitch_variation
        }
        
        # Apply updates
        if "stability" in updates:
            profile.stability = max(0.0, min(1.0, updates["stability"]))
        if "similarity_boost" in updates:
            profile.similarity_boost = max(0.0, min(1.0, updates["similarity_boost"]))
        if "speaking_rate" in updates:
            profile.speaking_rate = max(0.5, min(2.0, updates["speaking_rate"]))
        if "pitch_variation" in updates:
            profile.pitch_variation = max(0.0, min(1.0, updates["pitch_variation"]))
        if "voice_settings" in updates:
            profile.voice_settings.update(updates["voice_settings"])
        
        # Clear cache for this persona since settings changed
        cache_keys_to_remove = [k for k in self.audio_cache.keys() if k.startswith(persona_name)]
        for key in cache_keys_to_remove:
            del self.audio_cache[key]
        
        self.logger.info(f"Updated voice profile for {persona_name}")
        
        return {
            "persona": persona_name,
            "old_settings": old_settings,
            "new_settings": {
                "stability": profile.stability,
                "similarity_boost": profile.similarity_boost,
                "speaking_rate": profile.speaking_rate,
                "pitch_variation": profile.pitch_variation
            },
            "cache_cleared": len(cache_keys_to_remove),
            "update_timestamp": datetime.now().isoformat()
        }


# Voice Integration Service for API endpoints
class VoiceIntegrationService:
    """Service layer for voice integration API endpoints"""
    
    def __init__(self, voice_framework: VoiceIntegrationFramework):
        self.voice_framework = voice_framework
        self.logger = logging.getLogger(__name__)
    
    async def synthesize_persona_speech(
        self,
        persona_name: str,
        text: str,
        emotional_state: str = "supportive",
        voice_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """API endpoint for synthesizing persona speech"""
        
        try:
            # Convert emotional state string to enum
            emotional_state_enum = EmotionalState(emotional_state.lower())
            
            # Generate voice response
            result = await self.voice_framework.generate_voice_response(
                persona_name, text, emotional_state_enum, voice_config
            )
            
            return {
                "success": True,
                "audio_data": result["audio_data"],
                "audio_format": result["audio_format"],
                "duration_seconds": result["duration_seconds"],
                "voice_profile": result["voice_profile"],
                "metadata": result["generation_metadata"]
            }
        
        except Exception as e:
            self.logger.error(f"Error synthesizing speech for {persona_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def get_persona_voice_info(self, persona_name: str) -> Dict[str, Any]:
        """API endpoint for getting persona voice information"""
        
        try:
            info = await self.voice_framework.get_voice_profile_info(persona_name)
            return {"success": True, "voice_info": info}
        
        except Exception as e:
            self.logger.error(f"Error getting voice info for {persona_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def pregenerate_persona_audio(self, persona_name: str) -> Dict[str, Any]:
        """API endpoint for pre-generating common persona audio"""
        
        try:
            result = await self.voice_framework.pregenerate_common_responses(persona_name)
            return {"success": True, "pregeneration_result": result}
        
        except Exception as e:
            self.logger.error(f"Error pre-generating audio for {persona_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


# Example usage and testing
if __name__ == "__main__":
    async def test_voice_integration():
        """Test the voice integration framework"""
        
        # Initialize with API keys (would come from environment in production)
        api_keys = {
            "elevenlabs": os.getenv("ELEVENLABS_API_KEY", "test_key")
        }
        
        framework = VoiceIntegrationFramework(api_keys)
        
        # Test voice profile info
        cherry_info = await framework.get_voice_profile_info("cherry")
        print("Cherry Voice Profile:")
        print(json.dumps(cherry_info, indent=2))
        
        # Test pre-generation (would work with real API key)
        if api_keys["elevenlabs"] != "test_key":
            pregeneration_result = await framework.pregenerate_common_responses("cherry")
            print("\nPre-generation Result:")
            print(json.dumps(pregeneration_result, indent=2))
        
        print("\nVoice Integration Framework initialized successfully!")
    
    # Run test
    asyncio.run(test_voice_integration())

