#!/usr/bin/env python3
"""
WIF Reference Scanner and Updater

This script scans the codebase for references to old Workload Identity Federation (WIF)
components and updates them to use the new implementation. It helps ensure a clean
transition to the streamlined WIF implementation by:

1. Scanning for references to old script names and paths
2. Identifying hardcoded paths and dependencies
3. Updating references to point to new components
4. Validating the changes to ensure correctness
5. Generating a comprehensive report of all changes

Usage:
    python wif_reference_scanner.py [options]

Options:
    --scan-only            Only scan for references without making changes
    --update               Update references to use new implementation
    --validate             Validate changes after updating
    --report               Generate a detailed report of all changes
    --path PATH            Path to scan (default: current directory)
    --backup               Create backups of modified files
    --verbose              Show detailed output during processing
    --help                 Show this help message and exit
"""

import argparse
import fnmatch
import json
import logging
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("wif_scanner")


class ReferenceType(Enum):
    """Types of references that can be found in the codebase."""
    SCRIPT_PATH = "script_path"
    SCRIPT_NAME = "script_name"
    FUNCTION_CALL = "function_call"
    IMPORT = "import"
    DOCUMENTATION = "documentation"
    WORKFLOW = "workflow"
    HARDCODED_PATH = "hardcoded_path"
    OTHER = "other"


@dataclass
class Reference:
    """Represents a reference to a WIF component in the codebase."""
    file_path: str
    line_number: int
    line_content: str
    reference_type: ReferenceType
    old_reference: str
    new_reference: str
    context: List[str] = field(default_factory=list)
    updated: bool = False


@dataclass
class ScanResult:
    """Results of scanning the codebase for WIF references."""
    references: List[Reference] = field(default_factory=list)
    scanned_files: int = 0
    scanned_lines: int = 0
    modified_files: Set[str] = field(default_factory=set)
    
    def add_reference(self, reference: Reference) -> None:
        """Add a reference to the scan results."""
        self.references.append(reference)
        
    def get_references_by_type(self, reference_type: ReferenceType) -> List[Reference]:
        """Get all references of a specific type."""
        return [ref for ref in self.references if ref.reference_type == reference_type]
    
    def get_references_by_file(self, file_path: str) -> List[Reference]:
        """Get all references in a specific file."""
        return [ref for ref in self.references if ref.file_path == file_path]
    
    def get_updated_references(self) -> List[Reference]:
        """Get all references that have been updated."""
        return [ref for ref in self.references if ref.updated]
    
    def get_pending_references(self) -> List[Reference]:
        """Get all references that have not been updated."""
        return [ref for ref in self.references if not ref.updated]


