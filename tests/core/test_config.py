Project: Orchestra-Main – AI Command Center

Design a full-featured admin dashboard for managing dozens of AI agents.
This is a one-user interface, optimized for solo productivity, LLM control, and agent collaboration.
Inspired by: Merlin AI UX (clean/dark/prompt-centric) + Continue.dev (deep config blocks)

🎛 Pages to include:
1. Dashboard (Merlin-style Front Page)
Dark theme, center-focused

Greeting: “Hey there, [username]”

Large prompt box (centered, glowing)

Toggle: “Orchestra Magic” [on/off]

Below prompt: Quick action buttons

Analyze latest data

Assign agent task

Create new prompt flow

Sidebar (left):

Dashboard

History

Projects

Agents

Prompts

Labs

Vault

Profile at bottom

Collapsible with just icons

2. Agents Manager (Continue-style but modern UI)
Grid of agent cards:

Agent Name

Assigned Model

Status: Online / Idle / Busy

Configure ⚙️

Open Chat 💬

Avatar or emoji icon

"➕ New Agent" button (top-right)

3. Agent Deep Configuration (Modern)
Sections (collapsibles or tabs):

General Info:

Name, icon, description, tags

LLM & Runtime:

Model: Dropdown (Claude, GPT, Mistral, etc.)

Temperature / Top P

Max tokens

Streaming: toggle

API Key or Connection

Prompt Stack:

System prompt (editable textarea)

Pre-processing rules

Dynamic injection toggle

Custom formatting scripts

Tools & Abilities:

Toggle: Web access, Files, RAG, Custom APIs

Plugins: Select from enabled list

Memory:

Short-term window size

Long-term vector toggle

Autonomy & Behavior:

Autonomy toggle

Retry limit

Feedback logic

Behavior toggles: Clarify before running, Ask for approval, Auto-correct

Save & Cancel buttons (sticky footer)

4. Agent Chatroom (Slack-style per Agent)
List of agents on left

Chat thread on right:

Messages from agent/user

File attachments

Buttons: Retry / Debug / Convert to Task

5. Performance Dashboard
Real-time metrics:

Agent uptime

Average response time

Token usage (per agent)

Active tasks

Cost estimate

Graphs: token usage vs. time, per agent

Alerts and error logs (toast style or list)

6. Projects & Tasks
Kanban or list view

Columns: Backlog, Running, Review, Done

Tasks:

Title

Agent assigned

Linked prompt / history

ETA, priority

Status badges

Reassign or mark done

7. History Log
Filters:

Date

Agent

Keyword

Table:

Timestamp

Input (truncated)

Output (truncated)

Feedback (👍 👎)

Expand → Full view

🔧 Components & Styling Guidelines
Prompt bar = large, glowing, center weight

Dark theme base: #1a1a1a

Highlight accent: Purple glow (#8b5cf6) or custom

Soft-rounded cards, subtle shadows

Use auto-layout for everything

Sidebar hover expansion

Reuse components: Cards, Toggles, Inputs, Charts

Want me to generate text-based component names and layout structure for Figma layer naming too? Or prep a design system token sheet (colors, spacing, elevation, shadows)?








"""
Tests for the configuration module.

This module contains tests for the configuration loading and persona config functionality.
"""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr

from core.orchestrator.src.config.config import Settings, load_all_persona_configs


def test_settings_default_values():
    """Test that Settings loads with default values."""
    settings = Settings()
    
    # Check basic configuration defaults
    assert settings.APP_NAME == "AI Orchestration System"
    assert settings.ENVIRONMENT == "development"
    assert settings.LOG_LEVEL == "INFO"
    
    # Check storage configuration defaults
    assert settings.GCP_PROJECT_ID is None
    assert settings.FIRESTORE_ENABLED is True
    assert settings.REDIS_ENABLED is True
    assert settings.REDIS_HOST == "localhost"
    assert settings.REDIS_PORT == 6379
    
    # Check LLM settings defaults
    assert settings.OPENROUTER_API_KEY is None
    assert settings.DEFAULT_LLM_MODEL == "openai/gpt-3.5-turbo"


@patch.dict(os.environ, {
    "ENVIRONMENT": "testing",
    "LOG_LEVEL": "DEBUG",
    "GCP_PROJECT_ID": "test-project",
    "REDIS_HOST": "redis.example.com",
    "REDIS_PORT": "6380",
    "OPENROUTER_API_KEY": "test-api-key"
})
def test_settings_from_environment():
    """Test that Settings loads values from environment variables."""
    settings = Settings()
    
    # Check values loaded from environment
    assert settings.ENVIRONMENT == "testing"
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.GCP_PROJECT_ID == "test-project"
    assert settings.REDIS_HOST == "redis.example.com"
    assert settings.REDIS_PORT == 6380
    assert isinstance(settings.OPENROUTER_API_KEY, SecretStr)
    assert settings.OPENROUTER_API_KEY.get_secret_value() == "test-api-key"


def test_load_all_persona_configs():
    """Test that persona configs are loaded correctly."""
    persona_configs = load_all_persona_configs()
    
    # Check that all expected personas are present
    assert len(persona_configs) == 3
    assert set(persona_configs.keys()) == {"cherry", "sophia", "gordon"}
    
    # Check details of a specific persona
    cherry = persona_configs["cherry"]
    assert cherry.name == "Cherry"
    assert cherry.age == 28
    assert "creativity" in cherry.traits
    assert cherry.traits["creativity"] == 85
    assert cherry.interaction_style == "playful"
    
    # Check that traits are properly loaded for all personas
    for name, persona in persona_configs.items():
        assert isinstance(persona.traits, dict)
        assert len(persona.traits) > 0
