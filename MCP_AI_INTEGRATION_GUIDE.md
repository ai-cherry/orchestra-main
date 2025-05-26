# MCP & AI Context Integration Guide

## 🎯 Overview

Orchestra AI uses MCP (Model Context Protocol) servers and AI context files to provide intelligent coding assistance. This guide explains how everything works together.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AI CODING ASSISTANT                   │
│                  (Cursor, Claude, Roo)                   │
└────────────────────┬───────────────────┬────────────────┘
                     │                   │
                     ▼                   ▼
        ┌────────────────────┐ ┌─────────────────────┐
        │  AI Context Files  │ │    MCP Servers      │
        ├────────────────────┤ ├─────────────────────┤
        │ • ai_context_*.py  │ │ • orchestrator      │
        │ • Project rules    │ │ • memory            │
        │ • Coding patterns  │ │ • deployment        │
        └────────────────────┘ └─────────────────────┘
                     │                   │
                     ▼                   ▼
        ┌─────────────────────────────────────────────┐
        │           ORCHESTRA AI SYSTEM               │
        │  • MongoDB (persistent memory)              │
        │  • DragonflyDB (fast cache)                │
        │  • Weaviate (vector search)                │
        └─────────────────────────────────────────────┘
```

## 📁 AI Context Files (Static Guidance)

### Purpose
Provide phase-specific guidance to AI assistants without running any code.

### Files
- **`ai_context_planner.py`** - Planning phase (before coding)
- **`ai_context_coder.py`** - Implementation phase
- **`ai_context_reviewer.py`** - Code review phase
- **`ai_context_debugger.py`** - Debugging phase

### Usage
```
# In your AI prompt:
"Read ai_context_coder.py and implement a function to process user data"
```

### Key Features
- ✅ GCP-Free setup (MongoDB, DragonflyDB, Weaviate)
- ✅ Python 3.10 only (no 3.11+ features)
- ✅ pip/venv workflow (NO Poetry/Docker/Pipenv)
- ✅ External managed services
- ✅ Simple > Complex philosophy

## 🤖 MCP Servers (Dynamic Integration)

### Purpose
Provide real-time context and memory to AI assistants while coding.

### Servers

#### 1. **Orchestrator Server** (`orchestrator_server.py`)
- Manages agent coordination
- Switches between modes
- Runs workflows

#### 2. **Memory Server** (`memory_server.py`)
- Stores/retrieves memories
- Integrates with MongoDB/Redis
- Provides context from past sessions

#### 3. **Deployment Server** (`deployment_server.py`)
- Handles deployment tasks
- Integrates with DigitalOcean
- Manages infrastructure

### How MCP Works
1. **IDE Integration**: Tracks open files, cursor position, selections
2. **Memory Sync**: Shares context between different AI tools
3. **Tool Execution**: Runs specific actions (search, deploy, etc.)

## 🚀 Getting Started

### 1. Start Everything
```bash
./start_orchestra.sh
```
This starts:
- MCP servers
- Local services (if using docker-compose)
- Orchestra API

### 2. Launch AI Assistant
```bash
# For Cursor with Claude
./launch_cursor_with_claude.sh

# Or manually start Cursor
cursor .
```

### 3. Use AI Context Files
In your prompts, always reference the appropriate context file:

```
# Planning
"Read ai_context_planner.py and help me design a caching system"

# Coding
"Read ai_context_coder.py and implement the cache using Redis"

# Reviewing
"Read ai_context_reviewer.py and review this implementation"

# Debugging
"Read ai_context_debugger.py and help fix this connection error"
```

## 📋 Integration Files

### `.cursorrules`
- Configures Cursor AI behavior
- References AI context files
- Enforces project constraints

### `.roomodes`
- Defines different AI modes
- Configures model selection
- Sets temperature and capabilities

### `.mcp.json`
- MCP server configuration
- Defines available servers
- Sets capabilities and environment

## 🔍 Verification

Run the integration checker:
```bash
python scripts/mcp_integration_check.py
```

This verifies:
- AI context files are GCP-free
- MCP servers are configured
- Integration files are consistent
- No conflicting information

## 💡 Best Practices

### 1. **Always Reference Context Files**
```
# Good
"Read ai_context_coder.py and implement..."

# Bad
"Implement a function..." (no context)
```

### 2. **Use Appropriate Phase**
- Planning → `ai_context_planner.py`
- Coding → `ai_context_coder.py`
- Review → `ai_context_reviewer.py`
- Debug → `ai_context_debugger.py`

### 3. **Let MCP Handle Memory**
- Don't manually track context
- MCP servers remember previous interactions
- Automatic context window optimization

### 4. **Follow Project Constraints**
- Python 3.10 only
- pip/venv workflow
- External services (MongoDB, Redis, Weaviate)
- No GCP dependencies

## 🛠️ Troubleshooting

### MCP Servers Not Running
```bash
# Check status
ps aux | grep -E "orchestrator|memory|deployment"

# Start manually
python mcp_server/servers/orchestrator_server.py
```

### Context Files Outdated
```bash
# Check for issues
python scripts/ai_code_reviewer.py --check-file ai_context_coder.py

# Verify integration
python scripts/mcp_integration_check.py
```

### AI Not Following Rules
1. Ensure you reference context files in prompts
2. Check `.cursorrules` is present
3. Verify MCP servers are running

## 📊 Benefits

### With This Integration:
- ✅ **Consistent Code**: AI follows project patterns
- ✅ **No Repeated Explanations**: Context is automatic
- ✅ **Memory Across Sessions**: MCP remembers previous work
- ✅ **Correct Dependencies**: No Poetry/Docker mistakes
- ✅ **Proper Error Handling**: Debugger knows common issues

### Without This Integration:
- ❌ AI suggests Poetry/Docker
- ❌ Uses Python 3.11+ features
- ❌ Creates duplicate functionality
- ❌ Adds GCP dependencies
- ❌ Over-engineers solutions

## 🎯 Summary

The MCP & AI Context integration creates a "smart coding environment" where:
1. **Static guidance** from context files ensures consistency
2. **Dynamic context** from MCP servers provides memory
3. **Integration files** configure AI behavior
4. **External services** handle data persistence

This results in AI assistants that understand your project's specific requirements without constant reminders!
