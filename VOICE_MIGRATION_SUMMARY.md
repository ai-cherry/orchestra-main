# Voice Service Migration: Resemble AI to ElevenLabs

## Migration Summary
This document summarizes the migration from Resemble AI to ElevenLabs for voice synthesis in the Orchestra AI project.

## Changes Made

### 1. Dependencies
**Before:**
```
resemble==1.5.0
```

**After:**
```
elevenlabs==1.17.0
```

### 2. Environment Variables
**Removed:**
- `RESEMBLE_API_KEY`
- `RESEMBLE_SYNTHESIS_ENDPOINT`
- `RESEMBLE_STREAMING_ENDPOINT`

**Added:**
- `ELEVENLABS_API_KEY`

### 3. Code Changes

#### agent/app/services/natural_language_processor.py
- Replaced Resemble import with ElevenLabs client
- Updated ResponseGenerator class to use ElevenLabs API
- Implemented voice selection logic for conversational voices
- Added optimized voice settings for maximum realism

#### agent/app/core/config.py
- Replaced RESEMBLE_API_KEY with ELEVENLABS_API_KEY

### 4. Documentation Updates
- Deleted `RESEMBLE_SETUP.md`
- Created `ELEVENLABS_SETUP.md` with comprehensive setup guide
- Updated `env.example` with ElevenLabs configuration
- Updated `docs/SECRETS_CONFIGURATION.md` to remove Resemble references
- Updated `docs/ADMIN_UI_ENHANCEMENT_PLAN.md` to mention ElevenLabs
- Updated `scripts/check_env_config.py` to check for ElevenLabs
- Updated `scripts/test_nl_and_agent.py` next steps

### 5. Key Implementation Details

#### Voice Configuration
```python
voice_settings = VoiceSettings(
    stability=0.75,          # Balance between consistency and expressiveness
    similarity_boost=0.85,   # High similarity to original voice
    style=0.5,              # Moderate style exaggeration
    use_speaker_boost=True  # Enhanced clarity
)
```

#### Audio Output Format
- Format: MP3 (44.1kHz, 128kbps)
- Output: Base64 encoded data URL for direct browser playback
- Model: eleven_monolingual_v1 (with option for eleven_turbo_v2)

## Benefits of Migration

1. **Superior Voice Quality**: 24-bit HD voice with vocal fold modeling
2. **Real-Time Capabilities**: 50ms latency for natural conversations
3. **Emotional Adaptation**: Dynamic emotional responses based on context
4. **Better Documentation**: More comprehensive API and community support
5. **Cost Efficiency**: Competitive pricing with free tier available

## Testing the Migration

1. Set your ElevenLabs API key:
   ```bash
   export ELEVENLABS_API_KEY=your_key_here
   ```

2. Run the test script:
   ```bash
   python scripts/test_nl_and_agent.py
   ```

3. Test voice synthesis via API:
   ```bash
   curl -X POST http://localhost:8000/api/agent/synthesize \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, I am your AI assistant powered by ElevenLabs!"}'
   ```

## Migration Checklist

- [x] Update requirements.txt
- [x] Update natural language processor
- [x] Update configuration files
- [x] Update environment variables
- [x] Update documentation
- [x] Remove all Resemble references
- [x] Create ElevenLabs setup guide
- [x] Test voice synthesis functionality

## Next Steps

1. Configure specific voices for each persona (Cherry, Sophia, Karen)
2. Implement voice caching for frequently used phrases
3. Add streaming voice synthesis for real-time responses
4. Integrate voice synthesis with admin UI components
5. Set up cost monitoring and usage alerts

## Rollback Plan

If issues arise, to rollback:
1. Revert requirements/base.txt to use `resemble==1.5.0`
2. Revert agent/app/services/natural_language_processor.py
3. Restore RESEMBLE_API_KEY in environment
4. Restore original documentation

## Support Resources

- ElevenLabs Documentation: https://docs.elevenlabs.io
- ElevenLabs Python SDK: https://github.com/elevenlabs/elevenlabs-python
- API Status: https://status.elevenlabs.io
- Community Forum: https://discord.gg/elevenlabs 