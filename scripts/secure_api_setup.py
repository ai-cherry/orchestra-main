#!/usr/bin/env python3
"""
"""
    """Create secure .env file from provided keys"""
    print("🔐 Setting up API keys securely...")
    
    # Base configuration template
    env_template = """
"""
    print(f"✅ Environment file created: {env_file}")
    
    # Ensure .env is in .gitignore
    ensure_gitignore_security()
    
    return len([k for k in keys.values() if k])

def ensure_gitignore_security():
    """Ensure sensitive files are in .gitignore"""
        "# Environment variables",
        ".env",
        ".env.*", 
        "*.key",
        "*.pem",
        "secrets/",
        "# API Keys",
        "api_keys.txt",
        "config/secrets.json"
    ]
    
    if gitignore_file.exists():
        content = gitignore_file.read_text()
        additions = []
        # TODO: Consider using list comprehension for better performance

        for entry in security_entries:
            if entry not in content:
                additions.append(entry)
        
        if additions:
            with open(gitignore_file, 'a') as f:
                f.write('\n' + '\n'.join(additions) + '\n')
            print(f"✅ Added {len(additions)} security entries to .gitignore")
    else:
        with open(gitignore_file, 'w') as f:
            f.write('\n'.join(security_entries) + '\n')
        print("✅ Created .gitignore with security entries")

def verify_setup():
    """Verify the current API setup"""
    print("🔍 Verifying API setup...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Count configured services
    configured_services = []
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                if value.strip() and not value.strip().startswith('${'):
                    configured_services.append(key.strip())
    
    print(f"✅ Found {len(configured_services)} configured services:")
    for service in sorted(configured_services):
        if 'API_KEY' in service or 'TOKEN' in service:
            print(f"  🔑 {service}")
        else:
            print(f"  ⚙️ {service}")
    
    return len(configured_services) > 0

if __name__ == "__main__":
    print("🚀 Secure API Setup")
    print("==================")
    
    if verify_setup():
        print("✅ API services are already configured")
        print("🔐 Keys are stored in .env (not tracked by git)")
        print("🚀 Ready to test AI integrations!")
    else:
        print("⚠️ No API configuration found")
        print("💡 Use environment variables SETUP_*_KEY to configure services")
        print("📖 See AI_SERVICES_CONFIGURATION_GUIDE.md for details") 