# ElevenLabs Setup for Orchestra AI

This guide covers setting up ElevenLabs voice synthesis for Orchestra AI, providing realistic AI voice capabilities for your personal assistant.

## Prerequisites

1. ElevenLabs account (sign up at [elevenlabs.io](https://elevenlabs.io))
2. API key from your ElevenLabs dashboard
3. Python environment with Orchestra AI installed

## Configuration

### 1. Environment Variables

Add the following to your `.env` file:

```bash
# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 2. Getting Your ElevenLabs API Key

1. Sign in to [ElevenLabs](https://elevenlabs.io)
2. Navigate to your Profile Settings
3. Copy your API key from the API section

### 3. Voice Selection

ElevenLabs offers several high-quality voices. The system will automatically select the most suitable voice, prioritizing:
- Conversational voices
- Natural-sounding voices like Rachel, Antoni, or Bella
- Voices optimized for personal assistant use cases

## Features

### Voice Quality Settings

The implementation uses optimized settings for maximum realism:

```python
voice_settings = VoiceSettings(
    stability=0.75,          # Balance between consistency and expressiveness
    similarity_boost=0.85,   # High similarity to original voice
    style=0.5,              # Moderate style exaggeration
    use_speaker_boost=True  # Enhanced clarity
)
```

### Available Models

- **eleven_monolingual_v1**: Standard quality, lower latency
- **eleven_turbo_v2**: Fastest generation, good for real-time
- **eleven_multilingual_v2**: Best quality, supports multiple languages

## Usage Example

### Testing Voice Synthesis

```bash
# Run the natural language test script
python scripts/test_nl_and_agent.py
```

### Programmatic Usage

```python
from agent.app.services.natural_language_processor import ResponseGenerator

# Initialize the response generator
generator = ResponseGenerator()

# Generate speech from text
audio_url = await generator.text_to_speech("Hello, I'm your AI assistant!")
# Returns a data URL that can be played directly in browsers
```

## API Endpoints

### Text-to-Speech via Orchestra API

```bash
POST /api/agent/synthesize
Content-Type: application/json

{
  "text": "Your text to synthesize",
  "voice_settings": {
    "stability": 0.75,
    "similarity_boost": 0.85
  }
}

# Response includes audio_url with base64 encoded MP3
```

## Cost Optimization

### Usage Tiers

- **Free Tier**: 10,000 characters/month
- **Starter**: $5/month for 30,000 characters
- **Creator**: $22/month for 100,000 characters
- **Pro**: $99/month for 500,000 characters

### Best Practices for Cost Management

1. **Cache Generated Audio**: Store frequently used phrases
2. **Batch Processing**: Generate common responses in advance
3. **Use Turbo Model**: For non-critical audio where speed matters
4. **Monitor Usage**: Track character count in your application

## Advanced Features

### Real-Time Streaming (Coming Soon)

```python
# Future implementation for streaming TTS
async def stream_speech(text: str):
    async for chunk in elevenlabs_client.generate_stream(
        text=text,
        voice=voice_id,
        stream=True
    ):
        yield chunk
```

### Voice Cloning (Enterprise)

For enterprise accounts, you can create custom voices:
1. Upload voice samples (minimum 1 minute of clear audio)
2. Train the voice model
3. Use the custom voice_id in your application

## Troubleshooting

### Common Issues

1. **No Audio Generated**
   - Check API key is valid
   - Verify you have remaining character quota
   - Ensure text is not empty

2. **Poor Audio Quality**
   - Adjust stability and similarity_boost settings
   - Try different voice models
   - Check input text for special characters

3. **High Latency**
   - Use eleven_turbo_v2 model
   - Implement caching for repeated phrases
   - Consider batch processing

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

1. **API Key Protection**: Never commit API keys to version control
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Input Validation**: Sanitize text input before synthesis
4. **Audio Storage**: Secure any cached audio files

## Integration with Orchestra Personas

Each Orchestra persona can have unique voice settings:

```yaml
# In persona configuration
voice_config:
  provider: elevenlabs
  voice_id: "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
  settings:
    stability: 0.8
    similarity_boost: 0.9
    style: 0.3
```

## Monitoring and Analytics

Track voice synthesis usage:

```python
# Log synthesis requests
logger.info(f"Voice synthesis: {len(text)} characters, voice: {voice_id}")

# Monitor costs
estimated_cost = (len(text) / 1000) * 0.30  # $0.30 per 1000 chars
```

## Future Enhancements

1. **Emotion Detection**: Adjust voice parameters based on text sentiment
2. **Multi-Speaker**: Support conversations between multiple personas
3. **Voice Effects**: Add environmental effects (echo, phone, etc.)
4. **Localization**: Support for multiple languages and accents

## Support

- ElevenLabs Documentation: [docs.elevenlabs.io](https://docs.elevenlabs.io)
- Orchestra AI Issues: Create an issue in the repository
- API Status: [status.elevenlabs.io](https://status.elevenlabs.io) 