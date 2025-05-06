#!/usr/bin/env python3
"""
Credential Scanner for AI Orchestra

This script scans the codebase for potential hardcoded credentials and security issues.
It helps identify files that may need to be updated to use the secure credential management system.

Usage:
    python scripts/scan_for_credentials.py [--path /path/to/scan] [--output report.json]

Options:
    --path      Path to scan (default: current directory)
    --output    Output file for the report (default: credential_scan_report.json)
    --verbose   Show detailed output during scanning
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple, Set


# Patterns to search for
CREDENTIAL_PATTERNS = [
    # API Keys
    r'(?i)api[_-]?key[_-]?(?:id)?[\s]*[=:]\s*["\']([a-zA-Z0-9_\-\.]{20,})["\']',
    r'(?i)(?:secret|private)[_-]?key[\s]*[=:]\s*["\']([a-zA-Z0-9_\-\.]{20,})["\']',
    
    # GCP Service Account Keys
    r'(?i)"type":\s*"service_account"',
    r'(?i)"private_key":\s*"-----BEGIN PRIVATE KEY-----',
    r'(?i)"client_email":\s*"[^"]+@[^"]+\.iam\.gserviceaccount\.com"',
    
    # Passwords
    r'(?i)password[\s]*[=:]\s*["\']([^"\']{8,})["\']',
    r'(?i)passwd[\s]*[=:]\s*["\']([^"\']{8,})["\']',
    r'(?i)pwd[\s]*[=:]\s*["\']([^"\']{8,})["\']',
    
    # Connection strings
    r'(?i)(?:mongodb|postgres|mysql|redis|jdbc)(?:[\w]*://)[^\s"\'<>]+',
    
    # Hardcoded project IDs
    r'(?i)project[_-]?id[\s]*[=:]\s*["\']([a-zA-Z0-9_\-\.]+)["\']',
    
    # Hardcoded organization IDs
    r'(?i)org(?:anization)?[_-]?id[\s]*[=:]\s*["\']([0-9]{9,})["\']',
    
    # Tokens
    r'(?i)(?:access|auth|oauth|refresh)[_-]?token[\s]*[=:]\s*["\']([a-zA-Z0-9_\-\.]{20,})["\']',
    
    # Base64 encoded data (potential certificates or keys)
    r'(?i)(?:eyJ|MII)[a-zA-Z0-9+/=]{40,}',
]

# Files and directories to exclude
EXCLUDE_PATTERNS = [
    r'\.git',
    r'\.venv',
    r'__pycache__',
    r'node_modules',
    r'\.pytest_cache',
    r'\.mypy_cache',
    r'\.vscode',
    r'\.idea',
    r'\.DS_Store',
    r'\.env\.example',
    r'credential_scan_report\.json',
    r'.*\.pyc$',
    r'.*\.pyo$',
    r'.*\.so$',
    r'.*\.o$',
    r'.*\.a$',
    r'.*\.dll$',
    r'.*\.exe$',
    r'.*\.bin$',
    r'.*\.jpg$',
    r'.*\.jpeg$',
    r'.*\.png$',
    r'.*\.gif$',
    r'.*\.pdf$',
    r'.*\.zip$',
    r'.*\.tar$',
    r'.*\.gz$',
    r'.*\.lock$',
]

# File extensions to scan
INCLUDE_EXTENSIONS = [
    '.py', '.js', '.ts', '.sh', '.bash', '.yml', '.yaml', '.json', '.tf', '.tfvars',
    '.md', '.txt', '.env', '.ini', '.cfg', '.conf', '.xml', '.html', '.css',
    '.go', '.java', '.kt', '.rb', '.php', '.c', '.cpp', '.h', '.hpp', '.cs',
    '.dockerfile', 'Dockerfile', '.dockerignore', '.gitignore', '.gitattributes',
    '.htaccess', '.htpasswd', '.npmrc', '.yarnrc', '.pypirc', '.netrc',
    'requirements.txt', 'package.json', 'composer.json', 'Gemfile',
]


def should_exclude(path: str) -> bool:
    """Check if a path should be excluded from scanning."""
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, path):
            return True
    return False


def should_include(path: str) -> bool:
    """Check if a file should be included in scanning based on its extension."""
    _, ext = os.path.splitext(path)
    if os.path.basename(path) in INCLUDE_EXTENSIONS:
        return True
    return ext.lower() in INCLUDE_EXTENSIONS


def scan_file(file_path: str) -> List[Dict[str, Any]]:
    """Scan a file for potential credentials."""
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            for i, line in enumerate(content.splitlines(), 1):
                for pattern in CREDENTIAL_PATTERNS:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        # Extract a snippet of the line for context, but mask the actual credential
                        start_pos = max(0, match.start() - 10)
                        end_pos = min(len(line), match.end() + 10)
                        snippet = line[start_pos:end_pos]
                        
                        # Mask the actual credential in the snippet
                        if match.groups():
                            credential = match.group(1)
                            masked_credential = credential[:3] + '*' * (len(credential) - 6) + credential[-3:] if len(credential) > 6 else '*' * len(credential)
                            snippet = snippet.replace(credential, masked_credential)
                        
                        findings.append({
                            'file': file_path,
                            'line': i,
                            'pattern_type': pattern,
                            'snippet': snippet.strip(),
                            'confidence': 'high' if 'private_key' in pattern or 'api_key' in pattern.lower() else 'medium'
                        })
    except Exception as e:
        print(f"Error scanning file {file_path}: {str(e)}", file=sys.stderr)
    
    return findings


def scan_directory(directory: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """Recursively scan a directory for files with potential credentials."""
    all_findings = []
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(os.path.join(root, d))]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            if should_exclude(file_path):
                continue
                
            if not should_include(file_path):
                continue
            
            if verbose:
                print(f"Scanning {file_path}...")
            
            findings = scan_file(file_path)
            all_findings.extend(findings)
            
            if findings and verbose:
                print(f"  Found {len(findings)} potential issues")
    
    return all_findings


def generate_report(findings: List[Dict[str, Any]], output_file: str) -> None:
    """Generate a JSON report of the findings."""
    report = {
        'scan_time': datetime.now().isoformat(),
        'total_findings': len(findings),
        'findings_by_file': {},
        'findings_by_confidence': {
            'high': 0,
            'medium': 0,
            'low': 0
        }
    }
    
    # Group findings by file
    for finding in findings:
        file_path = finding['file']
        if file_path not in report['findings_by_file']:
            report['findings_by_file'][file_path] = []
        
        report['findings_by_file'][file_path].append(finding)
        
        # Count by confidence
        confidence = finding.get('confidence', 'medium')
        report['findings_by_confidence'][confidence] += 1
    
    # Sort files by number of findings
    sorted_files = sorted(
        report['findings_by_file'].items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    report['findings_by_file'] = {k: v for k, v in sorted_files}
    
    # Write the report
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)


def print_summary(findings: List[Dict[str, Any]]) -> None:
    """Print a summary of the findings."""
    if not findings:
        print("\n✅ No potential credentials found!")
        return
    
    print(f"\n⚠️ Found {len(findings)} potential credentials in {len(set(f['file'] for f in findings))} files")
    
    # Count by confidence
    confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
    for finding in findings:
        confidence = finding.get('confidence', 'medium')
        confidence_counts[confidence] += 1
    
    print(f"  High confidence: {confidence_counts['high']}")
    print(f"  Medium confidence: {confidence_counts['medium']}")
    print(f"  Low confidence: {confidence_counts['low']}")
    
    # Top 5 files with most findings
    file_counts = {}
    for finding in findings:
        file_path = finding['file']
        file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    if top_files:
        print("\nTop files with potential credentials:")
        for file_path, count in top_files:
            print(f"  {file_path}: {count} findings")


def main():
    parser = argparse.ArgumentParser(description='Scan codebase for potential hardcoded credentials')
    parser.add_argument('--path', default='.', help='Path to scan (default: current directory)')
    parser.add_argument('--output', default='credential_scan_report.json', help='Output file for the report')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output during scanning')
    
    args = parser.parse_args()
    
    print(f"Scanning {args.path} for potential credentials...")
    findings = scan_directory(args.path, args.verbose)
    
    print_summary(findings)
    
    generate_report(findings, args.output)
    print(f"\nDetailed report saved to {args.output}")


if __name__ == '__main__':
    main()