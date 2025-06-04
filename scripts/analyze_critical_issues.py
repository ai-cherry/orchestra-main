#!/usr/bin/env python3
"""
Analyze critical issues from backend audit and categorize them
"""

import json
from collections.abc import defaultdict
from pathlib import Path

def analyze_critical_issues():
    """Analyze and categorize critical issues"""
    
    # Load the audit report
    with open('backend_audit_report_20250603_215202.json', 'r') as f:
        report = json.load(f)
    
    # Categorize critical issues
    critical_by_category = defaultdict(list)
    high_by_category = defaultdict(list)
    
    for issue in report['issues']['critical']:
        critical_by_category[issue['category']].append(issue)
        
    for issue in report['issues']['high']:
        high_by_category[issue['category']].append(issue)
    
    print("🚨 CRITICAL ISSUES ANALYSIS")
    print("=" * 50)
    
    # Print critical issues by category
    print("\nCritical Issues by Category:")
    for category, issues in critical_by_category.items():
        print(f"\n{category.upper()}: {len(issues)} issues")
        
        # Show sample issues
        unique_issues = {}
        for issue in issues:
            issue_type = issue['issue']
            if issue_type not in unique_issues:
                unique_issues[issue_type] = []
            unique_issues[issue_type].append(issue)
        
        for issue_type, examples in list(unique_issues.items())[:5]:
            print(f"  - {issue_type} ({len(examples)} occurrences)")
            if examples[0]['suggestion']:
                print(f"    Fix: {examples[0]['suggestion']}")
    
    print("\n" + "=" * 50)
    print("\nHigh Priority Issues by Category:")
    for category, issues in high_by_category.items():
        print(f"\n{category.upper()}: {len(issues)} issues")
        
        # Show unique issue types
        unique_issues = set()
        for issue in issues:
            unique_issues.add(issue['issue'])
        
        for issue_type in list(unique_issues)[:3]:
            print(f"  - {issue_type}")
    
    # Identify most affected files
    print("\n" + "=" * 50)
    print("\nMost Affected Files:")
    file_issues = defaultdict(int)
    for severity in ['critical', 'high']:
        for issue in report['issues'][severity]:
            file_issues[issue['file']] += 1
    
    sorted_files = sorted(file_issues.items(), key=lambda x: x[1], reverse=True)
    for file_path, count in sorted_files[:10]:
        print(f"  {file_path}: {count} critical/high issues")
    
    return report

if __name__ == "__main__":
    analyze_critical_issues()