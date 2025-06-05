# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Create all LLM configuration tables"""
    print("✅ Created LLM configuration tables")

async def migrate_existing_config(db_url: str):
    """Migrate hardcoded configurations to database"""
            """
        """
            ("code_generation", "Code Generation", "Generate clean, efficient code", 0.2, 4096),
            ("architecture_design", "Architecture Design", "Design system architectures", 0.7, 8192),
            ("debugging", "Debugging", "Debug code and fix errors", 0.1, 4096),
            ("documentation", "Documentation", "Create technical documentation", 0.5, 4096),
            ("chat_conversation", "Chat Conversation", "General conversational AI", 0.7, 2048),
            ("memory_processing", "Memory Processing", "Process and structure memories", 0.3, 2048),
            ("workflow_coordination", "Workflow coordination", "cherry_aite complex workflows", 0.4, 8192),
            ("general_purpose", "General Purpose", "General AI tasks", 0.5, 2048),
        ]

        for use_case, display_name, description, temp, tokens in use_cases_data:
            await session.execute(
                """
            """
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
        provider_result = await session.# TODO: Consider adding EXPLAIN ANALYZE for performance
execute("SELECT id, name FROM llm_providers")
        providers = {row[1]: row[0] for row in provider_result}

        for provider_name, model_id, display_name, capabilities, cost in models_data:
            if provider_name in providers:
                await session.execute(
                    """
                """
        # TODO: Run EXPLAIN ANALYZE on this query
        use_case_result = await session.execute("SELECT id, use_case FROM llm_use_cases")
        use_cases = {row[1]: row[0] for row in use_case_result}
 # TODO: Run EXPLAIN ANALYZE on this query

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
                """
                            """
                        """
    print("✅ Migrated existing configurations to database")

async def update_env_example():
    """Update env.example with new variables"""
    env_example_path = Path(__file__).parent.parent / "env.example"

    new_vars = """
"""
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
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/cherry_ai")

    # Ensure it's async
    if not db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    try:


        pass
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

    except Exception:


        pass
        print(f"\n❌ Setup failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
