#!/usr/bin/env python3
"""
Code Duplication Analysis Script for Orchestra

This script analyzes the codebase to identify duplicate code patterns,
focusing on the components identified in the Technical Debt Remediation Plan.
It generates a report of duplicated code blocks to help prioritize cleanup efforts.

Usage:
  python analyze_code_duplication.py [--path PATH] [--output OUTPUT]
"""

import os
import re
import sys
import json
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict


# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print a formatted section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}==== {text} ===={Colors.END}\n")


def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.END}")


def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def check_for_tools():
    """Check if required analysis tools are available."""
    tools = {
        "pylint": "pylint --version",
        "flake8": "flake8 --version",
    }
    
    available_tools = {}
    
    for tool, command in tools.items():
        try:
            subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            available_tools[tool] = True
            print_success(f"{tool} is installed and available")
        except (subprocess.SubprocessError, FileNotFoundError):
            available_tools[tool] = False
            print_warning(f"{tool} is not installed or not available")
    
    return available_tools


def find_python_files(path):
    """Find all Python files in the given path."""
    print(f"Searching for Python files in {path}...")
    python_files = []
    
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print_success(f"Found {len(python_files)} Python files")
    return python_files


def analyze_imports(python_files):
    """Analyze import patterns to identify potential duplication."""
    print_header("Analyzing Import Patterns")
    
    # Track which files import each module
    import_map = defaultdict(list)
    
    # Common patterns for imports
    import_pattern = re.compile(r'^(?:from\s+([.\w]+)\s+)?import\s+([*\w, ]+)')
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        match = import_pattern.match(line)
                        if match:
                            module_from = match.group(1) or ""
                            imports = match.group(2).split(',')
                            
                            for imp in imports:
                                imp = imp.strip()
                                if imp and imp != '*':
                                    full_import = f"{module_from}.{imp}" if module_from else imp
                                    import_map[full_import].append((file_path, line_num))
        except Exception as e:
            print_error(f"Error analyzing {file_path}: {str(e)}")
    
    # Find commonly imported modules
    print("\nMost widely imported modules:")
    for module, occurrences in sorted(import_map.items(), key=lambda x: len(x[1]), reverse=True)[:15]:
        print(f"{Colors.CYAN}{module}{Colors.END}: Used in {len(occurrences)} locations")
    
    return import_map


def analyze_parallel_implementations(python_files):
    """Identify parallel implementations of similar functionality."""
    print_header("Analyzing Parallel Implementations")
    
    # Component families to look for
    component_families = {
        "registry": ["registry.py", "enhanced_registry.py", "unified_registry.py"],
        "event_bus": ["event_bus.py", "enhanced_event_bus.py", "unified_event_bus.py"],
        "agent_registry": ["agent_registry.py", "enhanced_agent_registry.py", "unified_agent_registry.py"]
    }
    
    found_implementations = defaultdict(list)
    
    for file_path in python_files:
        file_name = os.path.basename(file_path)
        
        for family, implementations in component_families.items():
            if file_name in implementations:
                found_implementations[family].append(file_path)
    
    # Report findings
    for family, implementations in found_implementations.items():
        print(f"\n{Colors.YELLOW}Component Family: {family}{Colors.END}")
        print(f"Found {len(implementations)} parallel implementations:")
        
        for impl in implementations:
            print(f"  - {impl}")
        
        if len(implementations) > 1:
            print_warning(f"Multiple implementations of {family} found - candidate for consolidation")
        else:
            print_success(f"Only one implementation of {family} found - already consolidated")
    
    return found_implementations


