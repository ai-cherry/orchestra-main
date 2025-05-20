#!/usr/bin/env python3
"""
Analyze Agent Registry Implementations

This script analyzes the different agent registry implementations in the codebase
and suggests a unified approach. It compares:

1. agent_registry.py - Original implementation with circuit breaker pattern
2. enhanced_agent_registry.py - Newer implementation with more features

Usage:
    python analyze_agent_registries.py [--output OUTPUT]

Options:
    --output OUTPUT    Output file for the unified registry design (default: unified_registry_design.md)
"""

import argparse
import ast
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    methods: List[str]
    attributes: List[str]
    base_classes: List[str]
    docstring: Optional[str] = None


@dataclass
class FunctionInfo:
    """Information about a function."""

    name: str
    parameters: List[str]
    return_type: Optional[str] = None
    docstring: Optional[str] = None


@dataclass
class ModuleInfo:
    """Information about a module."""

    name: str
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    imports: List[str]
    docstring: Optional[str] = None


class ClassVisitor(ast.NodeVisitor):
    """AST visitor to extract class information."""

    def __init__(self):
        self.classes = []

    def visit_ClassDef(self, node):
        """Visit a class definition."""
        # Extract base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(f"{base.value.id}.{base.attr}")

        # Extract methods and attributes
        methods = []
        attributes = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Create class info
        class_info = ClassInfo(
            name=node.name,
            methods=methods,
            attributes=attributes,
            base_classes=base_classes,
            docstring=docstring,
        )

        self.classes.append(class_info)

        # Continue visiting child nodes
        self.generic_visit(node)


