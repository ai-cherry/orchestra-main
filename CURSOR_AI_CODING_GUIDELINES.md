# 🤝 Cursor AI Coding Guidelines for the Orchestra AI Platform

This document outlines best practices for working with Cursor AI within the Orchestra AI codebase. Following these guidelines will help ensure the AI can understand the project structure, generate high-quality code, and perform complex tasks effectively.

## 🏛️ Core Architectural Principles

The AI is now configured to work with a containerized Docker environment.

1.  **Trust the `docker-compose.yml`**: This file is the single source of truth for the application's architecture. When asking the AI to perform tasks, assume it understands the services defined here (`api`, `frontend`, `mcp_server`).
2.  **Code is Mounted, Not Just Copied**: The `docker-compose.yml` uses `volumes` to mount the local source code into the running containers. This means changes made locally (or by the AI) are reflected instantly in the running services (the backend services will auto-reload).
3.  **Environment Variables are Key**: Use the `environment` section in `docker-compose.yml` for configuration. Avoid hardcoding values like API keys, database URLs, or ports.

## ✍️ Best Practices for Prompting

### Be Specific and Contextual

-   **Bad Prompt**: `Fix the website.`
-   **Good Prompt**: `The System Monitor page at http://localhost:3000/system-monitor is not displaying real-time CPU usage. The data is available from the `/api/system/status` endpoint. Please wire up the frontend component at `web/src/pages/SystemMonitor.tsx` to fetch and display this data.`

### Reference the Architecture

When asking for changes, reference the service names from `docker-compose.yml`.

-   **Example**: "Add a new endpoint to the `api` service for listing user agents. This should be exposed at `/api/agents` and should query the SQLite database."

### For New Features, Think in Services

If you want to add a new component, think about which service it belongs to.

-   **Example**: "I need a new service that handles image processing. Let's call it `image-processor`, add it to the `docker-compose.yml`, and create a basic Flask server for it in a new `image_processor/` directory."

## ✅ Common Tasks & How to Ask for Them

-   **"Add a new API endpoint"**: The AI will know to modify files within the `api/` directory, and the running `api` container will automatically reload.
-   **"Change a UI component"**: The AI will modify files in `web/src/`. You may need to restart the `frontend` service or use the "Active Frontend Development" method described in the `README.md` to see changes.
-   **"Add a new Python dependency"**: "Please add `scikit-learn` to the `api` service." The AI should know to add it to `requirements.txt` and that a rebuild of the container (`docker-compose build api`) will be needed.

By adhering to these guidelines, you can leverage Cursor AI as a true collaborator that understands the robust, containerized architecture of your project, leading to faster development and more reliable results. 