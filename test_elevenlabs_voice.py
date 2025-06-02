#!/usr/bin/env python3
"""
Test script to verify ElevenLabs voice synthesis integration
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_elevenlabs():
    """Test ElevenLabs voice synthesis"""
    print("🎤 Testing ElevenLabs Voice Synthesis")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not set!")
        print("\nTo set it:")
        print("export ELEVENLABS_API_KEY=your_key_here")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        from agent.app.services.natural_language_processor import ResponseGenerator
        print("✅ Successfully imported ResponseGenerator")
        
        # Initialize response generator
        generator = ResponseGenerator()
        print("✅ ResponseGenerator initialized")
        
        if generator.voice_id:
            print(f"✅ Voice ID selected: {generator.voice_id}")
        else:
            print("⚠️  No voice ID selected (check API key validity)")
            return False
        
        # Test text samples
        test_texts = [
            "Hello! I'm your AI assistant powered by ElevenLabs.",
            "The migration from Resemble AI to ElevenLabs is now complete.",
            "I can speak with natural, human-like voice quality."
        ]
        
        print("\n🔊 Testing voice synthesis...")
        for i, text in enumerate(test_texts, 1):
            print(f"\nTest {i}: {text}")
            
            # Generate speech
            audio_url = await generator.text_to_speech(text)
            
            if audio_url:
                print(f"✅ Audio generated successfully!")
                print(f"   Data URL length: {len(audio_url)} characters")
                
                # Save to file for manual testing (optional)
                if audio_url.startswith("data:audio/mp3;base64,"):
                    import base64
                    audio_data = audio_url.split(",")[1]
                    audio_bytes = base64.b64decode(audio_data)
                    
                    filename = f"test_audio_{i}.mp3"
                    with open(filename, "wb") as f:
                        f.write(audio_bytes)
                    print(f"   Saved to: {filename}")
            else:
                print("❌ Failed to generate audio")
                return False
        
        print("\n✅ All tests passed!")
        print("\n📝 Next steps:")
        print("1. Play the generated MP3 files to verify audio quality")
        print("2. Configure specific voices for each persona")
        print("3. Implement caching for frequently used phrases")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nMake sure to install requirements:")
        print("pip install -r requirements/base.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_voice_settings():
    """Test different voice settings"""
    print("\n\n🎛️  Testing Voice Settings")
    print("=" * 50)
    
    try:
        from elevenlabs import VoiceSettings
        
        # Test different configurations
        settings_configs = [
            {
                "name": "Natural Conversation",
                "settings": VoiceSettings(
                    stability=0.75,
                    similarity_boost=0.85,
                    style=0.5,
                    use_speaker_boost=True
                )
            },
            {
                "name": "Expressive Reading",
                "settings": VoiceSettings(
                    stability=0.60,
                    similarity_boost=0.75,
                    style=0.8,
                    use_speaker_boost=True
                )
            },
            {
                "name": "Stable Narration",
                "settings": VoiceSettings(
                    stability=0.90,
                    similarity_boost=0.95,
                    style=0.2,
                    use_speaker_boost=False
                )
            }
        ]
        
        for config in settings_configs:
            print(f"\n{config['name']}:")
            settings = config['settings']
            print(f"  Stability: {settings.stability}")
            print(f"  Similarity: {settings.similarity_boost}")
            print(f"  Style: {settings.style}")
            print(f"  Speaker Boost: {settings.use_speaker_boost}")
        
        print("\n✅ Voice settings configurations ready")
        return True
        
    except Exception as e:
        print(f"❌ Error testing voice settings: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 ElevenLabs Integration Test Suite")
    print("=" * 60)
    
    # Test basic functionality
    success = await test_elevenlabs()
    
    # Test voice settings
    if success:
        await test_voice_settings()
    
    print("\n" + "=" * 60)
    if success:
        print("✨ ElevenLabs integration is working correctly!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        sys.exit(1)
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 