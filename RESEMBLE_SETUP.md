# Resemble AI Setup for Orchestra

## Environment Variables

Add the following to your `.env` file:

```bash
# Resemble AI Configuration
RESEMBLE_API_KEY=your_resemble_api_key_here
RESEMBLE_PROJECT_UUID=your_project_uuid  # Optional - will use default if not set
RESEMBLE_VOICE_UUID=your_voice_uuid      # Optional - will use default if not set
```

## Getting Your Resemble Credentials

1. Sign in to [Resemble AI](https://app.resemble.ai)
2. Go to Settings → API Keys
3. Copy your API key
4. (Optional) Note your project UUID and voice UUID for specific voices

## Testing Voice Integration

Run the natural language test with voice:
```bash
# Test voice synthesis
curl -X POST http://localhost:8000/api/nl/text \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_ORCHESTRA_API_KEY" \
  -d '{"text": "Hello, I am your Orchestra AI assistant"}'

# The response will include speech_url if Resemble is configured
```

## Voice Customization Options

In `agent/app/services/natural_language_processor.py`, you can customize:
- `sample_rate`: 22050 (default), 44100, 48000
- `output_format`: mp3 (default), wav, ogg
- `precision`: PCM_16 (default), PCM_24, PCM_32 