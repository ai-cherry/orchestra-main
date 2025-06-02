#!/usr/bin/env python3
"""
Setup script for LLM configuration system
Initializes database tables and migrates existing configurations
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.llm_config_models import Base
from core.llm_router import UseCase, ModelTier, UnifiedLLMRouter

async def create_tables(db_url: str):
    """Create all LLM configuration tables"""
    engine = create_async_engine(db_url, echo=True)

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("✅ Created LLM configuration tables")

async def migrate_existing_config(db_url: str):
    """Migrate hardcoded configurations to database"""
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Get existing mappings from the router
    router = UnifiedLLMRouter()

    async with async_session() as session:
        # First, ensure providers exist
        await session.execute(
            """
            INSERT INTO llm_providers (name, api_key_env_var, base_url, priority) 
            VALUES 
                ('portkey', 'PORTKEY_API_KEY', 'https://api.portkey.ai/v1', 0),
                ('openrouter', 'OPENROUTER_API_KEY', 'https://openrouter.ai/api/v1', 1)
            ON CONFLICT (name) DO NOTHING
        """
        )

        # Insert use cases
        use_cases_data = [
            ("code_generation", "Code Generation", "Generate clean, efficient code", 0.2, 4096),
            ("architecture_design", "Architecture Design", "Design system architectures", 0.7, 8192),
            ("debugging", "Debugging", "Debug code and fix errors", 0.1, 4096),
            ("documentation", "Documentation", "Create technical documentation", 0.5, 4096),
            ("chat_conversation", "Chat Conversation", "General conversational AI", 0.7, 2048),
            ("memory_processing", "Memory Processing", "Process and structure memories", 0.3, 2048),
            ("workflow_orchestration", "Workflow Orchestration", "Orchestrate complex workflows", 0.4, 8192),
            ("general_purpose", "General Purpose", "General AI tasks", 0.5, 2048),
        ]

        for use_case, display_name, description, temp, tokens in use_cases_data:
            await session.execute(
                """
                INSERT INTO llm_use_cases 
                (use_case, display_name, description, default_temperature, default_max_tokens)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (use_case) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    description = EXCLUDED.description,
                    default_temperature = EXCLUDED.default_temperature,
                    default_max_tokens = EXCLUDED.default_max_tokens
            """,
                use_case,
                display_name,
                description,
                temp,
                tokens,
            )

        # Insert some default models
        models_data = [
            # Portkey models
            (
                "portkey",
                "anthropic/claude-3-opus",
                "Claude 3 Opus",
                '{"supports_tools": true, "max_tokens": 4096}',
                0.015,
            ),
            (
                "portkey",
                "anthropic/claude-3-sonnet",
                "Claude 3 Sonnet",
                '{"supports_tools": true, "max_tokens": 4096}',
                0.003,
            ),
            (
                "portkey",
                "anthropic/claude-3-haiku",
                "Claude 3 Haiku",
                '{"supports_tools": false, "max_tokens": 4096}',
                0.00025,
            ),
            ("portkey", "openai/gpt-4-turbo", "GPT-4 Turbo", '{"supports_tools": true, "max_tokens": 4096}', 0.01),
            ("portkey", "openai/gpt-4", "GPT-4", '{"supports_tools": true, "max_tokens": 8192}', 0.03),
            (
                "portkey",
                "openai/gpt-3.5-turbo",
                "GPT-3.5 Turbo",
                '{"supports_tools": true, "max_tokens": 4096}',
                0.0005,
            ),
            (
                "portkey",
                "google/gemini-1.5-pro",
                "Gemini 1.5 Pro",
                '{"supports_tools": true, "max_tokens": 8192}',
                0.007,
            ),
            (
                "portkey",
                "google/gemini-1.5-flash",
                "Gemini 1.5 Flash",
                '{"supports_tools": false, "max_tokens": 8192}',
                0.00035,
            ),
            # OpenRouter models (as fallback)
            (
                "openrouter",
                "anthropic/claude-3-opus:beta",
                "Claude 3 Opus",
                '{"supports_tools": true, "max_tokens": 4096}',
                0.015,
            ),
            (
                "openrouter",
                "anthropic/claude-3-sonnet:beta",
                "Claude 3 Sonnet",
                '{"supports_tools": true, "max_tokens": 4096}',
                0.003,
            ),
            (
                "openrouter",
                "google/gemini-pro-1.5",
                "Gemini 1.5 Pro",
                '{"supports_tools": true, "max_tokens": 8192}',
                0.007,
            ),
            (
                "openrouter",
                "mistralai/mixtral-8x7b",
                "Mixtral 8x7B",
                '{"supports_tools": false, "max_tokens": 32768}',
                0.00024,
            ),
        ]

        # Get provider IDs
        provider_result = await session.execute("SELECT id, name FROM llm_providers")
        providers = {row[1]: row[0] for row in provider_result}

        for provider_name, model_id, display_name, capabilities, cost in models_data:
            if provider_name in providers:
                await session.execute(
                    """
                    INSERT INTO llm_models 
                    (provider_id, model_identifier, display_name, capabilities, cost_per_1k_tokens, is_available)
                    VALUES ($1, $2, $3, $4::jsonb, $5, true)
                    ON CONFLICT (provider_id, model_identifier) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        capabilities = EXCLUDED.capabilities,
                        cost_per_1k_tokens = EXCLUDED.cost_per_1k_tokens,
                        is_available = EXCLUDED.is_available
                """,
                    providers[provider_name],
                    model_id,
                    display_name,
                    capabilities,
                    cost,
                )

        # Now migrate the model assignments from hardcoded mappings
        # Get use case and model IDs
        use_case_result = await session.execute("SELECT id, use_case FROM llm_use_cases")
        use_cases = {row[1]: row[0] for row in use_case_result}

        model_result = await session.execute("SELECT id, model_identifier FROM llm_models")
        models = {row[1]: row[0] for row in model_result}

        # Migrate mappings
        for use_case_enum, tier_mappings in router.MODEL_MAPPINGS.items():
            use_case_id = use_cases.get(use_case_enum.value)
            if not use_case_id:
                continue

            for tier_enum, mapping in tier_mappings.items():
                primary_model_id = models.get(mapping.primary_model)
                if not primary_model_id:
                    continue

                # Insert assignment
                result = await session.execute(
                    """
                    INSERT INTO llm_model_assignments
                    (use_case_id, tier, primary_model_id, temperature_override, max_tokens_override, system_prompt_override)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (use_case_id, tier) DO UPDATE SET
                        primary_model_id = EXCLUDED.primary_model_id,
                        temperature_override = EXCLUDED.temperature_override,
                        max_tokens_override = EXCLUDED.max_tokens_override,
                        system_prompt_override = EXCLUDED.system_prompt_override
                    RETURNING id
                """,
                    use_case_id,
                    tier_enum.value,
                    primary_model_id,
                    mapping.temperature,
                    mapping.max_tokens,
                    mapping.system_prompt,
                )

                assignment_id = result.scalar()

                # Insert fallback models
                for priority, fallback_model in enumerate(mapping.fallback_models):
                    fallback_model_id = models.get(fallback_model)
                    if fallback_model_id:
                        await session.execute(
                            """
                            INSERT INTO llm_fallback_models
                            (assignment_id, model_id, priority)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (assignment_id, model_id) DO UPDATE SET
                                priority = EXCLUDED.priority
                        """,
                            assignment_id,
                            fallback_model_id,
                            priority,
                        )

        await session.commit()

    await engine.dispose()
    print("✅ Migrated existing configurations to database")

async def update_env_example():
    """Update env.example with new variables"""
    env_example_path = Path(__file__).parent.parent / "env.example"

    new_vars = """
