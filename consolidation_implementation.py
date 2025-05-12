#!/usr/bin/env python3
"""
Implementation utility for code consolidation.

This script facilitates the careful implementation of consolidated code frameworks
by handling the migration process step by step. It helps with:

1. Installing consolidated frameworks
2. Adding deprecation warnings to original modules
3. Creating backward compatibility layers
4. Testing the migration

Usage:
    python consolidation_implementation.py --module [error|template|service] --action [install|deprecate|test]
"""

import argparse
import importlib.util
import inspect
import logging
import os
import re
import shutil
import sys
import textwrap
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("consolidation")


class ConsolidationError(Exception):
    """Base error for consolidation operations."""
    pass


class ModuleInfo:
    """Information about a module for consolidation."""
    
    def __init__(
        self,
        name: str,
        consolidated_file: str,
        original_files: List[str],
        target_dir: str = "utils",
        imports_to_update: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize module information.
        
        Args:
            name: Module name
            consolidated_file: Path to the consolidated file
            original_files: List of original files to be deprecated
            target_dir: Target directory for the consolidated file
            imports_to_update: Dictionary of import paths to update
        """
        self.name = name
        self.consolidated_file = consolidated_file
        self.original_files = original_files
        self.target_dir = target_dir
        self.imports_to_update = imports_to_update or {}


# Define module information
MODULES = {
    "error": ModuleInfo(
        name="error_handling",
        consolidated_file="error_handling_consolidation.py",
        original_files=[
            "utils/error_handling.py",
            "gcp_migration/utils/error_handling.py",
            "wif_implementation/error_handler.py",
        ],
        imports_to_update={
            "from utils.error_handling import": "from utils.error_handling_consolidation import",
            "from gcp_migration.utils.error_handling import": "from utils.error_handling_consolidation import",
            "from wif_implementation.error_handler import": "from utils.error_handling_consolidation import",
        },
    ),
    "template": ModuleInfo(
        name="template_management",
        consolidated_file="template_management_consolidation.py",
        original_files=[
            "wif_implementation/template_manager.py",
            "wif_implementation/enhanced_template_manager.py",
        ],
        imports_to_update={
            "from wif_implementation.template_manager import": "from utils.template_management_consolidation import",
            "from wif_implementation.enhanced_template_manager import": "from utils.template_management_consolidation import",
        },
    ),
    "service": ModuleInfo(
        name="service_management",
        consolidated_file="service_management_consolidation.py",
        original_files=[
            "gcp_migration/infrastructure/service_factory.py",
            "gcp_migration/infrastructure/service_container.py",
        ],
        imports_to_update={
            "from gcp_migration.infrastructure.service_factory import": "from utils.service_management_consolidation import",
            "from gcp_migration.infrastructure.service_container import": "from utils.service_management_consolidation import",
        },
    ),
}


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def copy_file(source: Union[str, Path], target: Union[str, Path], overwrite: bool = False) -> Path:
    """
    Copy a file from source to target.
    
    Args:
        source: Source file path
        target: Target file path
        overwrite: Whether to overwrite existing files
        
    Returns:
        Path to the copied file
        
    Raises:
        ConsolidationError: If the source file doesn't exist or the target file exists and overwrite is False
    """
    source_path = Path(source)
    target_path = Path(target)
    
    if not source_path.exists():
        raise ConsolidationError(f"Source file does not exist: {source_path}")
    
    if target_path.exists() and not overwrite:
        logger.warning(f"Target file already exists, not overwriting: {target_path}")
        return target_path
    
    # Create parent directories if needed
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy the file
    shutil.copy2(source_path, target_path)
    logger.info(f"Copied {source_path} to {target_path}")
    
    return target_path


def add_deprecation_warning(file_path: Union[str, Path], replacement: str) -> bool:
    """
    Add a deprecation warning to a file.
    
    Args:
        file_path: Path to the file
        replacement: Replacement module path
        
    Returns:
        True if the file was modified, False otherwise
        
    Raises:
        ConsolidationError: If the file cannot be read or written
    """
    path = Path(file_path)
    
    if not path.exists():
        logger.warning(f"File does not exist, skipping: {path}")
        return False
    
    try:
        # Read the file content
        with open(path, "r") as f:
            content = f.read()
        
        # Check if deprecation warning already exists
        if "DeprecationWarning" in content:
            logger.info(f"Deprecation warning already exists in {path}")
            return False
        
        # Get the module name
        module_name = path.name
        
        # Create the deprecation warning
        warning = textwrap.dedent(f'''
        import warnings

        warnings.warn(
            f"The module '{module_name}' is deprecated. Use '{replacement}' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        ''')
        
        # Add the warning after imports
        match = re.search(r'^(import|from).*$', content, re.MULTILINE)
        if match:
            # Find the last import statement
            all_imports = re.finditer(r'^(import|from).*$', content, re.MULTILINE)
            last_import = list(all_imports)[-1]
            end_of_imports = last_import.end()
            
            # Add warning after imports
            new_content = content[:end_of_imports] + "\n\n" + warning + content[end_of_imports:]
        else:
            # No imports found, add warning at the beginning
            new_content = warning + "\n\n" + content
        
        # Write the modified content
        with open(path, "w") as f:
            f.write(new_content)
        
        logger.info(f"Added deprecation warning to {path}")
        return True
    
    except Exception as e:
        raise ConsolidationError(f"Error adding deprecation warning to {path}: {str(e)}")


def update_imports_in_file(file_path: Union[str, Path], import_map: Dict[str, str]) -> bool:
    """
    Update imports in a file based on the provided mapping.
    
    Args:
        file_path: Path to the file
        import_map: Map of old imports to new imports
        
    Returns:
        True if the file was modified, False otherwise
        
    Raises:
        ConsolidationError: If the file cannot be read or written
    """
    path = Path(file_path)
    
    if not path.exists() or not path.is_file():
        return False
    
    # Skip if not a Python file
    if path.suffix != ".py":
        return False
    
    try:
        # Read the file content
        with open(path, "r") as f:
            content = f.read()
        
        # Track if any changes were made
        modified = False
        
        # Replace imports
        new_content = content
        for old_import, new_import in import_map.items():
            if old_import in new_content:
                new_content = new_content.replace(old_import, new_import)
                modified = True
        
        # Write the modified content if changes were made
        if modified:
            with open(path, "w") as f:
                f.write(new_content)
            
            logger.info(f"Updated imports in {path}")
            return True
        
        return False
    
    except Exception as e:
        raise ConsolidationError(f"Error updating imports in {path}: {str(e)}")


def find_python_files(directory: Union[str, Path]) -> List[Path]:
    """
    Find all Python files in a directory recursively.
    
    Args:
        directory: Directory path
        
    Returns:
        List of Python file paths
    """
    directory_path = Path(directory)
    
    if not directory_path.exists() or not directory_path.is_dir():
        return []
    
    return list(directory_path.glob("**/*.py"))


def install_module(module_info: ModuleInfo, overwrite: bool = False) -> bool:
    """
    Install a consolidated module.
    
    Args:
        module_info: Module information
        overwrite: Whether to overwrite existing files
        
    Returns:
        True if the module was installed, False otherwise
    """
    try:
        # Ensure target directory exists
        target_dir = ensure_directory(module_info.target_dir)
        
        # Copy the consolidated file
        target_path = target_dir / Path(module_info.consolidated_file).name
        copy_file(module_info.consolidated_file, target_path, overwrite=overwrite)
        
        logger.info(f"Installed {module_info.name} module to {target_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error installing {module_info.name} module: {str(e)}")
        return False


def add_deprecation_warnings(module_info: ModuleInfo) -> int:
    """
    Add deprecation warnings to original module files.
    
    Args:
        module_info: Module information
        
    Returns:
        Number of files modified
    """
    modified_count = 0
    
    for original_file in module_info.original_files:
        try:
            # Get the replacement module path
            replacement = f"utils.{Path(module_info.consolidated_file).stem}"
            
            # Add deprecation warning
            if add_deprecation_warning(original_file, replacement):
                modified_count += 1
        
        except Exception as e:
            logger.error(f"Error adding deprecation warning to {original_file}: {str(e)}")
    
    logger.info(f"Added deprecation warnings to {modified_count} files")
    return modified_count


def update_imports(module_info: ModuleInfo, directory: Union[str, Path] = ".") -> int:
    """
    Update imports in Python files to use the consolidated module.
    
    Args:
        module_info: Module information
        directory: Directory to search for Python files
        
    Returns:
        Number of files updated
    """
    if not module_info.imports_to_update:
        logger.warning(f"No import mappings defined for {module_info.name} module")
        return 0
    
    # Find all Python files
    python_files = find_python_files(directory)
    
    # Update imports
    updated_count = 0
    for file_path in python_files:
        try:
            if update_imports_in_file(file_path, module_info.imports_to_update):
                updated_count += 1
        
        except Exception as e:
            logger.error(f"Error updating imports in {file_path}: {str(e)}")
    
    logger.info(f"Updated imports in {updated_count} files")
    return updated_count


def test_imports(module_info: ModuleInfo) -> bool:
    """
    Test if the consolidated module can be imported.
    
    Args:
        module_info: Module information
        
    Returns:
        True if the module can be imported, False otherwise
    """
    target_path = Path(module_info.target_dir) / Path(module_info.consolidated_file).name
    
    if not target_path.exists():
        logger.error(f"Consolidated module not found: {target_path}")
        return False
    
    try:
        # Add the current directory to sys.path
        if "" not in sys.path:
            sys.path.insert(0, "")
        
        # Import the module
        module_name = target_path.stem
        module_path = f"{module_info.target_dir}.{module_name}"
        
        # Create a temporary module spec
        spec = importlib.util.spec_from_file_location(module_path, target_path)
        if not spec:
            logger.error(f"Failed to create module spec for {target_path}")
            return False
        
        # Create the module
        module = importlib.util.module_from_spec(spec)
        if not module:
            logger.error(f"Failed to create module from spec for {target_path}")
            return False
        
        # Execute the module
        spec.loader.exec_module(module)
        
        logger.info(f"Successfully imported {module_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error importing {target_path}: {str(e)}")
        return False


def run_action(module_name: str, action: str, **kwargs: Any) -> bool:
    """
    Run the specified action for the module.
    
    Args:
        module_name: Module name
        action: Action to run
        **kwargs: Additional arguments
        
    Returns:
        True if the action was successful, False otherwise
        
    Raises:
        ConsolidationError: If the module or action is invalid
    """
    if module_name not in MODULES:
        raise ConsolidationError(f"Invalid module: {module_name}")
    
    module_info = MODULES[module_name]
    
    if action == "install":
        return install_module(module_info, overwrite=kwargs.get("overwrite", False))
    
    elif action == "deprecate":
        return add_deprecation_warnings(module_info) > 0
    
    elif action == "update":
        return update_imports(module_info, directory=kwargs.get("directory", ".")) > 0
    
    elif action == "test":
        return test_imports(module_info)
    
    else:
        raise ConsolidationError(f"Invalid action: {action}")


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Consolidation implementation utility")
    parser.add_argument(
        "--module",
        choices=["error", "template", "service", "all"],
        default="all",
        help="Module to process",
    )
    parser.add_argument(
        "--action",
        choices=["install", "deprecate", "update", "test", "all"],
        default="all",
        help="Action to perform",
    )
    parser.add_argument(
        "--directory",
        default=".",
        help="Directory to search for Python files",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        modules_to_process = list(MODULES.keys()) if args.module == "all" else [args.module]
        actions_to_perform = ["install", "deprecate", "update", "test"] if args.action == "all" else [args.action]
        
        success = True
        
        for module_name in modules_to_process:
            for action in actions_to_perform:
                action_success = run_action(
                    module_name,
                    action,
                    directory=args.directory,
                    overwrite=args.overwrite,
                )
                
                if not action_success:
                    logger.warning(f"Action {action} for module {module_name} failed")
                    success = False
        
        return 0 if success else 1
    
    except ConsolidationError as e:
        logger.error(f"Consolidation error: {str(e)}")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
