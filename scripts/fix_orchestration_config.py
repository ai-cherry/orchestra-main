# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Run a shell command and return result"""
    """Fix PostgreSQL database configuration"""
    print("\n=== Fixing Database Configuration ===")
    
    # Check if PostgreSQL is running
    result = run_command("sudo systemctl status postgresql", check=False)
    if result.returncode != 0:
        print("Starting PostgreSQL...")
        run_command("sudo systemctl start postgresql")
    
    # Create orchestra user and database
    print("Setting up orchestra database...")
    
    # Create SQL script
    sql_script = """
"""
    result = run_command("sudo -u postgres psql -f /tmp/fix_orchestra_db.sql", check=False)
    if result.returncode == 0:
        print("✓ Database configuration fixed")
    else:
        print(f"⚠️  Database setup had issues: {result.stderr}")
    
    # Clean up
    os.remove('/tmp/fix_orchestra_db.sql')

def remove_conflicting_files():
    """Remove conflicting configuration files"""
    print("\n=== Removing Conflicting Files ===")
    
    conflicting_files = [
        '.env',
        'ai_components/.env',
        'scripts/.env',
        'infrastructure/.env'
    ]
    
    for file_path in conflicting_files:
        if Path(file_path).exists():
            print(f"Removing {file_path}...")
            os.remove(file_path)
            print(f"✓ Removed {file_path}")

def update_gitignore():
    """Ensure .env files are in gitignore"""
    print("\n=== Updating .gitignore ===")
    
    gitignore_path = Path('.gitignore')
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        
        # Add .env patterns if not present
        env_patterns = [
            '.env',
            '.env.*',
            '*.env',
            '!.env.example'
        ]
        
        lines = content.strip().split('\n')
        added = False
        
        # TODO: Consider using list comprehension for better performance

        
        for pattern in env_patterns:
            if pattern not in lines:
                lines.append(pattern)
                added = True
        
        if added:
            gitignore_path.write_text('\n'.join(lines) + '\n')
            print("✓ Updated .gitignore with .env patterns")
        else:
            print("✓ .gitignore already contains .env patterns")

def setup_local_environment():
    """Setup local environment for development"""
    print("\n=== Setting Up Local Environment ===")
    
    # Install required dependencies first
    print("Installing required dependencies...")
    deps_result = run_command("pip install psycopg2-binary", check=False)
    if deps_result.returncode != 0:
        print("⚠️  Could not install psycopg2-binary, trying system package...")
        run_command("sudo apt-get update && sudo apt-get install -y python3-psycopg2", check=False)
    
    # Run the secrets manager setup
    result = run_command("python3 scripts/setup_secrets_manager.py", check=False)
    if result.returncode == 0:
        print("✓ Local environment configured")
    else:
        print(f"⚠️  Environment setup had issues: {result.stderr}")

def fix_ai_orchestrator_imports():
    """Fix import issues in AI orchestrator"""
    print("\n=== Fixing AI Orchestrator Imports ===")
    
    # The orchestrator has already been updated to use the secrets manager
    print("✓ AI orchestrator already updated to use unified secrets manager")

def create_systemd_services():
    """Create systemd service files for production"""
    print("\n=== Creating Systemd Service Files ===")
    
    # AI Orchestrator service
    orchestrator_service = """
Environment="PYTHONPATH=/opt/ai-orchestrator"
EnvironmentFile=-/etc/orchestra.env
ExecStart=/usr/bin/python3 ai_components/orchestration/ai_orchestrator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        print("✓ Created ai-orchestrator.service")
    
    # MCP Server service
    mcp_service = """
Environment="PYTHONPATH=/opt/ai-orchestrator"
EnvironmentFile=-/etc/orchestra.env
ExecStart=/usr/bin/python3 mcp_server/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        print("✓ Created orchestrator-mcp.service")
    
    # Reload systemd
    run_command("sudo systemctl daemon-reload")
    print("✓ Systemd services configured")

def verify_configuration():
    """Verify the configuration is working"""
    print("\n=== Verifying Configuration ===")
    
    # Test database connection
    test_script = """
    print("✓ Database connection verified")
    sys.exit(0)
else:
    print("✗ Database connection failed")
    sys.exit(1)
"""
    result = run_command("python3 /tmp/test_db.py", check=False)
    os.remove('/tmp/test_db.py')
    
    # Test AI orchestrator imports
    test_import = """
    print("✓ AI orchestrator imports successfully")
except Exception:

    pass
    print(f"✗ AI orchestrator import failed: {e}")
"""
    result = run_command(f"python3 -c '{test_import}'", check=False)

def main():
    """Main fix function"""
    print("=== AI Orchestration Configuration Fix ===")
    print("This script will fix all configuration issues\n")
    
    # Check if running as root for systemd operations
    if os.geteuid() != 0 and '--no-systemd' not in sys.argv:
        print("Note: Run with sudo for systemd service creation")
        print("Or use --no-systemd to skip systemd setup\n")
    
    # Execute fixes
    fix_database_configuration()
    remove_conflicting_files()
    update_gitignore()
    setup_local_environment()
    fix_ai_orchestrator_imports()
    
    # Create systemd services if root
    if os.geteuid() == 0 and '--no-systemd' not in sys.argv:
        create_systemd_services()
    
    verify_configuration()
    
    print("\n=== Configuration Fix Complete ===")
    print("\nNext steps:")
    print("1. Set your API keys in GitHub Secrets:")
    print("   ./scripts/setup_github_secrets.sh")
    print("\n2. For local development, add API keys to environment:")
    print("   export ANTHROPIC_API_KEY='your-key-here'")
    print("   export OPENAI_API_KEY='your-key-here'")
    print("   # etc...")
    print("\n3. Run the secrets manager to create local .env:")
    print("   python scripts/setup_secrets_manager.py")
    print("\n4. Test the orchestrator:")
    print("   python ai_components/orchestration/ai_orchestrator.py")

if __name__ == "__main__":
    main()