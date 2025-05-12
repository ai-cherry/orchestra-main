#!/usr/bin/env python3
"""
Gemini code analysis wrapper for pre-commit hooks.

This script sends staged Python files to Google's Gemini API for code analysis,
providing immediate feedback before commit.
"""

import argparse
import json
import os
import subprocess
import sys
from typing import List, Dict, Any, Optional

# Import Google Cloud libraries with proper error handling
try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel
except ImportError:
    print("Error: Required Google Cloud libraries not found.")
    print("Install with: pip install google-cloud-aiplatform")
    sys.exit(1)

def get_staged_files(extensions: List[str]) -> List[str]:
    """Get list of staged files with specified extensions."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True,
        text=True,
        check=True
    )
    
    all_files = result.stdout.strip().split("\n")
    return [f for f in all_files if any(f.endswith(ext) for ext in extensions)]

def read_file_content(file_path: str) -> Optional[str]:
    """Read and return file content safely."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None

def analyze_code_with_gemini(
    files_content: Dict[str, str],
    project_id: str = "cherry-ai-project",
    location: str = "us-central1"
) -> Dict[str, Any]:
    """
    Analyze code using Gemini API.
    
    Args:
        files_content: Dictionary mapping file paths to content
        project_id: GCP project ID
        location: GCP region
        
    Returns:
        Analysis results
    """
    # Initialize Vertex AI
    aiplatform.init(project=project_id, location=location)
    
    # Create the model
    model = GenerativeModel("gemini-1.5-pro")
    
    # Prepare prompt with code from all files
    prompt = "Analyze the following Python code files for issues, security vulnerabilities, and best practices:\n\n"
    
    for file_path, content in files_content.items():
        prompt += f"File: {file_path}\n```python\n{content}\n```\n\n"
    
    prompt += "Provide a concise analysis focusing on code quality, security issues, and performance concerns."
    
    # Get response from Gemini
    response = model.generate_content(prompt)
    
    return {
        "analysis": response.text,
        "files_analyzed": list(files_content.keys())
    }

def main():
    parser = argparse.ArgumentParser(description="Analyze staged code with Gemini")
    parser.add_argument(
        "--extensions", 
        default=".py,.js,.ts",
        help="Comma-separated list of file extensions to analyze"
    )
    args = parser.parse_args()
    
    # Get file extensions to analyze
    extensions = args.extensions.split(",")
    
    # Get staged files
    staged_files = get_staged_files(extensions)
    
    if not staged_files:
        print("No matching files staged for commit.")
        return 0
    
    print(f"Running Gemini code analysis on staged files...")
    print(f"Files: {','.join(staged_files)}")
    
    # Read file contents
    files_content = {}
    for file_path in staged_files:
        content = read_file_content(file_path)
        if content:
            files_content[file_path] = content
    
    if not files_content:
        print("No valid files to analyze.")
        return 1
    
    try:
        # Analyze code
        results = analyze_code_with_gemini(files_content)
        
        # Print analysis results
        print("\n===== Gemini Code Analysis =====\n")
        print(results["analysis"])
        print("\n================================\n")
        
        # Ask if user wants to proceed with commit
        response = input("Proceed with commit? (y/n): ").lower()
        if response != 'y':
            print("Commit aborted by user.")
            return 1
            
        return 0
        
    except Exception as e:
        print(f"Error during code analysis: {str(e)}")
        print("You can still commit, but consider fixing the analysis script.")
        return 0

if __name__ == "__main__":
    sys.exit(main())