# LLM Router Configuration
PORTKEY_API_KEY=your_portkey_api_key_here
PORTKEY_CONFIG=your_portkey_config_id_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# OpenRouter Configuration (optional)
OR_SITE_URL=https://your-site.com
OR_APP_NAME=Orchestra AI
"""

    # Read existing content
    if env_example_path.exists():
        content = env_example_path.read_text()

        # Check if LLM config already exists
        if "LLM Router Configuration" not in content:
            # Append new variables
            with open(env_example_path, "a") as f:
                f.write("\n" + new_vars)
            print("✅ Updated env.example with LLM configuration variables")
    else:
        print("⚠️  env.example not found")

async def main():
    """Run the setup process"""
    print("🚀 Setting up LLM Configuration System")

    # Get database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/orchestra")

    # Ensure it's async
    if not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    try:
        # Create tables
        await create_tables(db_url)

        # Migrate existing configurations
        await migrate_existing_config(db_url)

        # Update env.example
        await update_env_example()

        print("\n✅ LLM Configuration System setup complete!")
        print("\n📝 Next steps:")
        print("1. Set your API keys in .env:")
        print("   - PORTKEY_API_KEY")
        print("   - OPENROUTER_API_KEY")
        print("2. Access the admin dashboard at /admin/llm")
        print("3. Configure models for each use case")
        print("4. Test configurations before deploying")

    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
