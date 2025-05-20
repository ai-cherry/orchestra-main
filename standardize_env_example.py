#!/usr/bin/env python3
"""
Standardize .env.example File

This script updates the .env.example file with standardized naming conventions
and organization based on the configuration standards.

Usage:
    python standardize_env_example.py

The script will:
1. Read the existing .env.example file
2. Organize sections and standardize naming
3. Write back the updated version
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Default paths
ENV_EXAMPLE_PATH = Path(".env.example")
OUTPUT_PATH = ENV_EXAMPLE_PATH


def read_env_file(path: Path) -> List[str]:
    """Read an env file and return its lines."""
    try:
        with open(path, "r") as f:
            return f.readlines()
    except FileNotFoundError:
        print(f"Error: {path} not found")
        sys.exit(1)


def write_env_file(path: Path, lines: List[str]) -> None:
    """Write lines to an env file."""
    with open(path, "w") as f:
        f.writelines(lines)
    print(f"Updated {path}")


def categorize_env_lines(lines: List[str]) -> Dict[str, List[str]]:
    """
    Categorize environment variables by section.

    Returns a dictionary mapping section names to lists of lines.
    """
    sections = {
        "header": [],
        "environment": [],
        "llm_api_keys": [],
        "tools_api_keys": [],
        "gcp": [],
        "github": [],
        "terraform": [],
        "redis": [],
        "postgres": [],
        "neo4j": [],
        "docker": [],
        "llm_config": [],
        "other": [],
    }

    # First pass - filter lines with actual content
    filtered_lines = []

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Skip lines with just "#" (empty comments)
        if line.strip() == "#":
            continue

        # Skip duplicated instructions
        if "copy this file to .env" in line.lower() and any(
            "copy this file to .env" in prev_line.lower()
            for prev_line in filtered_lines
        ):
            continue

        filtered_lines.append(line)

    # Process filtered lines
    current_section = "header"

    # Regular expressions for identifying sections and variables
    section_patterns = {
        "environment": r"# .*[Ee]nvironment|APP_ENV|ENVIRONMENT|SITE_URL|SITE_TITLE",
        "llm_api_keys": r"# .*API Keys.*Language Models|ANTHROPIC|OPENAI|OPENROUTER|MISTRAL|TOGETHER_AI|DEEPSEEK|PERPLEXITY|COHERE|HUGGINGFACE|ELEVEN_LABS|GOOGLE_API_KEY",
        "tools_api_keys": r"# .*API Keys.*Tools|PORTKEY|APIFY|APOLLO|BRAVE|EXA|EDEN|FIGMA|LANGSMITH|NOTION|PHANTOM|PINECONE|SOURCEGRAPH|TAVILY|TWINGLY|ZENROWS",
        "gcp": r"# .*GCP|GCP_|GOOGLE_APPLICATION_CREDENTIALS|GOOGLE_CLOUD_PROJECT|GCP_LOCATION|VERTEX_|GCP_SA_KEY",
        "github": r"# .*GitHub|GH_|GITHUB_",
        "terraform": r"# .*Terraform|TERRAFORM_",
        "redis": r"# .*Redis|REDIS_|CACHE_TTL",
        "postgres": r"# .*[Pp]ostgre|POSTGRES|CLOUD_SQL_|DATABASE",
        "neo4j": r"# .*Neo4j|NEO4J_",
        "docker": r"# .*Docker|DOCKER_",
        "llm_config": r"# .*LLM|DEFAULT_LLM_|LLM_REQUEST|LLM_MAX|LLM_RETRY|LLM_SEMANTIC|PREFERRED_LLM|PORTKEY_CONFIG|PORTKEY_STRATEGY|PORTKEY_VIRTUAL|MASTER_PORTKEY",
    }

    # Process each filtered line
    for line in filtered_lines:
        # Only process non-empty lines
        if line.strip():
            # Check if this line indicates a new section
            section_found = False
            for section, pattern in section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    current_section = section
                    section_found = True
                    break

            # If no specific section was matched, add to "other" only if it's a variable
            if not section_found and "=" in line and not line.strip().startswith("#"):
                current_section = "other"

            # Add the line to the current section
            sections[current_section].append(line)

    return sections


def standardize_comments_and_spacing(
    sections: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """Standardize comments and spacing in each section."""
    for section, lines in sections.items():
        # Skip empty sections
        if not lines:
            continue

        # Ensure each section has a header comment
        if section != "header" and not any(
            line.strip().startswith("#") and len(line.strip()) > 2 for line in lines[:3]
        ):
            section_title = section.replace("_", " ").title()
            sections[section] = [f"# {section_title} Configuration\n"] + lines

        # Ensure a blank line after comments at the start
        if any(line.strip().startswith("#") for line in lines):
            # Find the last comment line
            last_comment_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("#"):
                    last_comment_idx = i
                elif line.strip():  # If we hit a non-comment, non-blank line, stop
                    break

            # If the line after the last comment is not blank, add a blank line
            if (
                last_comment_idx + 1 < len(lines)
                and lines[last_comment_idx + 1].strip()
            ):
                lines.insert(last_comment_idx + 1, "\n")

    return sections


def remove_redundant_comments(sections: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Remove redundant comments that duplicate information already in other comments.
    """
    # Identify common patterns we want to eliminate duplicates of
    patterns = {
        "copy_this_file": r"copy this file to \.env",
        "env_options": r"options: development, test, staging, production",
        "authentication": r"authentication.*choose one method",
        "empty_comment": r"^#\s*$",
    }

    for section_name, lines in sections.items():
        if section_name == "header":
            continue

        # Extract actual variable assignments
        var_lines = [
            line for line in lines if "=" in line and not line.strip().startswith("#")
        ]
        var_names = set(line.split("=")[0].strip() for line in var_lines)

        # Filter comments
        filtered_lines = []
        seen_patterns = set()

        for line in lines:
            keep_line = True

            # Check if it's a comment
            if line.strip().startswith("#"):
                # Check for redundant patterns
                for pattern_name, regex in patterns.items():
                    if re.search(regex, line, re.IGNORECASE):
                        if pattern_name in seen_patterns:
                            # Skip this redundant comment
                            keep_line = False
                            break
                        seen_patterns.add(pattern_name)

            if keep_line:
                filtered_lines.append(line)

        sections[section_name] = filtered_lines

    return sections


def reassemble_env_file(sections: Dict[str, List[str]]) -> List[str]:
    """Reassemble the sections into a single list of lines."""
    result = []

    # Create a standard header
    result = [
        "# Orchestra Environment Configuration\n",
        "# Copy this file to .env and fill in your actual values\n",
        "\n",
    ]

    # Define the order of sections
    section_order = [
        "environment",
        "llm_api_keys",
        "tools_api_keys",
        "gcp",
        "github",
        "terraform",
        "redis",
        "postgres",
        "neo4j",
        "docker",
        "llm_config",
        "other",
    ]

    # Add each section with proper spacing
    for section in section_order:
        if sections[section]:
            if result and not result[-1].strip() == "":
                result.append("\n")
            result.extend(sections[section])

    return result


def main():
    """Main function."""
    print(f"Standardizing {ENV_EXAMPLE_PATH}...")

    # Read the existing file
    lines = read_env_file(ENV_EXAMPLE_PATH)

    # Process the file
    sections = categorize_env_lines(lines)
    sections = standardize_comments_and_spacing(sections)
    sections = remove_redundant_comments(sections)
    updated_lines = reassemble_env_file(sections)

    # Write the updated file
    write_env_file(OUTPUT_PATH, updated_lines)

    print("Done! The .env.example file has been standardized.")


if __name__ == "__main__":
    main()
