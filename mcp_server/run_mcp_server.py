#!/usr/bin/env python3
"""
"""
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp-main")

class MCPApplication:
    """Main MCP application class."""
        """Initialize the MCP application."""
        """Initialize the MCP application."""
        logger.info("Initializing MCP application")

        # Initialize storage
        storage_config = self.config.get("storage", {})
        self.storage = InMemoryStorage(storage_config)

        # Initialize memory manager
        self.memory_manager = StandardMemoryManager(self.storage)

        # Dynamically discover and register all adapters in mcp_server/adapters/
        import mcp_server.adapters

        adapter_pkg = mcp_server.adapters

        for finder, name, ispkg in pkgutil.iter_modules(adapter_pkg.__path__):
            if not name.endswith("_adapter"):
                continue
            module = importlib.import_module(f"mcp_server.adapters.{name}")
            # Find the adapter class (by convention: PascalCase of file, e.g., CopilotAdapter)
            class_name = "".join([part.capitalize() for part in name.replace("_adapter", "").split("_")]) + "Adapter"
            adapter_cls = getattr(module, class_name, None)
            if adapter_cls is None:
                logger.warning(f"Adapter class {class_name} not found in {name}")
                continue
            # Get config for this adapter if present
            adapter_config = self.config.get(name.replace("_adapter", ""), {})
            adapter_instance = adapter_cls(adapter_config)
            self.memory_manager.register_tool(adapter_instance)
            self.tools[name.replace("_adapter", "")] = adapter_instance
            logger.info(f"Registered adapter: {class_name}")

        # Initialize memory manager
        init_success = await self.memory_manager.initialize()

        if init_success:
            logger.info("MCP application initialized successfully")
            self.initialized = True
            return True
        else:
            logger.error("Failed to initialize MCP application")
            return False

    async def get_status(self) -> Dict[str, Any]:
        """Get the status of the MCP application."""
            return {"status": "not_initialized"}

        # Get memory status
        memory_status = await self.memory_manager.get_memory_status()

        # Get tool statuses
        tool_statuses = {}
        for tool_name, adapter in self.tools.items():
            try:

                pass
                tool_status = await adapter.get_status()
                tool_statuses[tool_name] = tool_status
            except Exception:

                pass
                logger.error(f"Error getting status for {tool_name}: {e}")
                tool_statuses[tool_name] = {"status": "error", "error": str(e)}

        return {
            "status": "initialized",
            "memory": memory_status,
            "tools": tool_statuses,
        }

async def main_async(config_path: Optional[str] = None):
    """Async main function."""
        logger.info(f"Using configuration with log level: {config.log_level}")

        # Set the log level from config
        logging.getLogger().setLevel(config.log_level)

    except Exception:


        pass
        logger.error(f"Error loading configuration: {e}")
        logger.warning("Using default configuration")
        config = MCPConfig()

    # Create and initialize application
    app = MCPApplication(config.dict())
    init_success = await app.initialize()

    if not init_success:
        logger.error("Failed to initialize MCP application")
        return 1

    # Print application status
    status = await app.get_status()
    logger.info(f"MCP Server Status: {json.dumps(status, indent=2)}")

    # Keep the application running
    logger.info("MCP Server running. Press Ctrl+C to stop.")

    try:


        pass
        # Keep the server running until interrupted
        while True:
            await asyncio.sleep(1)
    except Exception:

        pass
        logger.info("MCP Server stopping...")

    return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MCP Memory System")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()

    exit_code = asyncio.run(main_async(args.config))
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