def analyze_class_hierarchies(python_files):
    """Analyze class hierarchies to identify potential for consolidation."""
    print_header("Analyzing Class Hierarchies")
    
    class_pattern = re.compile(r'class\s+(\w+)\s*(?:\(([\w, ]+)\))?:')
    classes = {}
    inheritance = defaultdict(list)
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                for match in class_pattern.finditer(content):
                    class_name = match.group(1)
                    bases = match.group(2)
                    
                    classes[class_name] = file_path
                    
                    if bases:
                        for base in bases.split(','):
                            base = base.strip()
                            if base and base != 'object':
                                inheritance[base].append(class_name)
        except Exception as e:
            print_error(f"Error analyzing {file_path}: {str(e)}")
    
    # Find classes with many subclasses (potential for better inheritance structure)
    print("\nClasses with multiple subclasses:")
    for base, derived in sorted(inheritance.items(), key=lambda x: len(x[1]), reverse=True):
        if len(derived) > 1:
            print(f"{Colors.CYAN}{base}{Colors.END} has {len(derived)} subclasses:")
            for subclass in derived[:5]:  # Show first 5 only if there are many
                print(f"  - {subclass}")
            if len(derived) > 5:
                print(f"  - ... and {len(derived) - 5} more")
    
    return inheritance


def run_pylint_duplication_check(path, available_tools):
    """Run pylint's duplicate code checker."""
    if not available_tools.get("pylint", False):
        print_warning("Pylint not available. Skipping duplicate code check.")
        return {}
    
    print_header("Running Pylint Duplicate Code Check")
    
    results = {}
    try:
        cmd = f"pylint --disable=all --enable=duplicate-code {path}"
        print(f"Running: {cmd}")
        
        output = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        # Pylint returns non-zero exit code for duplicates found, but that's expected
        if output.stdout or output.stderr:
            print(output.stdout)
            
            # Extract duplicate blocks
            dup_blocks = []
            current_block = None
            
            for line in output.stdout.splitlines():
                if "Similar lines in" in line:
                    if current_block:
                        dup_blocks.append(current_block)
                    current_block = {"files": [], "similarity": 0, "lines": []}
                    
                    # Extract similarity percentage
                    sim_match = re.search(r'(\d+)%', line)
                    if sim_match:
                        current_block["similarity"] = int(sim_match.group(1))
                    
                    # Extract file paths
                    files = re.findall(r'([^:]+):\d+', line)
                    current_block["files"].extend(files)
                
                elif current_block and line.strip() and not line.startswith("pylint"):
                    current_block["lines"].append(line)
            
            if current_block:
                dup_blocks.append(current_block)
            
            results["duplicate_blocks"] = dup_blocks
            print_success(f"Found {len(dup_blocks)} duplicate code blocks")
        else:
            print_success("No duplicate code found")
    
    except Exception as e:
        print_error(f"Error running pylint: {str(e)}")
    
    return results


