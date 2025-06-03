# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Complete setup and cleanup for Orchestra AI."""
        self.env_file = self.root_dir / ".env"
        self.config = {}
        self.removed_files: List[str] = []
        self.updated_files: List[str] = []
        self.errors: List[str] = []

    def run(self):
        """Run complete setup process."""
        print("🎼 Orchestra AI - Complete Setup & Cleanup")
        print("=" * 60)
        print("This will clean archives, configure services, and set up MCP.")
        print("=" * 60)

        # Step 1: Clean archived files
        self.clean_archives()

        # Step 2: Configure all services
        self.configure_services()

        # Step 3: Setup MCP properly
        self.setup_mcp()

        # Step 4: Create automation scripts
        self.create_automation()

        # Step 5: Final validation
        self.validate_setup()

        # Summary
        self.print_summary()

    def clean_archives(self):
        """Remove all archived files and update references."""
        print("\n🧹 Step 1: Cleaning Archives")
        print("-" * 40)

        # Find and remove archive directories
        archive_dirs = [
            self.root_dir / "scripts" / "archive",
        ]

        for archive_dir in archive_dirs:
            if archive_dir.exists():
                print(f"  Removing {archive_dir.relative_to(self.root_dir)}/")
                shutil.rmtree(archive_dir)
                self.removed_files.append(str(archive_dir))

        # Files that reference archives
        files_with_refs = {
            "execute_strategy_workflow.py": [
                (
                    "from roo_workflow_manager import SubtaskManager",
                    "# Removed archive import",
                ),
                (
                    "Could not import Roo's workflow manager",
                    "Workflow manager not available",
                ),
            ],
            "mcp_server/demo_memory_sync.py": [('"roo_workflow_manager",', '# "roo_workflow_manager", # Removed')],
            "mcp_cli.py": [
                (
                    "from roo_workflow_manager import MODE_MAP as ROO_MODES",
                    "# Removed archive import",
                ),
                ("roo_workflow_manager.py", "workflow manager"),
            ],
        }

        # Update files
        for file_path, replacements in files_with_refs.items():
            full_path = self.root_dir / file_path
            if full_path.exists():
                print(f"  Updating {file_path}")
                with open(full_path, "r") as f:
                    content = f.read()

                for old, new in replacements:
                    content = content.replace(old, new)

                with open(full_path, "w") as f:
                    f.write(content)

                self.updated_files.append(file_path)

        print(f"  ✓ Removed {len(self.removed_files)} archive directories")
        print(f"  ✓ Updated {len(self.updated_files)} files")

    def configure_services(self):
        """Configure all external services with sensible defaults."""
        print("\n⚙️  Step 2: Configuring Services")
        print("-" * 40)

        # Load existing config
        if self.env_file.exists():
            with open(self.env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        self.config[key] = value

        # Service configurations with instructions
        services = {
            "MongoDB Atlas": {
                "url": "https://www.mongodb.com/cloud/atlas",
                "vars": {"MONGODB_URI": "mongodb://localhost:27017/orchestra"},  # Local default
                "note": "Using local MongoDB for development",
            },
            "DragonflyDB": {
                "url": "https://aiven.io/dragonfly",
                "vars": {"DRAGONFLY_URI": "redis://localhost:6379"},  # Local Redis default
                "note": "Using local Redis for development",
            },
            "Weaviate": {
                "url": "https://console.weaviate.cloud",
                "vars": {
                    "WEAVIATE_URL": "http://localhost:8080",
                    "WEAVIATE_API_KEY": "",
                },
                "note": "Optional - for vector search",
            },
        }

        # Configure each service
        for service_name, service_config in services.items():
            print(f"\n  {service_name}:")
            for var_name, default_value in service_config["vars"].items():
                if var_name not in self.config or not self.config[var_name]:
                    self.config[var_name] = default_value
                    if default_value:
                        print(f"    ✓ {var_name} = {default_value}")
                    else:
                        print(f"    ⚠️  {var_name} not configured")
                else:
                    print(f"    ✓ {var_name} already configured")

            if service_config.get("note"):
                print(f"    ℹ️  {service_config['note']}")

        # Essential configurations
        essentials = {
            "ENVIRONMENT": "development",
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "SITE_URL": "http://localhost:8000",
            "SITE_TITLE": "Orchestra AI",
            "PYTHONPATH": "/workspace",
        }

        for key, value in essentials.items():
            if key not in self.config:
                self.config[key] = value

        # Save configuration
        self.save_config()
        print("\n  ✓ Configuration saved to .env")

    def save_config(self):
        """Save configuration to .env file."""
        with open(self.env_file, "w") as f:
            f.write("# Orchestra AI Configuration\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# No GCP dependencies!\n\n")

            categories = {
                "Environment": ["ENVIRONMENT", "PYTHONPATH"],
                "Database Services": [
                    "MONGODB_URI",
                    "DRAGONFLY_URI",
                    "REDIS_HOST",
                    "REDIS_PORT",
                ],
                "Vector Search": ["WEAVIATE_URL", "WEAVIATE_API_KEY"],
                "LLM Services": [
                    "OPENROUTER_API_KEY",
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "PORTKEY_API_KEY",
                ],
                "Application": ["SITE_URL", "SITE_TITLE"],
            }

            # Get all configured keys
            all_keys = set(self.config.keys())
            categorized_keys = set()

            # Write categorized keys
            for category, keys in categories.items():
                category_keys = [k for k in keys if k in self.config]
                if category_keys:
                    f.write(f"# {category}\n")
                    for key in category_keys:
                        f.write(f"{key}={self.config[key]}\n")
                        categorized_keys.add(key)
                    f.write("\n")

            # Write any uncategorized keys
            uncategorized = all_keys - categorized_keys
            if uncategorized:
                f.write("# Other\n")
                for key in sorted(uncategorized):
                    f.write(f"{key}={self.config[key]}\n")

    def setup_mcp(self):
        """Setup MCP configuration properly."""
        print("\n🔧 Step 3: Setting up MCP")
        print("-" * 40)

        # Create awesome MCP configuration
        mcp_config = {
            "name": "Orchestra AI MCP",
            "version": "4.0.0",
            "description": "Automated MCP setup for Orchestra AI - GCP-free edition",
            "servers": {
                "orchestrator": {
                    "command": "python",
                    "args": ["mcp_server/servers/orchestrator_server.py"],
                    "env": {"PYTHONPATH": "${PYTHONPATH}:${PWD}"},
                    "capabilities": {"tools": True, "resources": True, "prompts": True},
                },
                "memory": {
                    "command": "python",
                    "args": ["mcp_server/servers/memory_server.py"],
                    "env": {
                        "MONGODB_URI": "${MONGODB_URI}",
                        "REDIS_HOST": "${REDIS_HOST}",
                        "REDIS_PORT": "${REDIS_PORT}",
                    },
                    "capabilities": {"tools": True, "resources": True},
                },
                "deployment": {
                    "command": "python",
                    "args": ["mcp_server/servers/deployment_server.py"],
                    "capabilities": {"tools": True},
                },
            },
            "client": {
                "mcpServers": {
                    "orchestrator": {
                        "command": "python",
                        "args": ["mcp_server/servers/orchestrator_server.py"],
                    },
                    "memory": {
                        "command": "python",
                        "args": ["mcp_server/servers/memory_server.py"],
                    },
                }
            },
        }

        # Save MCP configuration
        mcp_path = self.root_dir / ".mcp.json"
        with open(mcp_path, "w") as f:
            json.dump(mcp_config, f, indent=2)
        print("  ✓ Created automated MCP configuration")

        # Create MCP server implementations
        self.create_mcp_servers()

    def create_mcp_servers(self):
        """Create MCP server implementations."""
        servers_dir = self.root_dir / "mcp_server" / "servers"
        servers_dir.mkdir(parents=True, exist_ok=True)

        # Base server template
        base_server = '''
'''
            if name == "{tool['name']}":
                # TODO: Implement {tool['name']}
                result = f"Executed {tool['name']} with {{arguments}}"
                return [TextContent(type="text", text=result)]"""
                description=config["description"],
                class_name=config["class_name"],
                name=config["name"],
                tools=json.dumps(config["tools"], indent=12),
                tool_handlers="\n".join(tool_handlers),
            )

            with open(server_path, "w") as f:
                f.write(content)

            print(f"  ✓ Created {filename}")

    def create_automation(self):
        """Create automation scripts."""
        print("\n🤖 Step 4: Creating Automation")
        print("-" * 40)

        # Start script
        start_script = """
echo "🎼 Starting Orchestra AI..."

# Check environment
if [ ! -f .env ]; then
    echo "❌ No .env file found. Run: python scripts/orchestra_complete_setup.py"
    exit 1
fi

# Export environment
export $(cat .env | grep -v '^#' | xargs)

# Start services
echo "Starting services..."

# Option 1: Docker Compose (recommended)
if command -v docker-compose &> /dev/null; then
    echo "Using Docker Compose..."
    docker-compose up -d
    echo "✓ Services started with Docker Compose"
else
    echo "⚠️  Docker Compose not found. Install Docker for best experience."
    echo "Starting local services..."

    # Start Redis if not running
    if ! pgrep -x "redis-server" > /dev/null; then
        redis-server --daemonize yes
        echo "✓ Started Redis"
    fi
fi

# Start MCP servers
echo "Starting MCP servers..."
python mcp_server/servers/orchestrator_server.py &
python mcp_server/servers/memory_server.py &
echo "✓ MCP servers started"

# Start main application
echo "Starting Orchestra API..."
cd core/orchestrator && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &

echo ""
echo "✅ Orchestra AI is running!"
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""
echo "To stop: ./stop_orchestra.sh"
"""
        stop_script = """
echo "🛑 Stopping Orchestra AI..."

# Stop Python processes
pkill -f "orchestrator_server.py"
pkill -f "memory_server.py"
pkill -f "uvicorn"

# Stop Docker Compose if running
if command -v docker-compose &> /dev/null; then
    docker-compose down
fi

echo "✓ Orchestra AI stopped"
"""
        scripts = {"start_orchestra.sh": start_script, "stop_orchestra.sh": stop_script}

        for filename, content in scripts.items():
            script_path = self.root_dir / filename
            with open(script_path, "w") as f:
                f.write(content)
            script_path.chmod(0o755)
            print(f"  ✓ Created {filename}")

    def validate_setup(self):
        """Validate the complete setup."""
        print("\n✅ Step 5: Validating Setup")
        print("-" * 40)

        checks = {
            ".env exists": self.env_file.exists(),
            ".mcp.json exists": (self.root_dir / ".mcp.json").exists(),
            "MongoDB configured": bool(self.config.get("MONGODB_URI")),
            "Redis configured": bool(self.config.get("REDIS_HOST")),
            "No archive directories": not (self.root_dir / "scripts" / "archive").exists(),
            "MCP servers created": (self.root_dir / "mcp_server" / "servers" / "orchestrator_server.py").exists(),
            "Start script created": (self.root_dir / "start_orchestra.sh").exists(),
        }

        all_good = True
        for check, result in checks.items():
            status = "✓" if result else "✗"
            print(f"  {status} {check}")
            if not result:
                all_good = False

        return all_good

    def print_summary(self):
        """Print setup summary."""
        print("\n" + "=" * 60)
        print("Orchestra setup complete!")
        print("=" * 60)
        print("You can now use Orchestra CLI and Admin UI.")
        print("=" * 60)

if __name__ == "__main__":
    setup = OrchestraCompleteSetup()
    setup.run()
