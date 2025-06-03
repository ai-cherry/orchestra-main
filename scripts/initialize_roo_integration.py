# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""Initialize and test Roo AI Orchestrator integration."""
    """Check if required environment variables are set."""
        "OPENROUTER_API_KEY",
        "POSTGRES_HOST",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    ]
    
    optional_vars = [
        ("WEAVIATE_URL", "http://localhost:8080"),
        ("OPENAI_API_KEY", None),
        ("ORCHESTRATOR_URL", "http://localhost:8000"),
    ]

    missing = []
    warnings = []
    
    # Check required variables
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    # Check optional variables
    for var, default in optional_vars:
        if not os.getenv(var):
            if default:
                warnings.append(f"{var} not set, using default: {default}")
                os.environ[var] = default
            else:
                warnings.append(f"{var} not set, some features may be disabled")

    if missing:
        console.print(
            f"[red]Missing required environment variables: {', '.join(missing)}[/red]"
        )
        return False
    
    if warnings:
        for warning in warnings:
            console.print(f"[yellow]Warning: {warning}[/yellow]")

    return True


async def run_database_migration() -> bool:
    """Run database migration for Roo integration tables."""
        migration_file = Path(__file__).parent.parent / "migrations" / "add_roo_integration_tables.sql"
        
        if not migration_file.exists():
            console.print(f"[red]Migration file not found: {migration_file}[/red]")
            return False

        async with UnifiedDatabase() as db:
            # Read and execute migration
            migration_sql = migration_file.read_text()
            
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            
            for statement in statements:
                if statement:
                    await db.execute(statement)
            
            console.print("[green]✓ Database migration completed successfully[/green]")
            return True

    except Exception:


        pass
        console.print(f"[red]Database migration failed: {e}[/red]")
        logger.error(f"Migration error: {e}", exc_info=True)
        return False


async def test_roo_adapter() -> bool:
    """Test Roo MCP adapter functionality."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        adapter = RooMCPAdapter(api_key)

        # Test mode wrapping
        agent_id, capabilities = await adapter.wrap_mode_as_agent(RooMode.CODE)
        console.print(f"[green]✓ Wrapped CODE mode as agent: {agent_id}[/green]")

        # Test context transformation
        roo_context = {
            "mode": RooMode.CODE,
            "task": "Test task",
            "history": [],
            "files": ["test.py"],
        }
        mcp_context = await adapter.transform_context("roo", "mcp", roo_context)
        console.print("[green]✓ Context transformation successful[/green]")

        # Test session management
        session_id = await adapter.create_session(RooMode.CODE, "Test session")
        console.print(f"[green]✓ Created session: {session_id}[/green]")

        await adapter.close_session(session_id)
        await adapter.close()

        return True

    except Exception:


        pass
        console.print(f"[red]Roo adapter test failed: {e}[/red]")
        logger.error(f"Adapter test error: {e}", exc_info=True)
        return False


async def test_unified_router() -> bool:
    """Test unified API router functionality."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
        
        router = UnifiedAPIRouter(
            api_key,
            orchestrator_url,
            "https://openrouter.ai/api/v1",
        )

        # Test routing decisions
        decision = router._make_routing_decision(
            "workflow", {"task": "coordinate agents"}
        )
        console.print(
            f"[green]✓ Routing decision: {decision.service.value} "
            f"(confidence: {decision.confidence:.2f})[/green]"
        )

        # Test circuit breaker
        breaker = router.circuit_breakers["openrouter"]
        console.print(
            f"[green]✓ Circuit breaker state: {breaker.state.value}[/green]"
        )

        # Test service health
        health = router.get_service_health()
        console.print("[green]✓ Service health check successful[/green]")

        await router.close()
        return True

    except Exception:


        pass
        console.print(f"[red]Unified router test failed: {e}[/red]")
        logger.error(f"Router test error: {e}", exc_info=True)
        return False


async def test_transition_manager() -> bool:
    """Test mode transition manager functionality."""
            "test_session",
            RooMode.CODE,
            {"last_result": {"error": "Test error"}},
        )

        if suggestion:
            console.print(
                f"[green]✓ Suggested transition: {suggestion[0].value} - {suggestion[1]}[/green]"
            )
        else:
            console.print("[yellow]No transition suggested (expected behavior)[/yellow]")

        return True

    except Exception:


        pass
        console.print(f"[red]Transition manager test failed: {e}[/red]")
        logger.error(f"Transition manager error: {e}", exc_info=True)
        return False