def generate_report(analysis_results, output_path=None):
    """Generate a report from the analysis results."""
    print_header("Generating Report")
    
    report = {
        "timestamp": subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
        "analysis_results": analysis_results
    }
    
    # Create a readable summary
    summary = []
    summary.append("# Code Duplication Analysis Report")
    summary.append(f"\nGenerated on: {report['timestamp']}\n")
    
    # Summary of parallel implementations
    if "parallel_implementations" in analysis_results:
        summary.append("## Parallel Implementation Analysis")
        total_implementations = sum(len(impls) for impls in analysis_results["parallel_implementations"].values())
        families_with_duplicates = sum(1 for impls in analysis_results["parallel_implementations"].values() if len(impls) > 1)
        
        summary.append(f"\nFound {total_implementations} implementations across {len(analysis_results['parallel_implementations'])} component families.")
        summary.append(f"{families_with_duplicates} component families have multiple implementations that could be consolidated.\n")
        
        for family, implementations in analysis_results["parallel_implementations"].items():
            if len(implementations) > 1:
                summary.append(f"### Component Family: {family}")
                summary.append(f"Found {len(implementations)} parallel implementations:")
                for impl in implementations:
                    summary.append(f"- {impl}")
                summary.append("")
    
    # Summary of duplicate code blocks
    if "pylint_results" in analysis_results and "duplicate_blocks" in analysis_results["pylint_results"]:
        duplicate_blocks = analysis_results["pylint_results"]["duplicate_blocks"]
        
        summary.append("## Duplicate Code Blocks")
        summary.append(f"\nFound {len(duplicate_blocks)} instances of duplicated code.\n")
        
        # Group by files involved
        files_with_duplicates = set()
        for block in duplicate_blocks:
            files_with_duplicates.update(block["files"])
        
        summary.append(f"Files involved in code duplication: {len(files_with_duplicates)}\n")
        
        # Show top duplicate blocks by similarity
        if duplicate_blocks:
            summary.append("### Top Duplicate Blocks (by similarity)")
            for block in sorted(duplicate_blocks, key=lambda x: x["similarity"], reverse=True)[:5]:
                summary.append(f"\n**{block['similarity']}% similar** between:")
                for file in block["files"]:
                    summary.append(f"- {file}")
                summary.append("\n```python")
                summary.append("\n".join(block["lines"]))
                summary.append("```")
    
    # Recommendations
    summary.append("\n## Recommendations\n")
    summary.append("1. **Consolidate parallel implementations**:")
    summary.append("   - Start with the registry, event_bus, and agent_registry component families")
    summary.append("   - Follow the Technical Debt Remediation Plan, Section 7\n")
    
    summary.append("2. **Address duplicate code blocks**:")
    summary.append("   - Extract common functionality into shared utilities")
    summary.append("   - Use inheritance and composition to reduce duplication")
    summary.append("   - Consider template patterns for similar but variant code\n")
    
    summary.append("3. **Standardize dependency management**:")
    summary.append("   - Use the unified service registry consistently")
    summary.append("   - Remove global singletons in favor of dependency injection")
    summary.append("   - Add deprecation warnings to legacy component access patterns\n")
    
    # Join the summary into a single string
    summary_text = "\n".join(summary)
    
    # Write to file if output path is provided
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(summary_text)
            print_success(f"Report written to {output_path}")
        except Exception as e:
            print_error(f"Error writing report to {output_path}: {str(e)}")
    
    # Also write the machine-readable JSON report
    if output_path:
        json_path = output_path + '.json'
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print_success(f"JSON report written to {json_path}")
        except Exception as e:
            print_error(f"Error writing JSON report to {json_path}: {str(e)}")
    
    return summary_text


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze code duplication in Orchestra codebase")
    parser.add_argument('--path', default="core", help="Path to analyze (default: core)")
    parser.add_argument('--output', help="Path for output report (default: code_duplication_report.md)")
    
    args = parser.parse_args()
    path = args.path
    output = args.output or "code_duplication_report.md"
    
    print("\n" + "="*80)
    print(f"{Colors.BOLD}Orchestra Code Duplication Analysis{Colors.END}")
    print("="*80 + "\n")
    
    # Check for required tools
    available_tools = check_for_tools()
    
    if not os.path.exists(path):
        print_error(f"Path {path} does not exist")
        sys.exit(1)
    
    # Find Python files
    python_files = find_python_files(path)
    
    # Run analyses
    import_analysis = analyze_imports(python_files)
    parallel_impls = analyze_parallel_implementations(python_files)
    class_hierarchies = analyze_class_hierarchies(python_files)
    pylint_results = run_pylint_duplication_check(path, available_tools)
    
    # Combine results
    analysis_results = {
        "import_analysis": {k: len(v) for k, v in import_analysis.items()},
        "parallel_implementations": {k: v for k, v in parallel_impls.items()},
        "class_hierarchies": {k: v for k, v in class_hierarchies.items() if len(v) > 1},
        "pylint_results": pylint_results
    }
    
    # Generate report
    report = generate_report(analysis_results, output)
    
    print("\n" + "="*80)
    print(f"{Colors.BOLD}Analysis Complete{Colors.END}")
    print("="*80 + "\n")
    
    print("Next steps:")
    print("  1. Review the generated report")
    print("  2. Follow recommendations in the Technical Debt Remediation Plan")
    print("  3. Update the codebase to use unified components")
    print("  4. Follow the migration path in the plan")
    print("\n")


if __name__ == "__main__":
    main()
