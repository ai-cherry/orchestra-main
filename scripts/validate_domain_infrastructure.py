#!/usr/bin/env python3
"""
Domain Infrastructure Validation Script
Validates the complete domain separation setup
"""

import json
import os
from pathlib import Path

def validate_domain_setup():
    """Validate domain infrastructure setup"""
    
    print("🔍 Validating Domain Infrastructure Setup")
    print("=" * 50)
    
    issues = []
    
    # Check domain directories
    print("\n📁 Checking domain directories...")
    for domain in ["Personal", "PayReady", "ParagonRX"]:
        domain_path = Path(f"domains/{domain}")
        if domain_path.exists():
            print(f"  ✅ {domain} domain directory exists")
            
            # Check subdirectories
            for subdir in ["services", "models", "api", "config", "interfaces"]:
                if (domain_path / subdir).exists():
                    print(f"     ✅ {subdir}/ exists")
                else:
                    print(f"     ❌ {subdir}/ missing")
                    issues.append(f"{domain}/{subdir} directory missing")
        else:
            print(f"  ❌ {domain} domain directory missing")
            issues.append(f"{domain} domain directory missing")
    
    # Check configuration files
    print("\n⚙️ Checking configuration files...")
    config_files = [
        "config/domains/personal_weaviate.json",
        "config/domains/payready_weaviate.json",
        "config/domains/paragonrx_weaviate.json",
        "config/domains/personal_airbyte.json",
        "config/domains/payready_airbyte.json",
        "config/domains/paragonrx_airbyte.json"
    ]
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"  ✅ {config_file}")
            
            # Validate JSON
            try:
                with open(config_file) as f:
                    json.load(f)
                print(f"     ✅ Valid JSON")
            except json.JSONDecodeError as e:
                print(f"     ❌ Invalid JSON: {e}")
                issues.append(f"{config_file} has invalid JSON")
        else:
            print(f"  ❌ {config_file} missing")
            issues.append(f"{config_file} missing")
    
    # Check automation scripts
    print("\n🔧 Checking automation scripts...")
    scripts = [
        "scripts/domain_setup/provision_weaviate_clusters.py",
        "scripts/domain_setup/configure_airbyte_pipelines.py",
        "scripts/migrate_domains_with_resolution.sh"
    ]
    
    for script in scripts:
        if Path(script).exists():
            print(f"  ✅ {script}")
            
            # Check if executable
            if os.access(script, os.X_OK):
                print(f"     ✅ Executable")
            else:
                print(f"     ❌ Not executable")
                issues.append(f"{script} not executable")
        else:
            print(f"  ❌ {script} missing")
            issues.append(f"{script} missing")
    
    # Check infrastructure files
    print("\n🏗️ Checking infrastructure files...")
    infra_files = [
        "infrastructure/domain_separation.py",
        ".github/workflows/domain_infrastructure.yml",
        "shared/interfaces/domain_contracts.py"
    ]
    
    for infra_file in infra_files:
        if Path(infra_file).exists():
            print(f"  ✅ {infra_file}")
        else:
            print(f"  ❌ {infra_file} missing")
            issues.append(f"{infra_file} missing")
    
    # Summary
    print("\n" + "=" * 50)
    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ All validations passed!")
        print("\n🎉 Domain infrastructure is ready for deployment!")
        print("\nNext steps:")
        print("  1. Set environment variables:")
        print("     export WCS_API_KEY=your_weaviate_key")
        print("     export AIRBYTE_URL=your_airbyte_url")
        print("  2. Run migration: bash scripts/migrate_domains_with_resolution.sh")
        print("  3. Provision Weaviate: python3 scripts/domain_setup/provision_weaviate_clusters.py")
        print("  4. Configure Airbyte: python3 scripts/domain_setup/configure_airbyte_pipelines.py")
        print("  5. Deploy infrastructure: pulumi up -C infrastructure")
        return True

if __name__ == "__main__":
    validate_domain_setup()
