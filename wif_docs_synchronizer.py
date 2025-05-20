#!/usr/bin/env python3
"""
WIF Documentation Synchronizer

This script synchronizes documentation references to Workload Identity Federation (WIF)
components across the AI Orchestra project. It ensures consistency by:

1. Scanning all documentation files for references to old WIF components
2. Updating references to point to the new implementation
3. Ensuring consistent terminology and naming across all documentation
4. Generating a report of all changes made

Usage:
    python wif_docs_synchronizer.py [options]

Options:
    --scan-only          Only scan for references without making changes
    --update             Update references to use new implementation
    --report             Generate a detailed report of all changes
    --path PATH          Path to scan (default: current directory)
    --docs-path PATH     Path to documentation directory (default: ./docs)
    --backup             Create backups of modified files
    --verbose            Show detailed output during processing
    --help               Show this help message and exit
"""

import argparse
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
logger = logging.getLogger("wif_docs_sync")


class ReferenceType(Enum):
    """Types of documentation references."""

    INLINE_LINK = "inline_link"
    REFERENCE_LINK = "reference_link"
    CODE_BLOCK = "code_block"
    COMMAND = "command"
    HEADING = "heading"
    TEXT = "text"
    OTHER = "other"


@dataclass
class DocReference:
    """Represents a reference to a WIF component in documentation."""

    file_path: str
    line_number: int
    line_content: str
    reference_type: ReferenceType
    old_reference: str
    new_reference: str
    context: List[str] = field(default_factory=list)
    updated: bool = False


@dataclass
class SyncResult:
    """Results of synchronizing documentation references."""

    references: List[DocReference] = field(default_factory=list)
    scanned_files: int = 0
    scanned_lines: int = 0
    modified_files: Set[str] = field(default_factory=set)

    def add_reference(self, reference: DocReference) -> None:
        """Add a reference to the sync results."""
        self.references.append(reference)

    def get_references_by_type(
        self, reference_type: ReferenceType
    ) -> List[DocReference]:
        """Get all references of a specific type."""
        return [ref for ref in self.references if ref.reference_type == reference_type]

    def get_references_by_file(self, file_path: str) -> List[DocReference]:
        """Get all references in a specific file."""
        return [ref for ref in self.references if ref.file_path == file_path]

    def get_updated_references(self) -> List[DocReference]:
        """Get all references that have been updated."""
        return [ref for ref in self.references if ref.updated]

    def get_pending_references(self) -> List[DocReference]:
        """Get all references that have not been updated."""
        return [ref for ref in self.references if not ref.updated]


