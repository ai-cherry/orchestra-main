#!/bin/bash

echo "Security Scanner - Checking for Hardcoded Credentials"
echo "===================================================="

# Create security scanner Python script
cat > security_scanner.py << 'EOF'
#!/usr/bin/env python3
"""
Security Scanner for detecting hardcoded credentials and sensitive data
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

class SecurityScanner:
    def __init__(self):
        self.findings = []
        self.stats = {
            'files_scanned': 0,
            'issues_found': 0,
            'critical': 0,
            'high': 0,
            'medium': 0
        }
        
        # Patterns for detecting sensitive data
        self.patterns = {
            'api_key': {
                'pattern': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
                'severity': 'critical',
                'description': 'Hardcoded API key'
            },
            'password': {
                'pattern': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']([^"\']+)["\']',
                'severity': 'critical',
                'description': 'Hardcoded password'
            },
            'secret': {
                'pattern': r'(?i)(secret|private[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
                'severity': 'critical',
                'description': 'Hardcoded secret/private key'
            },
            'aws_key': {
                'pattern': r'(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*["\']?([A-Z0-9]{20})["\']?',
                'severity': 'critical',
                'description': 'AWS credentials'
            },
            'database_url': {
                'pattern': r'(?i)(database[_-]?url|db[_-]?url|connection[_-]?string)\s*[:=]\s*["\']([^"\']+@[^"\']+)["\']',
                'severity': 'high',
                'description': 'Database connection string with credentials'
            },
            'token': {
                'pattern': r'(?i)(token|auth[_-]?token|access[_-]?token)\s*[:=]\s*["\']([a-zA-Z0-9_\-\.]{20,})["\']',
                'severity': 'high',
                'description': 'Authentication token'
            },
            'private_ip': {
                'pattern': r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b',
                'severity': 'medium',
                'description': 'Private IP address'
            }
        }
        
        # Files to skip
        self.skip_extensions = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe', '.bin'}
        self.skip_dirs = {'__pycache__', '.git', 'node_modules', 'venv', '.env', 'dist', 'build'}
    
    def scan_file(self, filepath: str) -> List[Dict]:
        """Scan a single file for security issues"""
        findings = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check each pattern
            for pattern_name, pattern_info in self.patterns.items():
                matches = re.finditer(pattern_info['pattern'], content)
                
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Extract the matched value (redacted)
                    if len(match.groups()) > 1:
                        value = match.group(2)
                        redacted = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
                    else:
                        value = match.group(0)
                        redacted = value[:10] + '...' if len(value) > 10 else value
                    
                    finding = {
                        'file': filepath,
                        'line': line_num,
                        'type': pattern_name,
                        'severity': pattern_info['severity'],
                        'description': pattern_info['description'],
                        'match': redacted,
                        'context': self._get_context(content, match.start(), match.end())
                    }
                    
                    findings.append(finding)
                    self.stats['issues_found'] += 1
                    self.stats[pattern_info['severity']] += 1
                    
        except Exception as e:
            print(f"Error scanning {filepath}: {e}")
            
        return findings
    
    def _get_context(self, content: str, start: int, end: int, context_size: int = 50) -> str:
        """Get context around the match"""
        context_start = max(0, start - context_size)
        context_end = min(len(content), end + context_size)
        context = content[context_start:context_end]
        return context.replace('\n', ' ').strip()
    
    def scan_directory(self, directory: str):
        """Scan all files in directory"""
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                # Skip certain file types
                if Path(file).suffix in self.skip_extensions:
                    continue
                    
                self.stats['files_scanned'] += 1
                
                findings = self.scan_file(filepath)
                self.findings.extend(findings)
    
    def generate_report(self) -> Dict:
        """Generate security scan report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'findings': self.findings,
            'summary': {
                'total_issues': len(self.findings),
                'by_severity': {
                    'critical': self.stats['critical'],
                    'high': self.stats['high'],
                    'medium': self.stats['medium']
                },
                'by_type': self._count_by_type()
            }
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count findings by type"""
        counts = {}
        for finding in self.findings:
            finding_type = finding['type']
            counts[finding_type] = counts.get(finding_type, 0) + 1
        return counts


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Security scanner for hardcoded credentials')
    parser.add_argument('--directory', default='.', help='Directory to scan')
    parser.add_argument('--output', default='security_scan_report.json', help='Output report file')
    
    args = parser.parse_args()
    
    print(f"Scanning directory: {args.directory}")
    
    scanner = SecurityScanner()
    scanner.scan_directory(args.directory)
    
    report = scanner.generate_report()
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("SECURITY SCAN SUMMARY")
    print("="*60)
    print(f"Files scanned: {report['statistics']['files_scanned']}")
    print(f"Total issues found: {report['summary']['total_issues']}")
    print(f"\nBy Severity:")
    print(f"  Critical: {report['summary']['by_severity']['critical']}")
    print(f"  High: {report['summary']['by_severity']['high']}")
    print(f"  Medium: {report['summary']['by_severity']['medium']}")
    
    if report['findings']:
        print(f"\nTop Issues:")
        # Show first 5 critical issues
        critical_issues = [f for f in report['findings'] if f['severity'] == 'critical']
        for issue in critical_issues[:5]:
            print(f"  - {issue['file']}:{issue['line']} - {issue['description']}")
        
        if len(critical_issues) > 5:
            print(f"  ... and {len(critical_issues) - 5} more critical issues")
    
    print(f"\nFull report saved to: {args.output}")


if __name__ == "__main__":
    main()
EOF

# Make it executable
chmod +x security_scanner.py

# Run the security scan
echo "Running security scan..."
python3 security_scanner.py --directory . --output security_scan_report_$(date +%Y%m%d_%H%M%S).json

echo ""
echo "Security scan complete!"
echo ""
echo "Next steps:"
echo "1. Review the security scan report"
echo "2. Remove or secure any hardcoded credentials"
echo "3. Use environment variables or secure vaults for sensitive data"
echo "4. Add .env files to .gitignore"