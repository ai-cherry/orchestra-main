# Cursor AI Context – cherry_ai-main

The following context should be provided to the AI assistant for every session.

---

## Project Context
• Single unified Lambda server (45.32.69.157)
• Development, deployment, and production all on same server
• Direct SSH/Cursor development - no CI/CD needed
• Python 3.10 with pip/venv (no Poetry)
• Instant deployment - changes are live immediately

## Key Directories
admin-ui/          # React admin interface
agent/             # FastAPI agent service
core/              # Core conductor
mcp_server/        # MCP server components
scripts/           # Automation tools
.github/workflows/ # GitHub sync workflow

## Development Workflow
1. SSH to server or use Cursor Remote
2. Edit files directly in /root/cherry_ai-main
3. Changes are instant
4. Use `make` commands for service management

## Available Make Commands
- `make start-services` - Start all services
- `make stop-services` - Stop all services  
- `make health-check` - Check service health
- `make validate` - Run code validation
- `make service-status` - Show service status

---

_(Generated automatically 2025-05-22)_