class WIFDocsSynchronizer:
    """
    Synchronizer for WIF documentation references.

    This class provides functionality to scan documentation files for references to
    old Workload Identity Federation components and update them to use the new implementation.
    """

    # Mapping of old terms to new terms
    TERM_MAPPING = {
        "setup_github_secrets.sh": "setup_wif.sh",
        "setup_github_secrets.sh.updated": "setup_wif.sh",
        "update_wif_secrets.sh": "setup_wif.sh",
        "update_wif_secrets.sh.updated": "setup_wif.sh",
        "verify_github_secrets.sh": "verify_wif_setup.sh",
        "github_auth.sh": "setup_wif.sh",  # For authentication functionality
        "github_auth.sh.updated": "setup_wif.sh",
        "github-workflow-wif-template.yml": ".github/workflows/wif-deploy-template.yml",
        "github-workflow-wif-template.yml.updated": ".github/workflows/wif-deploy-template.yml",
        "workload_identity_federation.md": "WORKLOAD_IDENTITY_FEDERATION.md",
        "docs/workload_identity_federation.md": "docs/WORKLOAD_IDENTITY_FEDERATION.md",
    }

    # Patterns to identify references in documentation
    REFERENCE_PATTERNS = [
        # Inline links: [text](link)
        (
            r"\[(.*?)\]\(((?:\.\/)?(?:setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?)\)",
            ReferenceType.INLINE_LINK,
        ),
        (
            r"\[(.*?)\]\(((?:\.\/)?github-workflow-wif-template\.yml(?:\.updated)?)\)",
            ReferenceType.INLINE_LINK,
        ),
        (
            r"\[(.*?)\]\(((?:\.\/)?docs\/workload_identity_federation\.md)\)",
            ReferenceType.INLINE_LINK,
        ),
        # Reference links: [text][ref] or [ref]
        (
            r"\[(.*?)\]\[((?:setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?)\]",
            ReferenceType.REFERENCE_LINK,
        ),
        (
            r"\[(.*?)\]\[(github-workflow-wif-template\.yml(?:\.updated)?)\]",
            ReferenceType.REFERENCE_LINK,
        ),
        (
            r"\[(.*?)\]\[(workload_identity_federation\.md)\]",
            ReferenceType.REFERENCE_LINK,
        ),
        # Code blocks with commands
        (
            r"```(?:bash|sh).*?((?:\.\/)?(?:setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?).*?```",
            ReferenceType.CODE_BLOCK,
        ),
        (
            r"```(?:bash|sh).*?((?:\.\/)?github-workflow-wif-template\.yml(?:\.updated)?).*?```",
            ReferenceType.CODE_BLOCK,
        ),
        # Commands in text
        (
            r"`((?:\.\/)?(?:setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?)`",
            ReferenceType.COMMAND,
        ),
        (
            r"`((?:\.\/)?github-workflow-wif-template\.yml(?:\.updated)?)`",
            ReferenceType.COMMAND,
        ),
        # Headings
        (
            r"^#+\s+.*?((?:setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?).*?$",
            ReferenceType.HEADING,
        ),
        (
            r"^#+\s+.*?(github-workflow-wif-template\.yml(?:\.updated)?).*?$",
            ReferenceType.HEADING,
        ),
        (r"^#+\s+.*?(workload_identity_federation\.md).*?$", ReferenceType.HEADING),
        # Plain text references
        (
            r"(?<![`\[])((?:setup_github_secrets|update_wif_secrets|verify_github_secrets|github_auth)\.sh(?:\.updated)?)(?![`\]])",
            ReferenceType.TEXT,
        ),
        (
            r"(?<![`\[])(github-workflow-wif-template\.yml(?:\.updated)?)(?![`\]])",
            ReferenceType.TEXT,
        ),
        (r"(?<![`\[])(workload_identity_federation\.md)(?![`\]])", ReferenceType.TEXT),
    ]

    # File patterns to include in scanning
    INCLUDE_PATTERNS = [
        "*.md",
        "*.txt",
        "*.rst",
        "*.adoc",
        "*.html",
    ]

    def __init__(
        self,
        base_path: Union[str, Path] = ".",
        docs_path: Union[str, Path] = "./docs",
        backup: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize the WIF documentation synchronizer.

        Args:
            base_path: The base path to scan for documentation
            docs_path: The path to the documentation directory
            backup: Whether to create backups of modified files
            verbose: Whether to show detailed output during processing
        """
        self.base_path = Path(base_path).resolve()
        self.docs_path = Path(docs_path).resolve()
        self.backup = backup
        self.verbose = verbose
        self.sync_result = SyncResult()

        if verbose:
            logger.setLevel(logging.DEBUG)

        logger.debug(
            f"Initialized WIF documentation synchronizer with base path: {self.base_path}"
        )
        logger.debug(f"Documentation path: {self.docs_path}")

    def should_scan_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be scanned based on include patterns.

        Args:
            file_path: The path to the file

        Returns:
            True if the file should be scanned, False otherwise
        """
        # Check if file is in a hidden directory
        if any(part.startswith(".") for part in file_path.parts):
            if not (part == ".github" for part in file_path.parts):
                logger.debug(f"Skipping file in hidden directory: {file_path}")
                return False

        # Check include patterns
        for pattern in self.INCLUDE_PATTERNS:
            if file_path.match(pattern):
                return True

        logger.debug(f"Skipping file not matching include patterns: {file_path}")
        return False

    def get_context_lines(
        self, file_lines: List[str], line_number: int, context_size: int = 2
    ) -> List[str]:
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

    def map_old_to_new_term(self, old_term: str) -> str:
        """
        Map an old term to its new equivalent.

        Args:
            old_term: The old term

        Returns:
            The new term
        """
        # Check for direct mapping
        for old, new in self.TERM_MAPPING.items():
            if old in old_term:
                return old_term.replace(old, new)

        # If no direct mapping, return the original term
        return old_term

    def scan_file(self, file_path: Path) -> List[DocReference]:
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
                content = f.read()
                lines = content.splitlines()
        except UnicodeDecodeError:
            logger.debug(f"Skipping binary file: {file_path}")
            return references
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return references

        self.sync_result.scanned_files += 1
        self.sync_result.scanned_lines += len(lines)

        # Check for references in the entire content (for multi-line patterns)
        for pattern, reference_type in self.REFERENCE_PATTERNS:
            if reference_type == ReferenceType.CODE_BLOCK:
                # For code blocks, we need to search the entire content
                for match in re.finditer(pattern, content, re.DOTALL):
                    old_reference = match.group(1)
                    new_reference = self.map_old_to_new_term(old_reference)

                    if old_reference != new_reference:
                        # Find the line number for the match
                        start_pos = match.start()
                        line_number = content[:start_pos].count("\n")

                        # Get the line content
                        line_content = (
                            lines[line_number] if line_number < len(lines) else ""
                        )

                        # Get context
                        context = self.get_context_lines(lines, line_number)

                        reference = DocReference(
                            file_path=str(file_path),
                            line_number=line_number + 1,  # 1-based line number
                            line_content=line_content,
                            reference_type=reference_type,
                            old_reference=old_reference,
                            new_reference=new_reference,
                            context=context,
                        )

                        references.append(reference)
                        self.sync_result.add_reference(reference)

                        logger.debug(
                            f"Found reference in {file_path}:{line_number+1}: {old_reference} -> {new_reference}"
                        )

        # Check for references line by line
        for line_number, line in enumerate(lines):
            for pattern, reference_type in self.REFERENCE_PATTERNS:
                if (
                    reference_type != ReferenceType.CODE_BLOCK
                ):  # Skip code blocks, already handled
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        # The first group in the pattern is the actual reference
                        old_reference = match.group(1)
                        new_reference = self.map_old_to_new_term(old_reference)

                        if old_reference != new_reference:
                            context = self.get_context_lines(lines, line_number)

                            reference = DocReference(
                                file_path=str(file_path),
                                line_number=line_number + 1,  # 1-based line number
                                line_content=line.strip(),
                                reference_type=reference_type,
                                old_reference=old_reference,
                                new_reference=new_reference,
                                context=context,
                            )

                            references.append(reference)
                            self.sync_result.add_reference(reference)

                            logger.debug(
                                f"Found reference in {file_path}:{line_number+1}: {old_reference} -> {new_reference}"
                            )

        return references

    def scan_directory(self, directory_path: Optional[Path] = None) -> SyncResult:
        """
        Recursively scan a directory for references to old WIF components.

        Args:
            directory_path: The path to the directory to scan (defaults to docs_path)

        Returns:
            The sync results
        """
        if directory_path is None:
            directory_path = self.docs_path

        logger.info(f"Scanning directory: {directory_path}")

        for root, _, files in os.walk(directory_path):
            root_path = Path(root)

            for file in files:
                file_path = root_path / file

                if self.should_scan_file(file_path):
                    self.scan_file(file_path)

        logger.info(
            f"Scan complete. Found {len(self.sync_result.references)} references in {self.sync_result.scanned_files} files."
        )

        return self.sync_result

    def update_references(self) -> SyncResult:
        """
        Update references to old WIF components in documentation.

        Returns:
            The updated sync results
        """
        logger.info("Updating references...")

        # Group references by file for efficient updating
        references_by_file: Dict[str, List[DocReference]] = {}
        for reference in self.sync_result.references:
            if reference.file_path not in references_by_file:
                references_by_file[reference.file_path] = []
            references_by_file[reference.file_path].append(reference)

        # Update references in each file
        for file_path, references in references_by_file.items():
            self._update_file_references(file_path, references)

        logger.info(
            f"Updated {len(self.sync_result.get_updated_references())} references in {len(self.sync_result.modified_files)} files."
        )

        return self.sync_result

    def _update_file_references(
        self, file_path: str, references: List[DocReference]
    ) -> None:
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
            backup_path = (
                f"{file_path}.wif-docs-backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            try:
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")
            except Exception as e:
                logger.error(f"Error creating backup of {file_path}: {e}")
                return

        # Update content
        updated_content = content

        # Sort references by position in reverse order to avoid offset issues
        sorted_references = sorted(
            references, key=lambda r: r.line_number, reverse=True
        )

        # For code blocks, we need special handling
        code_block_references = [
            r for r in sorted_references if r.reference_type == ReferenceType.CODE_BLOCK
        ]
        non_code_block_references = [
            r for r in sorted_references if r.reference_type != ReferenceType.CODE_BLOCK
        ]

        # Handle code block references first
        for reference in code_block_references:
            # For code blocks, we need to be careful with the replacement
            # We'll use a regex pattern that matches the exact code block
            pattern = re.compile(
                f"```(?:bash|sh).*?{re.escape(reference.old_reference)}.*?```",
                re.DOTALL,
            )
            updated_content = pattern.sub(
                lambda m: m.group(0).replace(
                    reference.old_reference, reference.new_reference
                ),
                updated_content,
            )
            reference.updated = True
            logger.debug(
                f"Updated code block reference in {file_path}: {reference.old_reference} -> {reference.new_reference}"
            )

        # Handle other references
        for reference in non_code_block_references:
            if reference.reference_type == ReferenceType.INLINE_LINK:
                # For inline links, we need to replace the link part
                pattern = re.compile(
                    f"\\[(.*?)\\]\\({re.escape(reference.old_reference)}\\)"
                )
                updated_content = pattern.sub(
                    f"[\\1]({reference.new_reference})", updated_content
                )
                reference.updated = True
            elif reference.reference_type == ReferenceType.REFERENCE_LINK:
                # For reference links, we need to replace the reference part
                pattern = re.compile(
                    f"\\[(.*?)\\]\\[{re.escape(reference.old_reference)}\\]"
                )
                updated_content = pattern.sub(
                    f"[\\1][{reference.new_reference}]", updated_content
                )
                reference.updated = True
            elif reference.reference_type == ReferenceType.COMMAND:
                # For commands, we need to replace within backticks
                pattern = re.compile(f"`{re.escape(reference.old_reference)}`")
                updated_content = pattern.sub(
                    f"`{reference.new_reference}`", updated_content
                )
                reference.updated = True
            elif reference.reference_type == ReferenceType.HEADING:
                # For headings, we need to replace in the heading
                pattern = re.compile(
                    f"^(#+\\s+.*?){re.escape(reference.old_reference)}(.*?)$",
                    re.MULTILINE,
                )
                updated_content = pattern.sub(
                    f"\\1{reference.new_reference}\\2", updated_content
                )
                reference.updated = True
            elif reference.reference_type == ReferenceType.TEXT:
                # For plain text, we need to be careful not to replace within code blocks or links
                pattern = re.compile(
                    f"(?<![`\\[]){re.escape(reference.old_reference)}(?![`\\]])"
                )
                updated_content = pattern.sub(reference.new_reference, updated_content)
                reference.updated = True

            logger.debug(
                f"Updated {reference.reference_type.value} reference in {file_path}: {reference.old_reference} -> {reference.new_reference}"
            )

        # Write updated content back to file if changes were made
        if updated_content != content:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)

                self.sync_result.modified_files.add(file_path)
                logger.debug(f"Updated file: {file_path}")
            except Exception as e:
                logger.error(f"Error writing to file {file_path}: {e}")

    def generate_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a detailed report of the synchronization process.

        Args:
            output_path: Optional path to write the report to

        Returns:
            The report as a string
        """
        logger.info("Generating report...")

        report = {
            "timestamp": datetime.now().isoformat(),
            "base_path": str(self.base_path),
            "docs_path": str(self.docs_path),
            "statistics": {
                "scanned_files": self.sync_result.scanned_files,
                "scanned_lines": self.sync_result.scanned_lines,
                "total_references": len(self.sync_result.references),
                "updated_references": len(self.sync_result.get_updated_references()),
                "pending_references": len(self.sync_result.get_pending_references()),
                "modified_files": len(self.sync_result.modified_files),
            },
            "references_by_type": {
                ref_type.name: len(self.sync_result.get_references_by_type(ref_type))
                for ref_type in ReferenceType
            },
            "modified_files": list(self.sync_result.modified_files),
            "references": [
                {
                    "file_path": ref.file_path,
                    "line_number": ref.line_number,
                    "reference_type": ref.reference_type.name,
                    "old_reference": ref.old_reference,
                    "new_reference": ref.new_reference,
                    "updated": ref.updated,
                }
                for ref in self.sync_result.references
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
        Generate a detailed markdown report of the synchronization process.

        Args:
            output_path: Optional path to write the report to

        Returns:
            The report as a markdown string
        """
        logger.info("Generating markdown report...")

        # Get statistics
        stats = {
            "scanned_files": self.sync_result.scanned_files,
            "scanned_lines": self.sync_result.scanned_lines,
            "total_references": len(self.sync_result.references),
            "updated_references": len(self.sync_result.get_updated_references()),
            "pending_references": len(self.sync_result.get_pending_references()),
            "modified_files": len(self.sync_result.modified_files),
        }

        # Get references by type
        refs_by_type = {
            ref_type: self.sync_result.get_references_by_type(ref_type)
            for ref_type in ReferenceType
        }

        # Build the markdown report
        report = [
            "# WIF Documentation Synchronization Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"- Base Path: `{self.base_path}`",
            f"- Documentation Path: `{self.docs_path}`",
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
                    report.append(
                        f"- {status} `{ref.file_path}:{ref.line_number}`: `{ref.old_reference}` → `{ref.new_reference}`"
                    )

                report.append("")

        # Add modified files section
        if self.sync_result.modified_files:
            report.append("## Modified Files")
            report.append("")

            for file_path in sorted(self.sync_result.modified_files):
                report.append(f"- `{file_path}`")

            report.append("")

        # Add pending references section
        pending_refs = self.sync_result.get_pending_references()
        if pending_refs:
            report.append("## Pending References")
            report.append("")
            report.append(
                "The following references could not be updated automatically:"
            )
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
        description="Synchronize documentation references to WIF components."
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
        "--docs-path",
        type=str,
        default="./docs",
        help="Path to documentation directory (default: ./docs)",
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

    # Create synchronizer
    synchronizer = WIFDocsSynchronizer(
        base_path=args.path,
        docs_path=args.docs_path,
        backup=args.backup,
        verbose=args.verbose,
    )

    # Scan for references
    synchronizer.scan_directory()

    # Update references if requested
    if args.update:
        synchronizer.update_references()

    # Generate report if requested
    if args.report:
        output_path = args.output
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_path = f"wif_docs_sync_report_{timestamp}.md"

        synchronizer.generate_markdown_report(output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
