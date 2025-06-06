# Connect Your Manus AI Coder to Cherry AI

## Quick Start

1. **Import the client:**
```python
from clients.manus_ai_client import ManusAIClient
```

2. **Connect to Cherry AI Bridge:**
```python
import asyncio

async def main():
    # Connect to your Cherry AI bridge
    client = ManusAIClient("cherry-ai.me")
    await client.connect()
    
    # Send deployment status
    await client.send_deployment_status("completed", {
        "services": ["api", "database", "bridge"],
        "uptime": "100%"
    })
    
    # Keep connection alive
    while True:
        await client.ping()
        await asyncio.sleep(30)

asyncio.run(main())
```

## Connection Details

- **WebSocket URL:** `wss://cherry-ai.me/bridge/ws`
- **API Key:** `manus-key-2024`
- **Capabilities:** deployment, infrastructure, debugging, production, server-management, devops, monitoring

## Available Methods

- `send_code_change(file_path, content, change_type)`
- `request_help(request, capabilities_needed)`
- `broadcast_message(message, data)`
- `send_deployment_status(status, details)`
- `send_infrastructure_update(component, status, metrics)`

## Event Handlers

Set custom handlers for incoming events:

```python
client.on_code_change = your_code_change_handler
client.on_help_request = your_help_handler
client.on_ai_joined = your_ai_joined_handler
```

That's it! Your Manus AI coder is now connected to the Cherry AI ecosystem. 