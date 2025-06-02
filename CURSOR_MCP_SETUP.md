# Cursor MCP Setup Guide

## How MCP Works with Cursor

MCP (Model Context Protocol) servers are started automatically by Cursor when you open a project. They communicate via stdio (not HTTP), so they don't run as background services.

## Quick Setup for Cursor

### 1. Ensure Dependencies are Installed

```bash
cd /root/orchestra-main
source venv/bin/activate
pip install mcp psycopg weaviate-client
```

### 2. Configure Cursor Settings

Add to your Cursor settings (Cmd/Ctrl + , → Settings → MCP):

```json
{
  "mcpServers": {
    "orchestra-memory": {
      "command": "/root/orchestra-main/venv/bin/python",
      "args": ["/root/orchestra-main/mcp_server/servers/memory_server.py"],
      "env": {
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "orchestrator",
        "POSTGRES_USER": "orchestrator",
        "POSTGRES_PASSWORD": "orch3str4_2024",
        "WEAVIATE_HOST": "localhost",
        "WEAVIATE_PORT": "8080"
      }
    },
    "orchestra-orchestrator": {
      "command": "/root/orchestra-main/venv/bin/python",
      "args": ["/root/orchestra-main/mcp_server/servers/orchestrator_server.py"],
      "env": {
        "API_URL": "http://localhost:8080",
        "API_KEY": "4010007a9aa5443fc717b54e1fd7a463260965ec9e2fce297280cf86f1b3a4bd"
      }
    },
    "orchestra-tools": {
      "command": "/root/orchestra-main/venv/bin/python",
      "args": ["/root/orchestra-main/mcp_server/servers/tools_server.py"]
    }
  }
}
```

### 3. Test in Cursor

1. Restart Cursor
2. Open your project
3. In the chat, type: `@mcp` to see available servers
4. Use tools like:
   - `@orchestra-memory store_memory "Important code pattern discovered"`
   - `@orchestra-memory search_memories "authentication"`

## Troubleshooting

### Check if MCP is Active

In Cursor's chat:
```
@mcp list
```

### View MCP Logs

Cursor logs MCP output. Check:
- macOS/Linux: `~/.cursor/logs/`
- Windows: `%APPDATA%\Cursor\logs\`

### Common Issues

1. **"Module not found" errors**
   - Ensure virtual environment has all dependencies
   - Use full path to venv Python in MCP config

2. **"Connection refused" errors**
   - Check PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify Weaviate is running if using vector features

3. **MCP not showing in Cursor**
   - Restart Cursor after config changes
   - Check JSON syntax in settings

## Using MCP in Your Coding

### Store Context
When you discover important patterns or make decisions:
```
@orchestra-memory store_memory "Using PostgreSQL for all relational data, Weaviate for vectors only"
```

### Search Past Context
Before implementing something new:
```
@orchestra-memory search_memories "database architecture decisions"
```

### Add to Knowledge Base
When you find a good solution:
```
@orchestra-memory add_knowledge "Async PostgreSQL Connection Pattern" "Use psycopg pool with async context manager..."
```

## MCP is Working When...

1. You see `@orchestra-memory`, `@orchestra-orchestrator`, etc. in Cursor's autocomplete
2. Tools execute and return results
3. Memory persists between sessions

## Background Services Still Needed

While MCP servers are started by Cursor, you still need:

```bash
# PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Weaviate (if using vector features)
# Run via Docker or systemd

# API Server (if using orchestrator features)
# Run your FastAPI server
``` 