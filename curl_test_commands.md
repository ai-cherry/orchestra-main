# Curl Commands for Testing `/interact` Endpoint

Below are curl commands for testing the `/interact` endpoint with different personas and configurations.

## Basic Interaction (Default Persona and User ID)

```bash
curl -X POST "http://localhost:8000/api/interact" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?"
  }'
```

## Specifying a Custom User ID

```bash
curl -X POST "http://localhost:8000/api/interact" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "user_id": "custom_user_123"
  }'
```

## Using Different Personas

### Cherry Persona

```bash
curl -X POST "http://localhost:8000/api/interact?persona=cherry" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What's the best way to stay motivated?",
    "user_id": "test_user"
  }'
```

### Sophia Persona

```bash
curl -X POST "http://localhost:8000/api/interact?persona=sophia" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What's the meaning of life?",
    "user_id": "test_user"
  }'
```

### Gordon Gekko Persona

```bash
curl -X POST "http://localhost:8000/api/interact?persona=gordon_gekko" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "How can I improve my productivity?",
    "user_id": "test_user"
  }'
```

## Using OpenAI GPT-4o Model

```bash
curl -X POST "http://localhost:8000/api/interact?persona=cherry" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Create a short story about AI.",
    "user_id": "test_user",
    "model": "openai/gpt-4o"
  }'
```

# Common Error Troubleshooting

## LLM Timeouts

If you encounter timeout errors, try:

1. Check your internet connection
2. Verify the OPENROUTER_API_KEY in your .env file
3. Increase the timeout setting in settings.py
4. Try a different model that might be more available

## Persona Not Found

If you get a "persona not found" error:

1. Make sure the persona name is spelled correctly and in lowercase
2. Check that the persona exists in `core/orchestrator/src/config/personas.yaml`
3. Restart the server to reload the persona configurations

## Memory Issues

If you encounter memory-related errors:

1. Ensure the memory_manager is properly initialized
2. Check that user_id is being passed correctly
3. Restart the server to clear in-memory storage

## General Debug Tips

Add the following flag to see detailed logs:

```bash
uvicorn core.orchestrator.src.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

You can also check logs in the terminal where the server is running for debugging information.
