#!/usr/bin/env python3
"""
Orchestra AI Setup Wizard - Complete setup and validation tool.
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


class OrchestraSetupWizard:
    """Interactive setup wizard for Orchestra AI."""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.env_file = self.root_dir / ".env"
        self.config = {}
        self.services_status = {}

    def run(self):
        """Run the setup wizard."""
        self.print_header()

        # Step 1: Environment check
        self.check_environment()

        # Step 2: Configure services
        self.configure_services()

        # Step 3: Setup project
        self.setup_project()

        # Step 4: Run tests
        self.run_tests()

        # Step 5: Summary
        self.print_summary()

    def print_header(self):
        """Print wizard header."""
        print("\n" + "=" * 60)
        print("🎼 Orchestra AI Setup Wizard")
        print("=" * 60)
        print("This wizard will help you set up Orchestra AI completely.")
        print("No more GCP! Just simple, clean configuration.\n")

    def check_environment(self):
        """Check the current environment."""
        print("📋 Step 1: Checking Environment")
        print("-" * 40)

        # Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(f"✓ Python {py_version}")

        # Virtual environment
        if os.getenv("VIRTUAL_ENV"):
            print("✓ Virtual environment active")
        else:
            print("⚠️  Virtual environment not active")

        # Docker
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            print("✓ Docker installed")
        except:
            print("✗ Docker not installed")

        # Check for .env
        if self.env_file.exists():
            print("✓ .env file exists")
            self.load_env()
        else:
            print("⚠️  .env file missing - will create one")

        print()

    def load_env(self):
        """Load existing .env file."""
        if self.env_file.exists():
            with open(self.env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        self.config[key] = value

    def configure_services(self):
        """Configure external services."""
        print("📋 Step 2: Configuring External Services")
        print("-" * 40)
        print("Let's configure your external services.\n")

        # MongoDB
        print("1️⃣ MongoDB Atlas")
        if self.config.get("MONGODB_URI"):
            print("   ✓ Already configured")
            self.services_status["mongodb"] = True
        else:
            print("   ℹ️  Sign up at: https://www.mongodb.com/cloud/atlas")
            print("   Create a free cluster and get your connection string")
            uri = input("   Enter MongoDB URI (or press Enter to skip): ").strip()
            if uri:
                self.config["MONGODB_URI"] = uri
                self.services_status["mongodb"] = True
            else:
                self.services_status["mongodb"] = False

        print()

        # DragonflyDB
        print("2️⃣ DragonflyDB (Aiven)")
        if self.config.get("DRAGONFLY_URI"):
            print("   ✓ Already configured")
            self.services_status["dragonfly"] = True
        else:
            print("   ℹ️  Sign up at: https://aiven.io/dragonfly")
            print("   Create a free instance and get your connection string")
            uri = input("   Enter Dragonfly URI (or press Enter to skip): ").strip()
            if uri:
                self.config["DRAGONFLY_URI"] = uri
                self.services_status["dragonfly"] = True
            else:
                self.services_status["dragonfly"] = False

        print()

        # Weaviate
        print("3️⃣ Weaviate Cloud")
        if self.config.get("WEAVIATE_URL") and self.config.get("WEAVIATE_API_KEY"):
            print("   ✓ Already configured")
            self.services_status["weaviate"] = True
        else:
            print("   ℹ️  Sign up at: https://console.weaviate.cloud")
            print("   Create a free sandbox cluster")
            url = input("   Enter Weaviate URL (or press Enter to skip): ").strip()
            if url:
                self.config["WEAVIATE_URL"] = url
                api_key = input("   Enter Weaviate API Key: ").strip()
                self.config["WEAVIATE_API_KEY"] = api_key
                self.services_status["weaviate"] = bool(api_key)
            else:
                self.services_status["weaviate"] = False

        print()

        # LLM APIs
        print("4️⃣ LLM API Keys")
        llm_configured = 0

        for key, name in [
            ("OPENROUTER_API_KEY", "OpenRouter"),
            ("OPENAI_API_KEY", "OpenAI"),
            ("ANTHROPIC_API_KEY", "Anthropic"),
        ]:
            if self.config.get(key):
                print(f"   ✓ {name} configured")
                llm_configured += 1
            else:
                print(f"   ⚠️  {name} not configured")

        self.services_status["llm"] = llm_configured > 0

        # Set defaults
        self.config.setdefault("ENVIRONMENT", "development")
        self.config.setdefault("REDIS_HOST", "localhost")
        self.config.setdefault("REDIS_PORT", "6379")
        self.config.setdefault("SITE_URL", "http://localhost:8000")
        self.config.setdefault("SITE_TITLE", "Orchestra AI Development")

        # Save configuration
        self.save_env()
        print("\n✓ Configuration saved to .env")
        print()

    def save_env(self):
        """Save configuration to .env file."""
        with open(self.env_file, "w") as f:
            f.write("# Orchestra AI Environment Configuration\n")
            f.write(f"# Generated by Setup Wizard on {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Group by category
            categories = {
                "Environment": ["ENVIRONMENT"],
                "External Services": [
                    "MONGODB_URI",
                    "DRAGONFLY_URI",
                    "WEAVIATE_URL",
                    "WEAVIATE_API_KEY",
                ],
                "Local Services": ["REDIS_HOST", "REDIS_PORT"],
                "LLM APIs": [
                    "OPENROUTER_API_KEY",
                    "OPENAI_API_KEY",
                    "ANTHROPIC_API_KEY",
                    "PORTKEY_API_KEY",
                ],
                "Application": ["SITE_URL", "SITE_TITLE"],
            }

            for category, keys in categories.items():
                f.write(f"# {category}\n")
                for key in keys:
                    if key in self.config:
                        f.write(f"{key}={self.config[key]}\n")
                f.write("\n")

    def setup_project(self):
        """Setup project files and dependencies."""
        print("📋 Step 3: Setting Up Project")
        print("-" * 40)

        # Update MCP configuration
        print("Updating MCP configuration...")
        old_mcp = self.root_dir / ".mcp.json"
        new_mcp = self.root_dir / ".mcp-clean.json"
        if new_mcp.exists():
            shutil.copy(new_mcp, old_mcp)
            print("✓ MCP configuration updated")

        # Install dependencies
        print("\nInstalling dependencies...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    "requirements/base.txt",
                    "--quiet",
                ],
                check=True,
            )
            print("✓ Dependencies installed")
        except:
            print("⚠️  Some dependencies failed to install")

        print()

    def run_tests(self):
        """Run validation tests."""
        print("📋 Step 4: Running Validation Tests")
        print("-" * 40)

        if not all([self.services_status.get("mongodb"), self.services_status.get("llm")]):
            print("⚠️  Skipping tests - not all services configured")
            print("   Configure MongoDB and at least one LLM API to run tests")
            return

        print("Running test suite...")
        try:
            result = subprocess.run(
                [sys.executable, "scripts/test_new_setup.py"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print("✓ All tests passed!")
            else:
                print("⚠️  Some tests failed")
                print("   Run 'python scripts/test_new_setup.py' for details")
        except Exception as e:
            print(f"✗ Test suite error: {e}")

        print()

    def print_summary(self):
        """Print setup summary."""
        print("📋 Summary")
        print("=" * 60)

        print("\n🔧 Service Configuration:")
        print(f"  MongoDB Atlas: {'✅ Configured' if self.services_status.get('mongodb') else '❌ Not configured'}")
        print(f"  DragonflyDB:   {'✅ Configured' if self.services_status.get('dragonfly') else '❌ Not configured'}")
        print(f"  Weaviate:      {'✅ Configured' if self.services_status.get('weaviate') else '❌ Not configured'}")
        print(
            f"  LLM APIs:      {'✅ At least one configured' if self.services_status.get('llm') else '❌ None configured'}"
        )

        print("\n🚀 Next Steps:")

        if not self.services_status.get("mongodb"):
            print("  1. Sign up for MongoDB Atlas (free): https://www.mongodb.com/cloud/atlas")
            print("     Then run this wizard again to configure")

        if not self.services_status.get("dragonfly"):
            print("  2. (Optional) Sign up for DragonflyDB: https://aiven.io/dragonfly")
            print("     Or use local Redis for development")

        if not self.services_status.get("weaviate"):
            print("  3. (Optional) Sign up for Weaviate: https://console.weaviate.cloud")

        print("\n📚 Quick Start Commands:")
        print("  - Run tests:        python scripts/test_new_setup.py")
        print("  - Start locally:    docker-compose up")
        print("  - Deploy:           cd infra/digitalocean_deployment && pulumi up")

        print("\n✨ Your Orchestra AI is ready for development!")
        print("   No more GCP complexity - just clean, simple architecture.")
        print()

        print("\n" + "=" * 60)
        print("Orchestra setup complete!")
        print("=" * 60)
        print("You can now use Orchestra CLI and Admin UI.")
        print("=" * 60)


if __name__ == "__main__":
    wizard = OrchestraSetupWizard()
    wizard.run()