class WIFReferenceScanner:
    """
    Scanner for finding and updating references to old WIF components.
    
    This class provides functionality to scan the codebase for references to old
    Workload Identity Federation components and update them to use the new implementation.
    """
    
    # Mapping of old script names to new script names
    SCRIPT_MAPPING = {
        "setup_github_secrets.sh": "setup_wif.sh",
        "setup_github_secrets.sh.updated": "setup_wif.sh",
        "update_wif_secrets.sh": "setup_wif.sh",
        "update_wif_secrets.sh.updated": "setup_wif.sh",
        "verify_github_secrets.sh": "verify_wif_setup.sh",
        "github_auth.sh": "setup_wif.sh",  # For authentication functionality
        "github_auth.sh.updated": "setup_wif.sh",
        "github-workflow-wif-template.yml": ".github/workflows/wif-deploy-template.yml",
        "github-workflow-wif-template.yml.updated": ".github/workflows/wif-deploy-template.yml",
        "docs/workload_identity_federation.md": "docs/WORKLOAD_IDENTITY_FEDERATION.md",
    }
    
    # Patterns to identify references to old WIF components
    REFERENCE_PATTERNS = [
        # Script paths and names
        (r'(["\'`])((?:\.\/)?(?:setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?)\1', ReferenceType.SCRIPT_PATH),
        (r'(["\'`])((?:\.\/)?github-workflow-wif-template\.yml(?:\.updated)?)\1', ReferenceType.SCRIPT_PATH),
        (r'(["\'`])((?:\.\/)?docs\/workload_identity_federation\.md)\1', ReferenceType.SCRIPT_PATH),
        
        # Function calls
        (r'source\s+((?:\.\/)?(?:setup_github_secrets|update_wif_secrets|github_auth)\.sh(?:\.updated)?)', ReferenceType.FUNCTION_CALL),
        (r'\.\/?(setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?', ReferenceType.FUNCTION_CALL),
        
        # Documentation references
        (r'\[(.*?)\]\(((?:\.\/)?(?:setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?)\)', ReferenceType.DOCUMENTATION),
        (r'\[(.*?)\]\(((?:\.\/)?github-workflow-wif-template\.yml(?:\.updated)?)\)', ReferenceType.DOCUMENTATION),
        (r'\[(.*?)\]\(((?:\.\/)?docs\/workload_identity_federation\.md)\)', ReferenceType.DOCUMENTATION),
        
        # Workflow references
        (r'(file:\s*)((?:\.\/)?github-workflow-wif-template\.yml(?:\.updated)?)', ReferenceType.WORKFLOW),
        
        # Hardcoded paths
        (r'(["\'`])(\/(?:home|workspaces)\/[^\/]+\/(?:setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?)\1', ReferenceType.HARDCODED_PATH),
    ]
    
    # File patterns to exclude from scanning
    EXCLUDE_PATTERNS = [
        "*.pyc",
        "*.pyo",
        "*.so",
        "*.o",
        "*.a",
        "*.dylib",
        "*.dll",
        "*.exe",
        "*.bin",
        "*.jar",
        "*.war",
        "*.ear",
        "*.zip",
        "*.tar",
        "*.gz",
        "*.bz2",
        "*.xz",
        "*.rar",
        "*.7z",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "*.log",
        "*.tmp",
        "*.temp",
        "*.swp",
        "*.swo",
        "*.swn",
        "*.bak",
        "*.orig",
        "*.DS_Store",
        "*.class",
        "*.pdb",
        "*.min.js",
        "*.min.css",
        "node_modules/**",
        ".git/**",
        ".github/**",
        ".venv/**",
        "venv/**",
        "env/**",
        "__pycache__/**",
        "dist/**",
        "build/**",
        "*.egg-info/**",
    ]
    
    # File patterns to include in scanning
    INCLUDE_PATTERNS = [
        "*.py",
        "*.sh",
        "*.bash",
        "*.yml",
        "*.yaml",
        "*.json",
        "*.md",
        "*.txt",
        "*.tf",
        "*.hcl",
        "*.toml",
        "*.ini",
        "*.cfg",
        "*.conf",
        "Dockerfile*",
    ]
    
    def __init__(
        self,
        base_path: Union[str, Path] = ".",
        backup: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize the WIF reference scanner.
        
        Args:
            base_path: The base path to scan for references
            backup: Whether to create backups of modified files
            verbose: Whether to show detailed output during processing
        """
        self.base_path = Path(base_path).resolve()
        self.backup = backup
        self.verbose = verbose
        self.scan_result = ScanResult()
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.debug(f"Initialized WIF reference scanner with base path: {self.base_path}")
    
    def should_scan_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be scanned based on include/exclude patterns.
        
        Args:
            file_path: The path to the file
            
        Returns:
            True if the file should be scanned, False otherwise
        """
        # Check exclude patterns first
        for pattern in self.EXCLUDE_PATTERNS:
            if fnmatch.fnmatch(str(file_path), pattern):
                logger.debug(f"Skipping excluded file: {file_path}")
                return False
        
        # Then check include patterns
        for pattern in self.INCLUDE_PATTERNS:
            if fnmatch.fnmatch(str(file_path), pattern):
                return True
        
        logger.debug(f"Skipping file not matching include patterns: {file_path}")
        return False
    
    def get_context_lines(self, file_lines: List[str], line_number: int, context_size: int = 2) -> List[str]:
        """
        Get context lines around a specific line in a file.
        
        Args:
            file_lines: The lines of the file
            line_number: The line number to get context for (0-based)
            context_size: The number of lines of context to include before and after
            
        Returns:
            A list of context lines
        """
        start = max(0, line_number - context_size)
        end = min(len(file_lines), line_number + context_size + 1)
        
        context = []
        for i in range(start, end):
            if i == line_number:
                context.append(f">>> {file_lines[i]}")
            else:
                context.append(f"    {file_lines[i]}")
        
        return context
    
    def map_old_to_new_reference(self, old_reference: str) -> str:
        """
        Map an old reference to its new equivalent.
        
        Args:
            old_reference: The old reference
            
        Returns:
            The new reference
        """
        # Check for direct mapping
        for old, new in self.SCRIPT_MAPPING.items():
            if old in old_reference:
                return old_reference.replace(old, new)
        
        # If no direct mapping, return the original reference
        return old_reference
    
    def scan_file(self, file_path: Path) -> List[Reference]:
        """
        Scan a single file for references to old WIF components.
        
        Args:
            file_path: The path to the file to scan
            
        Returns:
            A list of references found in the file
        """
        logger.debug(f"Scanning file: {file_path}")
        
        references = []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            logger.debug(f"Skipping binary file: {file_path}")
            return references
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return references
        
        self.scan_result.scanned_files += 1
        self.scan_result.scanned_lines += len(lines)
        
        for line_number, line in enumerate(lines):
            for pattern, reference_type in self.REFERENCE_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    # Get the reference from the appropriate group
                    # Most patterns have the reference in group 2, but some might have it in group 1
                    try:
                        old_reference = match.group(2)
                    except IndexError:
                        # If group 2 doesn't exist, try group 1
                        try:
                            old_reference = match.group(1)
                        except IndexError:
                            # If neither group exists, skip this match
                            logger.warning(f"No capture group found in match: {match.group(0)}")
                            continue
                    
                    new_reference = self.map_old_to_new_reference(old_reference)
                    
                    if old_reference != new_reference:
                        context = self.get_context_lines(lines, line_number)
                        
                        reference = Reference(
                            file_path=str(file_path),
                            line_number=line_number + 1,  # 1-based line number
                            line_content=line.strip(),
                            reference_type=reference_type,
                            old_reference=old_reference,
                            new_reference=new_reference,
                            context=context,
                        )
                        
                        references.append(reference)
                        self.scan_result.add_reference(reference)
                        
                        logger.debug(f"Found reference in {file_path}:{line_number+1}: {old_reference} -> {new_reference}")
        
        return references
    
    def scan_directory(self, directory_path: Optional[Path] = None) -> ScanResult:
        """
        Recursively scan a directory for references to old WIF components.
        
        Args:
            directory_path: The path to the directory to scan (defaults to base_path)
            
        Returns:
            The scan results
        """
        if directory_path is None:
            directory_path = self.base_path
        
        logger.info(f"Scanning directory: {directory_path}")
        
        for root, _, files in os.walk(directory_path):
            root_path = Path(root)
            
            for file in files:
                file_path = root_path / file
                
                if self.should_scan_file(file_path):
                    self.scan_file(file_path)
        
        logger.info(f"Scan complete. Found {len(self.scan_result.references)} references in {self.scan_result.scanned_files} files.")
        
        return self.scan_result
    
    def update_references(self) -> ScanResult:
        """
        Update references to old WIF components in the codebase.
        
        Returns:
            The updated scan results
        """
        logger.info("Updating references...")
        
        # Group references by file for efficient updating
        references_by_file: Dict[str, List[Reference]] = {}
        for reference in self.scan_result.references:
            if reference.file_path not in references_by_file:
                references_by_file[reference.file_path] = []
            references_by_file[reference.file_path].append(reference)
        
        # Update references in each file
        for file_path, references in references_by_file.items():
            self._update_file_references(file_path, references)
        
        logger.info(f"Updated {len(self.scan_result.get_updated_references())} references in {len(self.scan_result.modified_files)} files.")
        
        return self.scan_result
    
    def _update_file_references(self, file_path: str, references: List[Reference]) -> None:
        """
        Update references in a single file.
        
        Args:
            file_path: The path to the file
            references: The references to update in the file
        """
        logger.debug(f"Updating references in file: {file_path}")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return
        
        # Create backup if enabled
        if self.backup:
            backup_path = f"{file_path}.wif-backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            try:
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")
            except Exception as e:
                logger.error(f"Error creating backup of {file_path}: {e}")
                return
        
        # Sort references by line number in reverse order to avoid offset issues
        sorted_references = sorted(references, key=lambda r: r.line_number, reverse=True)
        
        # Update content
        lines = content.splitlines()
        for reference in sorted_references:
            line_index = reference.line_number - 1  # Convert to 0-based index
            
            if line_index >= len(lines):
                logger.warning(f"Line number {reference.line_number} out of range in {file_path}")
                continue
            
            old_line = lines[line_index]
            
            # Replace the old reference with the new one
            # We need to be careful to replace only the exact reference, not partial matches
            new_line = old_line.replace(reference.old_reference, reference.new_reference)
            
            if new_line != old_line:
                lines[line_index] = new_line
                reference.updated = True
                logger.debug(f"Updated reference in {file_path}:{reference.line_number}")
        
        # Write updated content back to file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            
            self.scan_result.modified_files.add(file_path)
            logger.debug(f"Updated file: {file_path}")
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {e}")
    
    def validate_updates(self) -> Tuple[bool, List[Reference]]:
        """
        Validate that all references have been updated correctly.
        
        Returns:
            A tuple containing:
            - Whether all references were updated successfully
            - A list of references that failed to update
        """
        logger.info("Validating updates...")
        
        failed_references = []
        
        for reference in self.scan_result.references:
            if not reference.updated:
                failed_references.append(reference)
                logger.warning(f"Reference not updated: {reference.file_path}:{reference.line_number} - {reference.old_reference}")
        
        success = len(failed_references) == 0
        
        if success:
            logger.info("All references updated successfully.")
        else:
            logger.warning(f"Failed to update {len(failed_references)} references.")
        
        return success, failed_references
    
    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a detailed report of the scan and update process.
        
        Args:
            output_path: Optional path to write the report to
            
        Returns:
            The report as a string
        """
        logger.info("Generating report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_path": str(self.base_path),
            "statistics": {
                "scanned_files": self.scan_result.scanned_files,
                "scanned_lines": self.scan_result.scanned_lines,
                "total_references": len(self.scan_result.references),
                "updated_references": len(self.scan_result.get_updated_references()),
                "pending_references": len(self.scan_result.get_pending_references()),
                "modified_files": len(self.scan_result.modified_files),
            },
            "references_by_type": {
                ref_type.name: len(self.scan_result.get_references_by_type(ref_type))
                for ref_type in ReferenceType
            },
            "modified_files": list(self.scan_result.modified_files),
            "references": [
                {
                    "file_path": ref.file_path,
                    "line_number": ref.line_number,
                    "reference_type": ref.reference_type.name,
                    "old_reference": ref.old_reference,
                    "new_reference": ref.new_reference,
                    "updated": ref.updated,
                }
                for ref in self.scan_result.references
            ],
        }
        
        report_json = json.dumps(report, indent=2)
        
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(report_json)
                logger.info(f"Report written to: {output_path}")
            except Exception as e:
                logger.error(f"Error writing report to {output_path}: {e}")
        
        return report_json
    
    def generate_markdown_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a detailed markdown report of the scan and update process.
        
        Args:
            output_path: Optional path to write the report to
            
        Returns:
            The report as a markdown string
        """
        logger.info("Generating markdown report...")
        
        # Get statistics
        stats = {
            "scanned_files": self.scan_result.scanned_files,
            "scanned_lines": self.scan_result.scanned_lines,
            "total_references": len(self.scan_result.references),
            "updated_references": len(self.scan_result.get_updated_references()),
            "pending_references": len(self.scan_result.get_pending_references()),
            "modified_files": len(self.scan_result.modified_files),
        }
        
        # Get references by type
        refs_by_type = {
            ref_type: self.scan_result.get_references_by_type(ref_type)
            for ref_type in ReferenceType
        }
        
        # Build the markdown report
        report = [
            "# WIF Reference Scanner Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- Base Path: `{self.base_path}`",
            f"- Scanned Files: {stats['scanned_files']}",
            f"- Scanned Lines: {stats['scanned_lines']}",
            f"- Total References Found: {stats['total_references']}",
            f"- References Updated: {stats['updated_references']}",
            f"- References Pending: {stats['pending_references']}",
            f"- Files Modified: {stats['modified_files']}",
            "",
            "## References by Type",
            "",
        ]
        
        # Add references by type
        for ref_type, references in refs_by_type.items():
            if references:
                report.append(f"### {ref_type.name} ({len(references)})")
                report.append("")
                
                for ref in references:
                    status = "✅" if ref.updated else "❌"
                    report.append(f"- {status} `{ref.file_path}:{ref.line_number}`: `{ref.old_reference}` → `{ref.new_reference}`")
                
                report.append("")
        
        # Add modified files section
        if self.scan_result.modified_files:
            report.append("## Modified Files")
            report.append("")
            
            for file_path in sorted(self.scan_result.modified_files):
                report.append(f"- `{file_path}`")
            
            report.append("")
        
        # Add pending references section
        pending_refs = self.scan_result.get_pending_references()
        if pending_refs:
            report.append("## Pending References")
            report.append("")
            report.append("The following references could not be updated automatically:")
            report.append("")
            
            for ref in pending_refs:
                report.append(f"### {ref.file_path}:{ref.line_number}")
                report.append("")
                report.append("```")
                for ctx_line in ref.context:
                    report.append(ctx_line)
                report.append("```")
                report.append("")
                report.append(f"- Old Reference: `{ref.old_reference}`")
                report.append(f"- New Reference: `{ref.new_reference}`")
                report.append(f"- Type: {ref.reference_type.name}")
                report.append("")
        
        # Join the report lines
        report_md = "\n".join(report)
        
        # Write to file if output path is provided
        if output_path:
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(report_md)
                logger.info(f"Markdown report written to: {output_path}")
            except Exception as e:
                logger.error(f"Error writing markdown report to {output_path}: {e}")
        
        return report_md


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan and update references to old WIF components in the codebase."
    )
    
    parser.add_argument(
        "--scan-only",
        action="store_true",
        help="Only scan for references without making changes",
    )
    
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update references to use new implementation",
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate changes after updating",
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a detailed report of all changes",
    )
    
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to scan (default: current directory)",
    )
    
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backups of modified files",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output during processing",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Path to write the report to",
    )
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for the script."""
    args = parse_args()
    
    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create scanner
    scanner = WIFReferenceScanner(
        base_path=args.path,
        backup=args.backup,
        verbose=args.verbose,
    )
    
    # Scan for references
    scanner.scan_directory()
    
    # Update references if requested
    if args.update:
        scanner.update_references()
    
    # Validate changes if requested
    if args.validate:
        success, failed_references = scanner.validate_updates()
        if not success:
            logger.warning(f"Validation failed: {len(failed_references)} references not updated.")
    
    # Generate report if requested
    if args.report:
        output_path = args.output
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = f"wif_reference_report_{timestamp}.md"
        
        scanner.generate_markdown_report(output_path)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())