class FunctionVisitor(ast.NodeVisitor):
    """AST visitor to extract function information."""

    def __init__(self):
        self.functions = []

    def visit_FunctionDef(self, node):
        """Visit a function definition."""
        # Skip methods (they are handled by ClassVisitor)
        if isinstance(node.parent, ast.ClassDef):
            return

        # Extract parameters
        parameters = []
        for arg in node.args.args:
            parameters.append(arg.arg)

        # Extract return type
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Attribute):
                return_type = f"{node.returns.value.id}.{node.returns.attr}"

        # Extract docstring
        docstring = ast.get_docstring(node)

        # Create function info
        function_info = FunctionInfo(
            name=node.name,
            parameters=parameters,
            return_type=return_type,
            docstring=docstring,
        )

        self.functions.append(function_info)


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to extract import information."""

    def __init__(self):
        self.imports = []

    def visit_Import(self, node):
        """Visit an import statement."""
        for name in node.names:
            self.imports.append(name.name)

    def visit_ImportFrom(self, node):
        """Visit an import from statement."""
        if node.module:
            for name in node.names:
                self.imports.append(f"{node.module}.{name.name}")


def parse_module(file_path: Path) -> ModuleInfo:
    """
    Parse a module and extract information.

    Args:
        file_path: Path to the module file

    Returns:
        Module information
    """
    with open(file_path, "r") as f:
        source = f.read()

    # Parse the source code
    tree = ast.parse(source)

    # Add parent references to nodes
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

    # Extract classes
    class_visitor = ClassVisitor()
    class_visitor.visit(tree)

    # Extract functions
    function_visitor = FunctionVisitor()
    function_visitor.visit(tree)

    # Extract imports
    import_visitor = ImportVisitor()
    import_visitor.visit(tree)

    # Extract module docstring
    docstring = ast.get_docstring(tree)

    # Create module info
    module_info = ModuleInfo(
        name=file_path.stem,
        classes=class_visitor.classes,
        functions=function_visitor.functions,
        imports=import_visitor.imports,
        docstring=docstring,
    )

    return module_info


def compare_registries(registry1: ModuleInfo, registry2: ModuleInfo) -> Dict[str, Any]:
    """
    Compare two registry implementations.

    Args:
        registry1: First registry module
        registry2: Second registry module

    Returns:
        Comparison results
    """
    results = {
        "common_classes": [],
        "unique_classes_1": [],
        "unique_classes_2": [],
        "common_functions": [],
        "unique_functions_1": [],
        "unique_functions_2": [],
        "common_imports": [],
        "unique_imports_1": [],
        "unique_imports_2": [],
    }

    # Compare classes
    class_names_1 = {cls.name for cls in registry1.classes}
    class_names_2 = {cls.name for cls in registry2.classes}

    common_class_names = class_names_1.intersection(class_names_2)
    unique_class_names_1 = class_names_1 - class_names_2
    unique_class_names_2 = class_names_2 - class_names_1

    results["common_classes"] = [
        cls for cls in registry1.classes if cls.name in common_class_names
    ]
    results["unique_classes_1"] = [
        cls for cls in registry1.classes if cls.name in unique_class_names_1
    ]
    results["unique_classes_2"] = [
        cls for cls in registry2.classes if cls.name in unique_class_names_2
    ]

    # Compare functions
    function_names_1 = {func.name for func in registry1.functions}
    function_names_2 = {func.name for func in registry2.functions}

    common_function_names = function_names_1.intersection(function_names_2)
    unique_function_names_1 = function_names_1 - function_names_2
    unique_function_names_2 = function_names_2 - function_names_1

    results["common_functions"] = [
        func for func in registry1.functions if func.name in common_function_names
    ]
    results["unique_functions_1"] = [
        func for func in registry1.functions if func.name in unique_function_names_1
    ]
    results["unique_functions_2"] = [
        func for func in registry2.functions if func.name in unique_function_names_2
    ]

    # Compare imports
    imports_1 = set(registry1.imports)
    imports_2 = set(registry2.imports)

    results["common_imports"] = list(imports_1.intersection(imports_2))
    results["unique_imports_1"] = list(imports_1 - imports_2)
    results["unique_imports_2"] = list(imports_2 - imports_1)

    return results


def generate_unified_design(comparison_results: Dict[str, Any]) -> str:
    """
    Generate a unified design based on comparison results.

    Args:
        comparison_results: Comparison results

    Returns:
        Unified design as markdown
    """
    markdown = "# Unified Agent Registry Design\n\n"

    # Introduction
    markdown += "## Introduction\n\n"
    markdown += "This document proposes a unified agent registry design that combines the best features of both implementations:\n\n"
    markdown += "1. `agent_registry.py` - Original implementation with circuit breaker pattern\n"
    markdown += (
        "2. `enhanced_agent_registry.py` - Newer implementation with more features\n\n"
    )

    # Classes
    markdown += "## Classes\n\n"

    # Common classes
    if comparison_results["common_classes"]:
        markdown += "### Common Classes\n\n"
        for cls in comparison_results["common_classes"]:
            markdown += f"#### {cls.name}\n\n"
            if cls.docstring:
                markdown += f"{cls.docstring}\n\n"
            if cls.base_classes:
                markdown += f"Base classes: {', '.join(cls.base_classes)}\n\n"
            markdown += "Methods:\n"
            for method in cls.methods:
                markdown += f"- `{method}`\n"
            markdown += "\n"

    # Unique classes from first implementation
    if comparison_results["unique_classes_1"]:
        markdown += "### Unique Classes from agent_registry.py\n\n"
        for cls in comparison_results["unique_classes_1"]:
            markdown += f"#### {cls.name}\n\n"
            if cls.docstring:
                markdown += f"{cls.docstring}\n\n"
            if cls.base_classes:
                markdown += f"Base classes: {', '.join(cls.base_classes)}\n\n"
            markdown += "Methods:\n"
            for method in cls.methods:
                markdown += f"- `{method}`\n"
            markdown += "\n"

    # Unique classes from second implementation
    if comparison_results["unique_classes_2"]:
        markdown += "### Unique Classes from enhanced_agent_registry.py\n\n"
        for cls in comparison_results["unique_classes_2"]:
            markdown += f"#### {cls.name}\n\n"
            if cls.docstring:
                markdown += f"{cls.docstring}\n\n"
            if cls.base_classes:
                markdown += f"Base classes: {', '.join(cls.base_classes)}\n\n"
            markdown += "Methods:\n"
            for method in cls.methods:
                markdown += f"- `{method}`\n"
            markdown += "\n"

    # Functions
    markdown += "## Functions\n\n"

    # Common functions
    if comparison_results["common_functions"]:
        markdown += "### Common Functions\n\n"
        for func in comparison_results["common_functions"]:
            markdown += f"#### {func.name}\n\n"
            if func.docstring:
                markdown += f"{func.docstring}\n\n"
            markdown += f"Parameters: {', '.join(func.parameters)}\n\n"
            if func.return_type:
                markdown += f"Return type: {func.return_type}\n\n"

    # Unique functions from first implementation
    if comparison_results["unique_functions_1"]:
        markdown += "### Unique Functions from agent_registry.py\n\n"
        for func in comparison_results["unique_functions_1"]:
            markdown += f"#### {func.name}\n\n"
            if func.docstring:
                markdown += f"{func.docstring}\n\n"
            markdown += f"Parameters: {', '.join(func.parameters)}\n\n"
            if func.return_type:
                markdown += f"Return type: {func.return_type}\n\n"

    # Unique functions from second implementation
    if comparison_results["unique_functions_2"]:
        markdown += "### Unique Functions from enhanced_agent_registry.py\n\n"
        for func in comparison_results["unique_functions_2"]:
            markdown += f"#### {func.name}\n\n"
            if func.docstring:
                markdown += f"{func.docstring}\n\n"
            markdown += f"Parameters: {', '.join(func.parameters)}\n\n"
            if func.return_type:
                markdown += f"Return type: {func.return_type}\n\n"

    # Unified Design
    markdown += "## Unified Design\n\n"
    markdown += "### Proposed Class Hierarchy\n\n"
    markdown += "```python\n"
    markdown += "class UnifiedAgentRegistry(Service):\n"
    markdown += '    """Unified agent registry that combines the best features of both implementations."""\n'
    markdown += "    \n"
    markdown += "    def __init__(self):\n"
    markdown += "        self._agents = {}  # Agent instances\n"
    markdown += "        self._agent_types = {}  # Agent classes\n"
    markdown += "        self._capabilities = {}  # Capability-based lookup\n"
    markdown += "        self._default_agent_type = None\n"
    markdown += "        self._circuit_breaker = get_circuit_breaker()\n"
    markdown += "        self._event_bus = get_enhanced_event_bus()\n"
    markdown += "    \n"
    markdown += "    # Registration methods\n"
    markdown += "    def register_agent(self, agent: Agent) -> None: ...\n"
    markdown += "    def register_agent_type(self, agent_type: str, agent_class: Type[Agent]) -> None: ...\n"
    markdown += "    def register_agent_with_capabilities(self, agent_class: Type[Agent], agent_type: str, capabilities: List[AgentCapability], priority: int = 0) -> None: ...\n"
    markdown += "    \n"
    markdown += "    # Agent retrieval methods\n"
    markdown += (
        "    def get_agent(self, agent_type: Optional[str] = None) -> Agent: ...\n"
    )
    markdown += (
        "    def select_agent_for_context(self, context: AgentContext) -> Agent: ...\n"
    )
    markdown += "    \n"
    markdown += "    # Lifecycle methods\n"
    markdown += "    def initialize(self) -> None: ...\n"
    markdown += "    async def initialize_async(self) -> None: ...\n"
    markdown += "    def close(self) -> None: ...\n"
    markdown += "    async def close_async(self) -> None: ...\n"
    markdown += "```\n\n"

    # Key Features
    markdown += "### Key Features to Preserve\n\n"
    markdown += "1. **Circuit Breaker Pattern** from `agent_registry.py`\n"
    markdown += "   - Provides resilience and fault tolerance\n"
    markdown += "   - Handles failures gracefully with fallbacks\n\n"
    markdown += "2. **Capability-Based Selection** from `enhanced_agent_registry.py`\n"
    markdown += "   - More sophisticated agent selection based on capabilities\n"
    markdown += "   - Better matching of agents to specific tasks\n\n"
    markdown += "3. **Event-Based Communication** from `enhanced_agent_registry.py`\n"
    markdown += "   - Allows for loose coupling between components\n"
    markdown += "   - Enables extensibility through event subscribers\n\n"
    markdown += "4. **Lifecycle Management** from both implementations\n"
    markdown += "   - Proper initialization and cleanup of resources\n"
    markdown += "   - Support for both synchronous and asynchronous operations\n\n"

    # Migration Strategy
    markdown += "## Migration Strategy\n\n"
    markdown += "1. Create the unified registry implementation\n"
    markdown += "2. Create adapters for backward compatibility\n"
    markdown += "3. Update agent implementations to use the unified registry\n"
    markdown += "4. Gradually migrate existing code to the new approach\n"
    markdown += "5. Remove the old implementations once migration is complete\n\n"

    return markdown


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Analyze agent registry implementations"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="unified_registry_design.md",
        help="Output file for the unified registry design",
    )
    args = parser.parse_args()

    # Parse the registry modules
    registry1_path = Path("core/orchestrator/src/agents/agent_registry.py")
    registry2_path = Path("core/orchestrator/src/agents/enhanced_agent_registry.py")

    if not registry1_path.exists():
        print(f"Error: File {registry1_path} does not exist")
        sys.exit(1)

    if not registry2_path.exists():
        print(f"Error: File {registry2_path} does not exist")
        sys.exit(1)

    print(f"Parsing {registry1_path}...")
    registry1_info = parse_module(registry1_path)

    print(f"Parsing {registry2_path}...")
    registry2_info = parse_module(registry2_path)

    # Compare the registries
    print("Comparing registries...")
    comparison_results = compare_registries(registry1_info, registry2_info)

    # Generate unified design
    print("Generating unified design...")
    unified_design = generate_unified_design(comparison_results)

    # Write to output file
    output_path = Path(args.output)
    with open(output_path, "w") as f:
        f.write(unified_design)

    print(f"Unified design written to {output_path}")


if __name__ == "__main__":
    main()
