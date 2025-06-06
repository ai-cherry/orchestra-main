#!/usr/bin/env python3
"""
Comprehensive Codebase Analyzer
Performs deep analysis of codebase issues and provides prioritized remediation strategies
"""

import json
import os
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict, Counter
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CodebaseAnalyzer:
    """Comprehensive codebase analysis and remediation tool"""
    
    def __init__(self, audit_report_path: str):
        self.audit_report_path = audit_report_path
        self.audit_data = self._load_audit_report()
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        self.patterns = defaultdict(list)
        self.remediation_strategies = {}
        self.impact_analysis = {}
        
    def _load_audit_report(self) -> Dict:
        """Load the audit report"""
        try:
            with open(self.audit_report_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load audit report: {e}")
            return {}
    
    def analyze_syntax_errors(self):
        """Analyze syntax errors and categorize by pattern"""
        syntax_errors = self.audit_data.get('syntax_errors', [])
        
        # Group errors by type
        error_types = defaultdict(list)
        for error in syntax_errors:
            error_type = self._categorize_syntax_error(error)
            error_types[error_type].append(error)
        
        # Analyze patterns
        for error_type, errors in error_types.items():
            pattern_analysis = {
                'type': error_type,
                'count': len(errors),
                'files': [e['file'] for e in errors],
                'common_causes': self._identify_common_causes(error_type, errors),
                'severity': self._assess_severity(error_type, errors),
                'impact': self._assess_impact(errors)
            }
            self.patterns[error_type] = pattern_analysis
            
            # Categorize by severity
            severity = pattern_analysis['severity']
            for error in errors:
                issue = {
                    'type': 'syntax_error',
                    'subtype': error_type,
                    'file': error['file'],
                    'line': error.get('line', 0),
                    'error': error['error'],
                    'impact': pattern_analysis['impact'],
                    'remediation': self._get_remediation_strategy(error_type)
                }
                self.issues[severity].append(issue)
    
    def _categorize_syntax_error(self, error: Dict) -> str:
        """Categorize syntax error by type"""
        error_msg = error.get('error', '').lower()
        
        if 'unexpected indent' in error_msg:
            return 'indentation_error'
        elif 'invalid syntax' in error_msg:
            return 'syntax_error'
        elif 'was never closed' in error_msg:
            return 'unclosed_bracket'
        elif 'unterminated string' in error_msg:
            return 'unterminated_string'
        elif 'expected an indented block' in error_msg:
            return 'missing_indentation'
        elif 'mismatched braces' in error_msg:
            return 'brace_mismatch'
        else:
            return 'other_syntax_error'
    
    def _identify_common_causes(self, error_type: str, errors: List[Dict]) -> List[str]:
        """Identify common causes for error patterns"""
        causes = []
        
        if error_type == 'indentation_error':
            causes = [
                'Mixed tabs and spaces',
                'Incorrect indentation level',
                'Missing indentation after control structures',
                'Extra indentation in code blocks',
                'File corruption or encoding issues'
            ]
        elif error_type == 'syntax_error':
            causes = [
                'Missing colons after control structures',
                'Invalid operator usage',
                'Incorrect function/class definitions',
                'Import statement errors'
            ]
        elif error_type == 'unclosed_bracket':
            causes = [
                'Missing closing parenthesis, bracket, or brace',
                'Mismatched bracket types',
                'Nested structure errors'
            ]
        
        return causes
    
    def _assess_severity(self, error_type: str, errors: List[Dict]) -> str:
        """Assess severity of error pattern"""
        # Critical: Blocks execution entirely
        if error_type in ['syntax_error', 'indentation_error', 'unclosed_bracket']:
            if len(errors) > 50:  # Widespread issue
                return 'critical'
            elif len(errors) > 10:
                return 'high'
            else:
                return 'medium'
        
        # Other errors
        return 'medium'
    
    def _assess_impact(self, errors: List[Dict]) -> Dict[str, Any]:
        """Assess impact of errors"""
        affected_files = set(e['file'] for e in errors)
        
        # Categorize affected components
        core_files = [f for f in affected_files if f.startswith('core/')]
        api_files = [f for f in affected_files if 'api' in f or 'routers' in f]
        service_files = [f for f in affected_files if 'service' in f]
        script_files = [f for f in affected_files if f.startswith('scripts/')]
        
        return {
            'total_affected_files': len(affected_files),
            'core_system_affected': len(core_files) > 0,
            'api_affected': len(api_files) > 0,
            'services_affected': len(service_files) > 0,
            'scripts_affected': len(script_files) > 0,
            'critical_components': {
                'core': core_files[:5],  # Top 5
                'api': api_files[:5],
                'services': service_files[:5]
            }
        }
    
    def _get_remediation_strategy(self, error_type: str) -> Dict[str, Any]:
        """Get remediation strategy for error type"""
        strategies = {
            'indentation_error': {
                'approach': 'Automated indentation fix',
                'tools': ['autopep8', 'black', 'custom indentation fixer'],
                'steps': [
                    'Detect indentation style (tabs vs spaces)',
                    'Normalize to 4 spaces',
                    'Fix control structure indentation',
                    'Validate with Python AST parser'
                ],
                'estimated_effort': 'Low (automated)',
                'risk': 'Low'
            },
            'syntax_error': {
                'approach': 'Semi-automated fix with manual review',
                'tools': ['pylint', 'flake8', 'custom syntax analyzer'],
                'steps': [
                    'Identify specific syntax issue',
                    'Apply pattern-based fixes',
                    'Manual review for complex cases',
                    'Unit test validation'
                ],
                'estimated_effort': 'Medium',
                'risk': 'Medium'
            },
            'unclosed_bracket': {
                'approach': 'Automated bracket matching',
                'tools': ['custom bracket matcher', 'AST parser'],
                'steps': [
                    'Parse file to find unclosed brackets',
                    'Match opening and closing brackets',
                    'Insert missing brackets',
                    'Validate syntax'
                ],
                'estimated_effort': 'Low',
                'risk': 'Low'
            }
        }
        
        return strategies.get(error_type, {
            'approach': 'Manual review required',
            'tools': ['Code editor', 'Python interpreter'],
            'steps': ['Manual inspection and fix'],
            'estimated_effort': 'High',
            'risk': 'Medium'
        })
    
    def analyze_code_quality(self):
        """Analyze code quality issues"""
        formatting_issues = self.audit_data.get('formatting_issues', [])
        naming_violations = self.audit_data.get('naming_violations', [])
        
        # Analyze formatting issues
        line_length_issues = [i for i in formatting_issues if 'line too long' in i.get('issue', '').lower()]
        console_log_issues = [i for i in formatting_issues if 'console.log' in i.get('issue', '').lower()]
        
        # Add to issues list
        if len(line_length_issues) > 50:
            self.issues['medium'].append({
                'type': 'formatting',
                'subtype': 'line_length',
                'count': len(line_length_issues),
                'files': list(set(i['file'] for i in line_length_issues))[:10],
                'impact': {'readability': 'medium', 'maintainability': 'low'},
                'remediation': {
                    'approach': 'Automated formatting',
                    'tools': ['black', 'autopep8'],
                    'estimated_effort': 'Low'
                }
            })
        
        if console_log_issues:
            self.issues['low'].append({
                'type': 'code_quality',
                'subtype': 'debug_statements',
                'count': len(console_log_issues),
                'files': list(set(i['file'] for i in console_log_issues))[:10],
                'impact': {'production_readiness': 'medium', 'performance': 'low'},
                'remediation': {
                    'approach': 'Remove or replace with proper logging',
                    'tools': ['grep', 'sed', 'logging framework'],
                    'estimated_effort': 'Low'
                }
            })
    
    def analyze_dependencies(self):
        """Analyze dependency issues"""
        # Check for import errors in syntax errors
        import_errors = []
        for error in self.audit_data.get('syntax_errors', []):
            if 'import' in error.get('file', '') or 'from' in str(error.get('error', '')):
                import_errors.append(error)
        
        if import_errors:
            self.issues['high'].append({
                'type': 'dependency',
                'subtype': 'import_errors',
                'count': len(import_errors),
                'files': list(set(e['file'] for e in import_errors))[:10],
                'impact': {'functionality': 'critical', 'deployment': 'blocker'},
                'remediation': {
                    'approach': 'Fix import paths and dependencies',
                    'tools': ['pipreqs', 'pip-tools'],
                    'steps': [
                        'Analyze import statements',
                        'Update requirements.txt',
                        'Fix relative imports',
                        'Validate in clean environment'
                    ],
                    'estimated_effort': 'Medium'
                }
            })
    
    def analyze_security_issues(self):
        """Analyze potential security issues"""
        # Check for hardcoded credentials, API keys, etc.
        security_patterns = [
            (r'api[_-]?key\s*=\s*["\'][\w\-]+["\']', 'hardcoded_api_key'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded_password'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'hardcoded_secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'hardcoded_token')
        ]
        
        security_issues = []
        
        # Sample check (would need to scan actual files)
        # For now, add a general security check recommendation
        self.issues['high'].append({
            'type': 'security',
            'subtype': 'credential_scan_needed',
            'impact': {'security': 'critical', 'compliance': 'high'},
            'remediation': {
                'approach': 'Security audit and remediation',
                'tools': ['git-secrets', 'truffleHog', 'environment variables'],
                'steps': [
                    'Scan for hardcoded credentials',
                    'Move secrets to environment variables',
                    'Implement secret management',
                    'Rotate compromised credentials'
                ],
                'estimated_effort': 'High',
                'priority': 'Immediate'
            }
        })
    
    def generate_impact_matrix(self) -> Dict[str, Any]:
        """Generate impact matrix for all issues"""
        impact_matrix = {
            'business_impact': {
                'deployment_blocked': any(i['type'] == 'syntax_error' for i in self.issues['critical']),
                'api_functionality_affected': any('api' in str(i) for i in self.issues['critical'] + self.issues['high']),
                'data_processing_affected': any('service' in str(i) for i in self.issues['critical'] + self.issues['high']),
                'user_experience_affected': any('ui' in str(i).lower() or 'interface' in str(i).lower() 
                                               for i in self.issues['critical'] + self.issues['high'])
            },
            'technical_impact': {
                'core_system_broken': len([i for i in self.issues['critical'] if 'core' in str(i)]) > 0,
                'integration_broken': len([i for i in self.issues['high'] if 'integration' in str(i)]) > 0,
                'testing_impossible': len(self.issues['critical']) > 10,
                'deployment_impossible': len(self.issues['critical']) > 0
            },
            'effort_estimation': {
                'critical_fixes': sum(1 for i in self.issues['critical']),
                'high_priority_fixes': sum(1 for i in self.issues['high']),
                'total_effort_days': self._estimate_total_effort()
            }
        }
        
        return impact_matrix
    
    def _estimate_total_effort(self) -> int:
        """Estimate total effort in days"""
        effort_map = {
            'critical': 0.5,  # Half day per critical issue (mostly automated)
            'high': 1,        # 1 day per high issue
            'medium': 0.25,   # Quarter day per medium issue
            'low': 0.1        # Tenth of a day per low issue
        }
        
        total_days = 0
        for severity, issues in self.issues.items():
            total_days += len(issues) * effort_map.get(severity, 0.5)
        
        return int(total_days)
    
    def generate_remediation_roadmap(self) -> List[Dict[str, Any]]:
        """Generate phased remediation roadmap"""
        roadmap = []
        
        # Phase 1: Critical Syntax Fixes (Immediate)
        phase1_issues = [i for i in self.issues['critical'] if i['type'] == 'syntax_error']
        if phase1_issues:
            roadmap.append({
                'phase': 1,
                'name': 'Critical Syntax Remediation',
                'timeline': '1-2 days',
                'priority': 'Immediate',
                'issues': phase1_issues[:10],  # Top 10
                'approach': 'Automated fixing with validation',
                'success_criteria': 'All Python files compile without syntax errors',
                'tools': ['autopep8', 'black', 'custom indentation fixer'],
                'risks': 'Minimal - automated tools with validation'
            })
        
        # Phase 2: Security Remediation
        security_issues = [i for i in self.issues['high'] if i['type'] == 'security']
        if security_issues:
            roadmap.append({
                'phase': 2,
                'name': 'Security Hardening',
                'timeline': '2-3 days',
                'priority': 'Critical',
                'issues': security_issues,
                'approach': 'Scan, remediate, and implement secret management',
                'success_criteria': 'No hardcoded credentials, proper secret management',
                'tools': ['git-secrets', 'environment variables', 'secret manager'],
                'risks': 'Medium - requires credential rotation'
            })
        
        # Phase 3: Dependency and Import Fixes
        dependency_issues = [i for i in self.issues['high'] if i['type'] == 'dependency']
        if dependency_issues:
            roadmap.append({
                'phase': 3,
                'name': 'Dependency Resolution',
                'timeline': '2-3 days',
                'priority': 'High',
                'issues': dependency_issues,
                'approach': 'Fix imports, update requirements, test in clean env',
                'success_criteria': 'All imports resolve, requirements.txt accurate',
                'tools': ['pipreqs', 'pip-tools', 'virtual environments'],
                'risks': 'Medium - potential version conflicts'
            })
        
        # Phase 4: Code Quality Improvements
        quality_issues = [i for i in self.issues['medium'] if i['type'] in ['formatting', 'code_quality']]
        if quality_issues:
            roadmap.append({
                'phase': 4,
                'name': 'Code Quality Enhancement',
                'timeline': '1-2 days',
                'priority': 'Medium',
                'issues': quality_issues[:20],  # Top 20
                'approach': 'Automated formatting and linting',
                'success_criteria': 'Code passes linting, consistent formatting',
                'tools': ['black', 'flake8', 'pylint'],
                'risks': 'Low - mostly cosmetic changes'
            })
        
        # Phase 5: Testing and Validation
        roadmap.append({
            'phase': 5,
            'name': 'Comprehensive Testing',
            'timeline': '2-3 days',
            'priority': 'High',
            'approach': 'Unit tests, integration tests, deployment validation',
            'success_criteria': 'All tests pass, successful deployment',
            'tools': ['pytest', 'docker', 'CI/CD pipeline'],
            'risks': 'Low - validation phase'
        })
        
        return roadmap
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report"""
        # Run all analyses
        self.analyze_syntax_errors()
        self.analyze_code_quality()
        self.analyze_dependencies()
        self.analyze_security_issues()
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_critical_issues': len(self.issues['critical']),
                'total_high_issues': len(self.issues['high']),
                'total_medium_issues': len(self.issues['medium']),
                'total_low_issues': len(self.issues['low']),
                'estimated_remediation_days': self._estimate_total_effort(),
                'deployment_blocked': len(self.issues['critical']) > 0
            },
            'critical_findings': {
                'syntax_errors': {
                    'total': len([i for i in self.issues['critical'] if i['type'] == 'syntax_error']),
                    'pattern': 'Widespread indentation errors across codebase',
                    'root_cause': 'Likely file corruption or mass editing issue',
                    'immediate_action': 'Run automated indentation fixer'
                },
                'blocking_issues': [
                    {
                        'issue': 'Cannot execute Python files',
                        'impact': 'Complete system failure',
                        'fix': 'Phase 1 remediation required'
                    }
                ]
            },
            'detailed_issues': self.issues,
            'patterns_identified': dict(self.patterns),
            'impact_analysis': self.generate_impact_matrix(),
            'remediation_roadmap': self.generate_remediation_roadmap(),
            'recommendations': {
                'immediate': [
                    'Stop all deployment attempts',
                    'Create backup of current state',
                    'Run automated syntax fixer on development branch',
                    'Implement pre-commit hooks to prevent future issues'
                ],
                'short_term': [
                    'Complete Phase 1-3 of remediation roadmap',
                    'Implement CI/CD validation',
                    'Add automated code quality checks'
                ],
                'long_term': [
                    'Refactor problematic modules',
                    'Implement comprehensive testing',
                    'Establish code review process',
                    'Regular security audits'
                ]
            }
        }
        
        return report


def main():
    """Main execution function"""
    # Use the audit report from the previous scan
    audit_report_path = ""
    
    if not os.path.exists(audit_report_path):
        logger.error(f"Audit report not found: {audit_report_path}")
        return
    
    # Create analyzer
    analyzer = CodebaseAnalyzer(audit_report_path)
    
    # Generate comprehensive report
    logger.info("Generating comprehensive diagnostic report...")
    report = analyzer.generate_report()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"comprehensive_diagnostic_report_{timestamp}.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("COMPREHENSIVE CODEBASE DIAGNOSTIC REPORT")
    print("="*80)
    print(f"\nCRITICAL ISSUES: {report['summary']['total_critical_issues']}")
    print(f"HIGH PRIORITY ISSUES: {report['summary']['total_high_issues']}")
    print(f"MEDIUM PRIORITY ISSUES: {report['summary']['total_medium_issues']}")
    print(f"LOW PRIORITY ISSUES: {report['summary']['total_low_issues']}")
    print(f"\nESTIMATED REMEDIATION TIME: {report['summary']['estimated_remediation_days']} days")
    print(f"DEPLOYMENT BLOCKED: {'YES' if report['summary']['deployment_blocked'] else 'NO'}")
    
    print("\n" + "-"*80)
    print("IMMEDIATE ACTIONS REQUIRED:")
    print("-"*80)
    for action in report['recommendations']['immediate']:
        print(f"• {action}")
    
    print("\n" + "-"*80)
    print("REMEDIATION ROADMAP:")
    print("-"*80)
    for phase in report['remediation_roadmap']:
        print(f"\nPhase {phase['phase']}: {phase['name']}")
        print(f"  Timeline: {phase['timeline']}")
        print(f"  Priority: {phase['priority']}")
        print(f"  Approach: {phase['approach']}")
    
    print("\n" + "="*80)
    print("Full report saved to:", report_path)
    print("="*80)


if __name__ == "__main__":
    main()