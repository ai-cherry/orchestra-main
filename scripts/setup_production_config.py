#!/usr/bin/env python3
"""
Setup production configuration for cherry_ai MCP deployment
"""

import os
import sys
import secrets
import subprocess
from pathlib import Path

def generate_ssh_key():
    """Generate SSH key pair for deployment"""
    ssh_dir = Path.home() / ".ssh"
    ssh_dir.mkdir(exist_ok=True)
    
    key_path = ssh_dir / "cherry_ai_deploy"
    
    if not key_path.exists():
        print("🔑 Generating SSH key pair...")
        subprocess.run([
            "ssh-keygen", "-t", "rsa", "-b", "4096",
            "-f", str(key_path),
            "-N", "",  # No passphrase
            "-C", "conductor-mcp-deploy"
        ], check=True)
        print(f"  ✓ SSH key generated: {key_path}")
    else:
        print(f"  ✓ SSH key already exists: {key_path}")
        
    return str(key_path)

def update_env_file():
    """Update .env file with production values"""
    print("\n📝 Updating .env file for production...")
    
    env_file = Path(".env")
    
    # Read current env
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Update with production values
    updates = {
        # Generate secure passwords if not set
        "POSTGRES_PASSWORD": env_vars.get("POSTGRES_PASSWORD") or secrets.token_urlsafe(32),
        "GRAFANA_PASSWORD": secrets.token_urlsafe(16),
        
        # Set production URLs (will be updated after deployment)
        "API_URL": "https://api.conductor-mcp.com",
        "GRAFANA_URL": "https://grafana.conductor-mcp.com",
        
        # Production settings
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
        
        # Performance settings
        "MAX_CONCURRENT_REQUESTS": "200",
        "MEMORY_LIMIT": "8192",
        "CPU_LIMIT": "4",
        
        # Security
        "SECURE_COOKIES": "true",
        "SESSION_TIMEOUT": "3600",
        
        # Monitoring
        "PROMETHEUS_PORT": "9090",
        "GRAFANA_PORT": "3000",
        "METRICS_PORT": "9091",
    }
    
    # Apply updates
    for key, value in updates.items():
        env_vars[key] = value
    
    # Write back
    with open(env_file, 'w') as f:
        f.write("# cherry_ai MCP Production Configuration\n")
        f.write("# Auto-generated - DO NOT COMMIT WITH SECRETS\n\n")
        
        categories = {
            "Security": ["SECRET_KEY", "JWT_SECRET", "ENCRYPTION_KEY", "API_KEY", "PASSWORD_SALT", "SESSION_SECRET", "COOKIE_SECRET"],
            "Database": ["DATABASE_URL", "POSTGRES_", "REDIS_URL", "MONGODB_URI"],
            "API Keys": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY", "PORTKEY_API_KEY", "VULTR_API_KEY"],
            "Services": ["WEAVIATE_", "MCP_", "API_"],
            "Monitoring": ["PROMETHEUS_", "GRAFANA_", "METRICS_", "SENTRY_", "LOG_LEVEL"],
            "Communication": ["SMTP_", "SLACK_", "ALERT_", "MONITOR_"],
            "Performance": ["CACHE_", "MEMORY_", "CPU_", "MAX_", "OPTIMIZE_", "CIRCUIT_"],
            "Other": []
        }
        
        written_keys = set()
        
        for category, prefixes in categories.items():
            category_vars = {}
            
            if prefixes:  # Categories with prefixes
                for key, value in env_vars.items():
                    if any(key.startswith(prefix) for prefix in prefixes) and key not in written_keys:
                        category_vars[key] = value
                        written_keys.add(key)
            
            if category_vars:
                f.write(f"# {category}\n")
                for key in sorted(category_vars.keys()):
                    f.write(f"{key}={category_vars[key]}\n")
                f.write("\n")
        
        # Write remaining vars
        remaining_vars = {k: v for k, v in env_vars.items() if k not in written_keys}
        if remaining_vars:
            f.write("# Other\n")
            for key in sorted(remaining_vars.keys()):
                f.write(f"{key}={remaining_vars[key]}\n")
    
    print("  ✓ Environment file updated")
    
    # Create .env.production for reference
    prod_env = Path(".env.production")
    with open(prod_env, 'w') as f:
        f.write("# Production Environment Template\n")
        f.write("# Copy this to .env and fill in your actual values\n\n")
        
        critical_vars = {
            "VULTR_API_KEY": "<your-vultr-api-key>",
            "OPENAI_API_KEY": "<your-openai-api-key>",
            "ANTHROPIC_API_KEY": "<your-anthropic-api-key>",
            "SMTP_PASSWORD": "<your-smtp-password>",
            "SLACK_WEBHOOK_URL": "<your-slack-webhook>",
            "GITHUB_TOKEN": "<your-github-token>",
            "SENTRY_DSN": "<your-sentry-dsn>",
        }
        
        for key, placeholder in critical_vars.items():
            f.write(f"{key}={placeholder}\n")
    
    print("  ✓ Created .env.production template")

