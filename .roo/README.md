# Roo Configuration for cherry_ai Project

This directory contains the Roo configuration for the Cherry AI project, optimized for single-developer, AI-assisted workflows.

## Overview

Roo has been configured with 10 specialized modes, each using specific OpenRouter models:

### Mode Assignments

| Mode | Model | Purpose |
|------|-------|---------|
| 🏗 Architect | anthropic/claude-opus-4 | System design and architecture |
| 💻 Developer | google/gemini-2.5-flash-preview-05-20 | Code implementation |
| 🪲 Debugger | openai/gpt-4.1 | Systematic debugging |
| 🪃 conductor | anthropic/claude-sonnet-4 | Workflow coordination |
| 🧠 Strategist | anthropic/claude-opus-4 | Technical planning |
| 🔍 Researcher | anthropic/claude-sonnet-4 | Best practices research |
| 📊 Analytics | google/gemini-2.5-flash-preview-05-20 | Data analysis |
| ⚙️ Implementation | google/gemini-2.5-flash-preview-05-20 | Deployment operations |
| ✅ Quality Control | openai/gpt-4.1 | Testing and validation |
| 📝 Documentation | anthropic/claude-sonnet-4 | Knowledge management |

## Directory Structure

```
.roo/
├── modes/              # Mode configuration files
│   ├── architect.json
│   ├── code.json
│   ├── debug.json
│   └── ...
├── rules-{mode}/       # Mode-specific rules
│   └── 01-*.md        # Rule files (numbered for order)
├── scripts/            # Utility scripts
│   └── verify_setup.py # Setup verification
└── mcp.json           # MCP server configuration
```

## MCP Integration

The project includes three MCP servers:

1. **memory-bank**: Persistent memory storage for contexts
2. **portkey-router**: Model routing and management
3. **conductor-mcp**: Project-specific tools for context, vector search, database, deployment, and monitoring

## Usage

1. **Switching Modes**: Use `switch to [mode] mode` in Roo
2. **Testing**: Run `python3 .roo/scripts/verify_setup.py` to verify setup
3. **Adding Rules**: Add new `.md` files to `rules-{mode}/` directories
4. **Updating Modes**: Edit JSON files in `modes/` directory

## Important Notes

- **Never edit mode settings in Roo UI** - JSON files are the source of truth
- **Close and reopen Roo** after making configuration changes
- **Ensure MCP servers are running** before starting Roo
- **All modes use OpenRouter API** - ensure API key is configured

## Customization

To add a new mode:
1. Copy an existing mode JSON file
2. Update slug, name, and roleDefinition
3. Create corresponding `rules-{slug}/` directory
4. Add at least one rule file
5. Update MCP permissions if needed

## Troubleshooting

If modes aren't working:
1. Run the verification script
2. Check that Roo is closed when making changes
3. Verify OpenRouter API key is set
4. Ensure MCP servers are accessible
5. Check logs in Roo for errors 