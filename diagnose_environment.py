#!/usr/bin/env python3
"""
DEPRECATED: This diagnostic script is deprecated and will be removed in a future release.

Please use unified_diagnostics.py instead, which provides:
- Comprehensive health checks for all Orchestra components
- Better error reporting and visualization
- Checks for GCP authentication, Terraform configuration, and Figma integration
- Memory manager validation
- GitHub Actions configuration validation

Example: python unified_diagnostics.py

Diagnostic script to verify environment setup and imports.

This script tests importing critical modules and initializing key components
to identify issues that might cause the system to fall back to recovery mode.
"""

import os
import sys
import importlib
import traceback

# Configure basic logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("diagnostics")

def print_separator(title):
    """Print a section separator with title"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def test_import(module_name):
    """Test importing a module and return success/failure"""
    print(f"Testing import: {module_name}...", end=" ")
    try:
        module = importlib.import_module(module_name)
        print("✓ SUCCESS")
        return True, module
    except Exception as e:
        print("✗ FAILED")
        print(f"  Error: {str(e)}")
        return False, None

def test_environment():
    """Test environment variables and paths"""
    print_separator("ENVIRONMENT VARIABLES")
    
    # Check critical environment variables
    critical_vars = [
        "PYTHONPATH",
        "USE_RECOVERY_MODE", 
        "STANDARD_MODE",
        "ENVIRONMENT"
    ]
    
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            print(f"{var} = {value}")
        else:
            print(f"{var} is not set")
    
    # Check Python path
    print("\nPython sys.path:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")

def test_basic_imports():
    """Test importing basic system dependencies"""
    print_separator("BASIC DEPENDENCIES")
    
    basic_modules = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "loguru"
    ]
    
    for module in basic_modules:
        test_import(module)

def test_application_imports():
    """Test importing application modules"""
    print_separator("APPLICATION MODULES")
    
    # Test both legacy and new module paths
    app_modules = [
        # Configuration modules
        "config.gcp_config",
        
        # Shared modules - try both legacy and new paths
        "shared.memory.memory_manager",
        "packages.shared.src.memory.concrete_memory_manager",
        "shared.models.base_models",
        "packages.shared.src.models.base_models",
        
        # Orchestrator modules - try both legacy and new paths
        "orchestrator.agents.agent_registry",
        "core.orchestrator.src.agents.agent_registry",
        "orchestrator.main",
        "core.orchestrator.src.main"
    ]
    
    results = {}
    for module in app_modules:
        success, mod = test_import(module)
        results[module] = (success, mod)
    
    # Group results by component
    print("\nImport results by component:")
    
    components = {
        "Config": ["config.gcp_config"],
        "Shared (Legacy)": ["shared.memory.memory_manager", "shared.models.base_models"],
        "Shared (New)": ["packages.shared.src.memory.concrete_memory_manager", "packages.shared.src.models.base_models"],
        "Orchestrator (Legacy)": ["orchestrator.agents.agent_registry", "orchestrator.main"],
        "Orchestrator (New)": ["core.orchestrator.src.agents.agent_registry", "core.orchestrator.src.main"]
    }
    
    for component, modules in components.items():
        success_count = sum(1 for m in modules if m in results and results[m][0])
        total = len(modules)
        print(f"  {component}: {success_count}/{total} modules imported successfully")
    
    return results

def test_memory_manager_creation():
    """Test creating the memory manager"""
    print_separator("MEMORY MANAGER INITIALIZATION")
    
    try:
        # Import the memory manager factory
        from shared.memory.memory_manager import MemoryManagerFactory
        
        # Try to create an in-memory manager first (should always work)
        print("Testing in-memory manager creation...", end=" ")
        memory_manager = MemoryManagerFactory.create("in-memory")
        print("✓ SUCCESS")
        
        # Import the GCP config
        from config.gcp_config import get_memory_manager_config
        
        # Try to create the configured memory manager
        print("Testing configured memory manager creation...")
        try:
            memory_config = get_memory_manager_config()
            print(f"Configuration: {memory_config}")
            memory_manager = MemoryManagerFactory.create(**memory_config)
            print(f"✓ SUCCESS - Memory manager type: {memory_config['memory_type']}")
        except Exception as e:
            print(f"✗ FAILED - Could not create configured memory manager")
            print(f"  Error: {str(e)}")
            print(f"  Traceback:")
            traceback.print_exc()
    except Exception as e:
        print(f"✗ FAILED - Basic memory manager testing failed")
        print(f"  Error: {str(e)}")
        print(f"  Traceback:")
        traceback.print_exc()

def check_directory_structure():
    """Check for expected directory structure"""
    print_separator("DIRECTORY STRUCTURE")
    
    # List of important directories and files to check
    paths = {
        # Core paths (new structure)
        "core/orchestrator/src/main.py": "Core orchestrator entry point",
        "core/orchestrator/src/agents/agent_registry.py": "Core agent registry",
        "packages/shared/src/memory/concrete_memory_manager.py": "Shared memory manager",
        "packages/shared/src/models/base_models.py": "Shared base models",
        
        # Legacy paths
        "orchestrator/main.py": "Legacy orchestrator entry point",
        "orchestrator/agents/agent_registry.py": "Legacy agent registry",
        "shared/memory/memory_manager.py": "Legacy memory manager",
        
        # Configuration
        "config/gcp_config.py": "GCP configuration",
        
        # Requirements files
        "requirements-consolidated.txt": "Consolidated requirements",
        "requirements.txt": "Main requirements",
        "requirements-dev.txt": "Development requirements",
        "core/orchestrator/requirements.txt": "Core orchestrator requirements",
        "packages/shared/requirements.txt": "Shared package requirements",
        "orchestrator/requirements.txt": "Legacy orchestrator requirements"
    }
    
    # Count existing files in new vs legacy structure
    legacy_count = 0
    new_count = 0
    
    for path, description in paths.items():
        full_path = os.path.join("/workspaces/orchestra-main", path)
        exists = os.path.exists(full_path)
        is_file = os.path.isfile(full_path) if exists else False
        
        # Track counts
        if exists:
            if "core/orchestrator" in path or "packages/shared" in path:
                new_count += 1
            elif "orchestrator/" in path or "shared/" in path:
                legacy_count += 1
        
        # Print status
        if exists:
            if is_file:
                print(f"✓ File exists: {path} - {description}")
            else:
                print(f"✓ Directory exists: {path} - {description}")
        else:
            print(f"✗ Missing: {path} - {description}")
    
    # Print structure assessment
    print("\nStructure assessment:")
    if new_count > 0 and legacy_count > 0:
        print("⚠️  Detected both legacy and new structure components.")
        print("    This suggests an incomplete migration that could cause import confusion.")
    elif new_count > 0:
        print("✓ Using new package structure (core/orchestrator and packages/shared).")
    elif legacy_count > 0:
        print("✓ Using legacy package structure (orchestrator/ and shared/).")
    else:
        print("⚠️  Critical structure components are missing.")

def main():
    """Run all diagnostic tests"""
    print_separator("SYSTEM DIAGNOSTICS")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Run tests
    test_environment()
    test_basic_imports()
    app_modules = test_application_imports()
    check_directory_structure()
    
    # Only test memory manager if basic imports worked
    if app_modules.get("shared.memory.memory_manager", (False, None))[0]:
        test_memory_manager_creation()
    else:
        print_separator("MEMORY MANAGER INITIALIZATION")
        print("Skipping memory manager tests due to import failures")
    
    # Summary
    print_separator("SUMMARY")
    if all(success for success, _ in app_modules.values()):
        print("All application modules imported successfully.")
        print("If you're still experiencing issues, the problem is likely in the initialization")
        print("code or environment variables rather than missing dependencies.")
    else:
        print("Some application modules failed to import.")
        print("You need to fix these import issues to prevent recovery mode.")
        # Count failures
        failures = sum(1 for success, _ in app_modules.values() if not success)
        print(f"Failed imports: {failures}/{len(app_modules)}")

if __name__ == "__main__":
    main()