def setup_pulumi():
    """Setup Pulumi configuration"""
    print("\n🔧 Setting up Pulumi...")
    
    # Ensure we're logged in to Pulumi
    try:
        subprocess.run(["pulumi", "whoami"], check=True, capture_output=True)
        print("  ✓ Pulumi already logged in")
    except:
        print("  ⚠️  Pulumi not logged in. Logging in to local backend...")
        subprocess.run(["pulumi", "login", "--local"], check=True)
    
    # Install Pulumi Vultr plugin
    print("  📦 Installing Pulumi Vultr plugin...")
    subprocess.run(["pulumi", "plugin", "install", "resource", "vultr"], check=True)
    print("  ✓ Pulumi setup complete")

def create_deployment_checklist():
    """Create deployment checklist script"""
    print("\n📋 Creating deployment checklist...")
    
    checklist = Path("scripts/deployment_checklist.sh")
    checklist.write_text("""#!/bin/bash
# cherry_ai MCP Deployment Checklist

echo "🚀 cherry_ai MCP Production Deployment Checklist"
echo "=============================================="
echo ""

# Function to check requirement
check_requirement() {
    local name=$1
    local check_cmd=$2
    local help_text=$3
    
    echo -n "Checking $name... "
    if eval "$check_cmd" > /dev/null 2>&1; then
        echo "✓"
        return 0
    else
        echo "❌"
        echo "  → $help_text"
        return 1
    fi
}

# Track failures
FAILED=0

# Check requirements
check_requirement "Pulumi installed" "which pulumi" "Install: curl -fsSL https://get.pulumi.com | sh" || ((FAILED++))
check_requirement "Docker installed" "which docker" "Install: curl -fsSL https://get.docker.com | sh" || ((FAILED++))
check_requirement "Python 3.8+" "python3 --version | grep -E '3\.(8|9|10|11|12)'" "Install Python 3.8 or higher" || ((FAILED++))
check_requirement "SSH key exists" "test -f ~/.ssh/cherry_ai_deploy" "Run: python3 scripts/setup_production_config.py" || ((FAILED++))
check_requirement ".env file exists" "test -f .env" "Copy .env.example to .env" || ((FAILED++))
check_requirement "VULTR_API_KEY set" "grep -q 'VULTR_API_KEY=.' .env" "Add your Vultr API key to .env" || ((FAILED++))

echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ All requirements met! Ready to deploy."
    echo ""
    echo "Next steps:"
    echo "1. Review and update .env with production values"
    echo "2. Run: python3 scripts/deploy_to_vultr.py"
else
    echo "❌ $FAILED requirement(s) failed. Please fix before deploying."
    exit 1
fi
""")
    
    checklist.chmod(0o755)
    print(f"  ✓ Created deployment checklist: {checklist}")

def main():
    print("🚀 Setting up cherry_ai MCP for Production Deployment")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Generate SSH key
    ssh_key_path = generate_ssh_key()
    
    # Update environment
    update_env_file()
    
    # Setup Pulumi
    setup_pulumi()
    
    # Create checklist
    create_deployment_checklist()
    
    print("\n✅ Production setup complete!")
    print("\n📋 Next steps:")
    print("1. Update .env with your production API keys:")
    print("   - VULTR_API_KEY (required)")
    print("   - OPENAI_API_KEY / ANTHROPIC_API_KEY (for AI features)")
    print("   - SMTP_PASSWORD (for email alerts)")
    print("   - SLACK_WEBHOOK_URL (for Slack alerts)")
    print("\n2. Run deployment checklist:")
    print("   ./scripts/deployment_checklist.sh")
    print("\n3. Deploy to Vultr:")
    print("   python3 scripts/deploy_to_vultr.py")
    
    # Set SSH key path in environment
    print(f"\n💡 SSH key path: {ssh_key_path}")
    print(f"   Export: export SSH_PRIVATE_KEY_PATH={ssh_key_path}")

if __name__ == "__main__":
    main()