async def test_context_manager() -> bool:
    """Test unified context manager functionality."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        
        context_manager = UnifiedContextManager(
            weaviate_url,
            api_key,
        )

        # Test context sync
        roo_context = {
            "mode": RooMode.CODE.value,
            "task": "Test task",
            "result": "Test result",
            "history": [],
            "files": [],
        }

        mcp_context = await context_manager.sync_context_bidirectional(
            "test_session", "roo", roo_context
        )

        console.print("[green]✓ Context synchronization successful[/green]")

        # Test transition tracking
        await context_manager.track_mode_transition(
            "test_session",
            RooMode.CODE,
            RooMode.DEBUG,
            {"reason": "test"},
        )

        console.print("[green]✓ Transition tracking successful[/green]")

        return True

    except Exception:


        pass
        console.print(f"[red]Context manager test failed: {e}[/red]")
        logger.error(f"Context manager error: {e}", exc_info=True)
        return False


def display_configuration() -> None:
    """Display current Roo integration configuration."""
    config_file = Path(__file__).parent.parent / "config" / "roo_mode_mappings.yaml"
    
    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        # Create modes table
        table = Table(title="Roo Mode Configurations")
        table.add_column("Mode", style="cyan")
        table.add_column("Model", style="green")
        table.add_column("Capabilities", style="yellow")
        
        for mode, settings in config["roo_modes"].items():
            capabilities = ", ".join(settings["capabilities"][:3])
            if len(settings["capabilities"]) > 3:
                capabilities += f" (+{len(settings['capabilities']) - 3} more)"
            
            table.add_row(
                mode,
                settings["model"],
                capabilities,
            )
        
        console.print(table)
    else:
        console.print("[yellow]Configuration file not found[/yellow]")


async def main() -> int:
    """Main initialization function."""
    console.print(Panel.fit("🚀 Roo AI Orchestrator Integration Initializer", style="bold blue"))
    
    # Check environment
    console.print("\n[bold]Checking environment...[/bold]")
    if not await check_environment():
        return 1
    
    # Run database migration
    console.print("\n[bold]Running database migration...[/bold]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Migrating database...", total=None)
        if not await run_database_migration():
            return 1
        progress.update(task, completed=True)
    
    # Display configuration
    console.print("\n[bold]Current Configuration:[/bold]")
    display_configuration()
    
    # Run tests
    console.print("\n[bold]Running integration tests...[/bold]")
    
    tests = [
        ("Roo MCP Adapter", test_roo_adapter),
        ("Unified API Router", test_unified_router),
        ("Mode Transition Manager", test_transition_manager),
        ("Unified Context Manager", test_context_manager),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        console.print(f"\nTesting {test_name}...")
        if not await test_func():
            all_passed = False
    
    # Summary
    console.print("\n" + "=" * 50)
    if all_passed:
        console.print(
            Panel.fit(
                "✅ All tests passed! Roo integration is ready.",
                style="bold green",
            )
        )
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Ensure all required environment variables are set")
        console.print("2. Start Weaviate (if using vector search features)")
        console.print("3. Start the orchestrator service")
        console.print("4. Use the Roo modes through the MCP interface")
        console.print("\n[bold]Environment variables:[/bold]")
        console.print("Required:")
        console.print("  - OPENROUTER_API_KEY: Your OpenRouter API key")
        console.print("  - POSTGRES_*: Database connection settings")
        console.print("Optional:")
        console.print("  - WEAVIATE_URL: Weaviate instance URL (default: http://localhost:8080)")
        console.print("  - OPENAI_API_KEY: For Weaviate vectorization")
        console.print("  - ORCHESTRATOR_URL: Orchestrator service URL (default: http://localhost:8000)")
        return 0
    else:
        console.print(
            Panel.fit(
                "❌ Some tests failed. Please check the logs.",
                style="bold red",
            )
        )
        return 1


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("logs/roo_integration_init.log"),
            logging.StreamHandler(),
        ],
    )
    
    # Run main
    sys.exit(asyncio.run(main()))