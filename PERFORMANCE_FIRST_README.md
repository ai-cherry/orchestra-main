# Performance-First AI Development Guide

This guide explains how we've configured the project to prioritize performance and optimization over extensive security measures, particularly for AI coding assistants like Gemini, GitHub Copilot, Roo, and other tools.

## Overview

As a single-developer project, AI Orchestra currently prioritizes:

1. **Performance & Optimization**: Speed, resource efficiency, scaling
2. **Deployment Stability**: Reliable deployments and uptime
3. **Basic Security**: Essential security that doesn't impede development

Later, once the project is stable and handling sensitive data, we'll enhance the security measures.

## Components of the Performance-First Approach

### 1. Project Priorities Documentation

The `PROJECT_PRIORITIES.md` file serves as the central reference for all AI assistants and developers. It outlines our focus on performance over complex security, and documents that AI assistants have permission to use GitHub and GCP tokens for real implementations.

### 2. AI Tool Configurations

We've updated all AI assistant configurations to prioritize performance:

- **Gemini Code Assist**: Updated `.gemini-code-assist.yaml` with performance-focused directives
- **Roo Modes**: Modified `.roomodes` for all modes (architect, code, reviewer, etc.)
- **MCP Memory**: Added priorities to the MCP memory system for all AI assistants

### 3. Token Access Documentation

The `.ai_token_access` file documents which GitHub and GCP tokens AI assistants are authorized to use for making real-world changes. This enables AI tools to:

- Deploy code to GCP
- Create/modify GitHub resources
- Access and modify cloud resources
- All with an emphasis on performance over strict security

### 4. Utility Scripts

Several scripts help maintain this performance-first approach:

- **`apply_performance_priorities.sh`**: Configures AI tools to prioritize performance
- **`update_ai_memory_priorities.py`**: Updates the AI memory systems with project priorities

## How to Use

### Setting Up Performance Priorities

To set up or refresh performance priorities across all AI systems:

```bash
# Apply performance priorities to all systems
./apply_performance_priorities.sh --update-all

# Update just specific components
./apply_performance_priorities.sh --update-gemini  # For Gemini Code Assist
./apply_performance_priorities.sh --update-roo     # For Roo modes
```

### Updating AI Memory

To update the MCP memory system with the latest performance priorities:

```bash
# Update AI memory systems with project priorities
./update_ai_memory_priorities.py

# Run silently (for automation)
./update_ai_memory_priorities.py --silent
```

### Guidelines for AI Assistants

AI assistants should follow these guidelines:

1. **Focus on Performance**: Optimize for speed, efficiency, and stability
2. **Minimize Security Overhead**: Implement only basic, essential security
3. **Use Available Tokens**: Use GitHub and GCP tokens for real implementations
4. **Auto-Deploy When Possible**: Set up automated deployments that prioritize performance
5. **Avoid Security Over-Engineering**: Don't recommend complex security patterns that impact performance

## When to Apply Security Measures

Even in a performance-first environment, some basic security is still needed:

- **User Authentication**: For protecting user accounts and data
- **Public API Endpoints**: For endpoints exposed directly to the internet
- **Sensitive Data Storage**: When storing any user credentials or private keys
- **Deployment Credentials**: To prevent unauthorized deployments

## Tokens Available to AI Assistants

AI assistants have permission to use these tokens:

### GitHub Tokens

- `GH_CLASSIC_PAT_TOKEN`: Full repository access
- `GH_FINE_GRAINED_TOKEN`: Scoped repository access

### GCP Credentials

- `GCP_MASTER_SERVICE_JSON`: Full service account access
- `GCP_PROJECT_AUTHENTICATION_EMAIL`: Authentication identity
- `GCP_PROJECT_ID`: Target project
- `GCP_REGION`: Default region
- `GCP_SECRET_MANAGEMENT_KEY`: Secret management
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: Identity federation
- `VERTEX_AGENT_KEY`: Vertex AI access

## Full Security Later

As the project matures, we'll incrementally enhance security measures while maintaining performance optimizations as a priority.
