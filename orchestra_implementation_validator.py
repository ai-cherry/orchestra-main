#!/usr/bin/env python3
"""
Orchestra Implementation Validator
Final validation and handoff preparation for debugging specialist
"""

import os
import json
import subprocess
import sys
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImplementationValidator:
    """Validates the complete Orchestra implementation"""
    
    def __init__(self):
        self.validation_results = {}
        self.handoff_package = {}
        self.critical_issues = []
        self.recommendations = []
        
    def validate_all_components(self) -> Dict[str, Any]:
        """Run comprehensive validation of all components"""
        logger.info("🔍 Running Comprehensive Implementation Validation")
        
        # 1. Architecture Blueprint Validation
        self.validate_architecture_blueprint()
        
        # 2. Security Remediation Status
        self.validate_security_fixes()
        
        # 3. Infrastructure Readiness
        self.validate_infrastructure()
        
        # 4. Code Quality Metrics
        self.validate_code_quality()
        
        # 5. Deployment Configuration
        self.validate_deployment_config()
        
        # 6. Integration Points
        self.validate_integrations()
        
        # 7. Performance Baselines
        self.establish_performance_baselines()
        
        # 8. Monitoring Setup
        self.validate_monitoring()
        
        return self.validation_results
    
    def validate_architecture_blueprint(self):
        """Validate architecture blueprint implementation"""
        logger.info("📐 Validating Architecture Blueprint...")
        
        results = {
            "blueprint_exists": False,
            "components_defined": 0,
            "phases_defined": 0,
            "security_framework": False,
            "error_handling": False,
            "performance_optimization": False
        }
        
        try:
            if os.path.exists('architecture_blueprint.json'):
                with open('architecture_blueprint.json', 'r') as f:
                    blueprint = json.load(f)
                
                results["blueprint_exists"] = True
                results["components_defined"] = len(blueprint.get('components', []))
                results["phases_defined"] = len(blueprint.get('implementation_roadmap', []))
                results["security_framework"] = 'security_framework' in blueprint
                results["error_handling"] = 'error_handling_framework' in blueprint
                results["performance_optimization"] = 'performance_optimization' in blueprint
                
                # Check component completeness
                required_components = [
                    'postgres_db', 'redis_cache', 'api_gateway', 
                    'orchestration_service', 'weaviate_vector_db'
                ]
                
                component_names = [c['name'] for c in blueprint.get('components', [])]
                missing_components = [c for c in required_components if c not in component_names]
                
                if missing_components:
                    self.critical_issues.append(f"Missing components: {missing_components}")
            else:
                self.critical_issues.append("Architecture blueprint not found!")
                
        except Exception as e:
            logger.error(f"Error validating blueprint: {e}")
            self.critical_issues.append(f"Blueprint validation error: {e}")
        
        self.validation_results['architecture'] = results
    
    def validate_security_fixes(self):
        """Validate security remediation status"""
        logger.info("🔒 Validating Security Fixes...")
        
        results = {
            "env_template_exists": os.path.exists('.env.template'),
            "credentials_fixed": 0,
            "sql_injection_warnings": 0,
            "bare_except_fixed": 0,
            "security_headers_configured": False
        }
        
        # Check for security remediation report
        security_reports = [f for f in os.listdir('.') if f.startswith('security_remediation_report_')]
        if security_reports:
            latest_report = sorted(security_reports)[-1]
            with open(latest_report, 'r') as f:
                report = json.load(f)
            
            results["credentials_fixed"] = report['summary'].get('credentials_fixed', 0)
            results["sql_injection_warnings"] = report['summary'].get('sql_injection_warnings', 0)
            results["bare_except_fixed"] = report['summary'].get('bare_except_fixed', 0)
        
        # Check for remaining hardcoded credentials
        remaining_credentials = self._scan_for_credentials()
        if remaining_credentials:
            self.critical_issues.append(f"Found {len(remaining_credentials)} remaining hardcoded credentials")
            results["remaining_credentials"] = len(remaining_credentials)
        
        self.validation_results['security'] = results
    
    def _scan_for_credentials(self) -> List[str]:
        """Quick scan for remaining hardcoded credentials"""
        credentials = []
        patterns = ['password=', 'api_key=', 'secret=', 'token=']
        
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(file_path, 'r') as f:
                            for i, line in enumerate(f, 1):
                                for pattern in patterns:
                                    if pattern in line.lower() and 'os.getenv' not in line:
                                        credentials.append(f"{file_path}:{i}")
                    except:
                        pass
        
        return credentials
    
    def validate_infrastructure(self):
        """Validate infrastructure configuration"""
        logger.info("🏗️ Validating Infrastructure...")
        
        results = {
            "pulumi_configured": os.path.exists('Pulumi.yaml'),
            "deployment_framework": os.path.exists('orchestra_deployment_framework.py'),
            "docker_compose": os.path.exists('docker-compose.yml') or os.path.exists('docker-compose.weaviate-fix.yml'),
            "nginx_config": os.path.exists('nginx/'),
            "database_schema": os.path.exists('infrastructure/database_schema.sql')
        }
        
        # Check Pulumi configuration
        if results["pulumi_configured"]:
            try:
                with open('Pulumi.yaml', 'r') as f:
                    pulumi_config = f.read()
                    results["pulumi_runtime"] = 'runtime: python' in pulumi_config
            except:
                pass
        
        # Check for infrastructure validation
        if os.path.exists('infrastructure/infrastructure_validator.py'):
            results["infrastructure_validator"] = True
        
        self.validation_results['infrastructure'] = results
    
    def validate_code_quality(self):
        """Validate code quality metrics"""
        logger.info("📊 Validating Code Quality...")
        
        results = {
            "test_coverage": 0,
            "linting_issues": 0,
            "complexity_issues": 0,
            "documentation_coverage": 0
        }
        
        # Check test coverage from technical debt report
        debt_reports = [f for f in os.listdir('.') if f.startswith('technical_debt_report_')]
        if debt_reports:
            latest_report = sorted(debt_reports)[-1]
            with open(latest_report, 'r') as f:
                report = json.load(f)
            
            results["test_coverage"] = report.get('test_coverage', {}).get('percentage', 0)
            
            # Count high complexity methods
            high_complexity = [i for i in report.get('high_priority_issues', []) 
                             if i.get('type') == 'complex_method']
            results["complexity_issues"] = len(high_complexity)
        
        # Check for test files
        test_files = []
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(file)
        
        results["test_files_count"] = len(test_files)
        
        self.validation_results['code_quality'] = results
    
    def validate_deployment_config(self):
        """Validate deployment configuration"""
        logger.info("🚀 Validating Deployment Configuration...")
        
        results = {
            "ci_cd_configured": False,
            "deployment_scripts": [],
            "environment_configs": [],
            "secrets_management": False
        }
        
        # Check for deployment scripts
        deployment_scripts = [
            'deploy_to_lambda.py',
            'production_deploy.sh',
            'deploy_orchestrator_infrastructure.py',
            'orchestra_deployment_framework.py'
        ]
        
        for script in deployment_scripts:
            if os.path.exists(script):
                results["deployment_scripts"].append(script)
        
        # Check for CI/CD configuration
        ci_cd_files = ['.github/workflows/', '.gitlab-ci.yml', 'Jenkinsfile']
        for ci_file in ci_cd_files:
            if os.path.exists(ci_file):
                results["ci_cd_configured"] = True
                break
        
        # Check environment configurations
        env_files = ['.env.template', '.env.example', 'env.example']
        for env_file in env_files:
            if os.path.exists(env_file):
                results["environment_configs"].append(env_file)
        
        # Check secrets management
        if os.path.exists('.env.template') and not os.path.exists('.env'):
            results["secrets_management"] = True
        
        self.validation_results['deployment'] = results
    
    def validate_integrations(self):
        """Validate integration points"""
        logger.info("🔌 Validating Integrations...")
        
        results = {
            "mcp_server": os.path.exists('mcp_server/'),
            "weaviate_integration": False,
            "postgres_integration": False,
            "redis_integration": False,
            "api_endpoints": []
        }
        
        # Check for database integrations
        if os.path.exists('src/database/unified_database.py'):
            results["postgres_integration"] = True
        
        # Check for Weaviate service
        if os.path.exists('services/weaviate_service.py'):
            results["weaviate_integration"] = True
        
        # Check for Redis in requirements
        req_files = ['requirements.txt', 'requirements-app.txt']
        for req_file in req_files:
            if os.path.exists(req_file):
                with open(req_file, 'r') as f:
                    if 'redis' in f.read():
                        results["redis_integration"] = True
                        break
        
        # Check API endpoints
        if os.path.exists('src/api/main.py'):
            results["api_endpoints"].append('main_api')
        
        self.validation_results['integrations'] = results
    
    def establish_performance_baselines(self):
        """Establish performance baselines"""
        logger.info("⚡ Establishing Performance Baselines...")
        
        baselines = {
            "api_response_time_target": "< 200ms",
            "database_query_time_target": "< 50ms",
            "cache_hit_rate_target": "> 80%",
            "concurrent_users_target": 1000,
            "requests_per_second_target": 100
        }
        
        # Add recommendations based on architecture
        self.recommendations.append("Run load tests to validate performance targets")
        self.recommendations.append("Configure database connection pooling (min: 10, max: 100)")
        self.recommendations.append("Implement Redis caching for frequently accessed data")
        
        self.validation_results['performance_baselines'] = baselines
    
    def validate_monitoring(self):
        """Validate monitoring setup"""
        logger.info("📈 Validating Monitoring Setup...")
        
        results = {
            "logging_configured": False,
            "metrics_collection": False,
            "alerting_configured": False,
            "dashboards_defined": False
        }
        
        # Check for logging configuration
        if os.path.exists('mcp_server/utils/structured_logging.py'):
            results["logging_configured"] = True
        
        # Check for monitoring configuration in deployment
        if os.path.exists('orchestra_deployment_framework.py'):
            with open('orchestra_deployment_framework.py', 'r') as f:
                content = f.read()
                if 'prometheus' in content.lower():
                    results["metrics_collection"] = True
                if 'alertmanager' in content.lower():
                    results["alerting_configured"] = True
                if 'grafana' in content.lower():
                    results["dashboards_defined"] = True
        
        self.validation_results['monitoring'] = results
    
    def create_handoff_package(self) -> Dict[str, Any]:
        """Create comprehensive handoff package for debugging specialist"""
        logger.info("📦 Creating Handoff Package...")
        
        self.handoff_package = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": self.validation_results,
            "critical_issues": self.critical_issues,
            "recommendations": self.recommendations,
            "deployment_checklist": self._create_deployment_checklist(),
            "debugging_priorities": self._identify_debugging_priorities(),
            "test_scenarios": self._create_test_scenarios(),
            "rollback_procedures": self._define_rollback_procedures(),
            "monitoring_alerts": self._define_monitoring_alerts()
        }
        
        return self.handoff_package
    
    def _create_deployment_checklist(self) -> List[Dict[str, Any]]:
        """Create deployment checklist"""
        return [
            {
                "step": "Environment Setup",
                "tasks": [
                    "Create .env file from .env.template",
                    "Configure all required environment variables",
                    "Verify database credentials",
                    "Set up SSL certificates"
                ],
                "validation": "Run implementation_checklist.py"
            },
            {
                "step": "Database Initialization",
                "tasks": [
                    "Run database migrations",
                    "Create required schemas",
                    "Set up initial data",
                    "Configure connection pooling"
                ],
                "validation": "Test database connectivity"
            },
            {
                "step": "Service Deployment",
                "tasks": [
                    "Deploy PostgreSQL",
                    "Deploy Redis",
                    "Deploy Weaviate",
                    "Deploy API services",
                    "Deploy worker nodes"
                ],
                "validation": "Check service health endpoints"
            },
            {
                "step": "Security Configuration",
                "tasks": [
                    "Configure firewall rules",
                    "Set up SSL/TLS",
                    "Enable authentication",
                    "Configure CORS policies"
                ],
                "validation": "Run security scan"
            },
            {
                "step": "Monitoring Setup",
                "tasks": [
                    "Deploy Prometheus",
                    "Configure Grafana dashboards",
                    "Set up alerting rules",
                    "Configure log aggregation"
                ],
                "validation": "Verify metrics collection"
            }
        ]
    
    def _identify_debugging_priorities(self) -> List[Dict[str, str]]:
        """Identify debugging priorities"""
        priorities = []
        
        # Based on validation results
        if self.validation_results.get('security', {}).get('remaining_credentials', 0) > 0:
            priorities.append({
                "priority": "CRITICAL",
                "issue": "Remaining hardcoded credentials",
                "action": "Run critical_security_remediation.py and verify fixes"
            })
        
        if self.validation_results.get('code_quality', {}).get('test_coverage', 0) < 50:
            priorities.append({
                "priority": "HIGH",
                "issue": "Low test coverage",
                "action": "Add unit tests for critical components"
            })
        
        if not self.validation_results.get('infrastructure', {}).get('docker_compose'):
            priorities.append({
                "priority": "HIGH",
                "issue": "Missing Docker configuration",
                "action": "Create docker-compose.yml for local development"
            })
        
        return priorities
    
    def _create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create test scenarios for debugging"""
        return [
            {
                "scenario": "Database Connection Pool Exhaustion",
                "steps": [
                    "Simulate 100 concurrent database connections",
                    "Monitor connection pool metrics",
                    "Verify pool recovery after load"
                ],
                "expected_result": "Connections queued, no failures",
                "debugging_tools": ["pgAdmin", "connection pool stats"]
            },
            {
                "scenario": "API Rate Limiting",
                "steps": [
                    "Send 1000 requests/second to API",
                    "Verify rate limiting kicks in",
                    "Check response codes and headers"
                ],
                "expected_result": "429 status codes with retry headers",
                "debugging_tools": ["curl", "Apache Bench"]
            },
            {
                "scenario": "Memory Leak Detection",
                "steps": [
                    "Run application under load for 1 hour",
                    "Monitor memory usage",
                    "Check for growing memory consumption"
                ],
                "expected_result": "Stable memory usage",
                "debugging_tools": ["tracemalloc", "memory_profiler"]
            },
            {
                "scenario": "Failover Testing",
                "steps": [
                    "Simulate primary database failure",
                    "Verify automatic failover",
                    "Check data consistency"
                ],
                "expected_result": "Seamless failover with no data loss",
                "debugging_tools": ["pg_dump", "replication status"]
            }
        ]
    
    def _define_rollback_procedures(self) -> Dict[str, List[str]]:
        """Define rollback procedures"""
        return {
            "database_rollback": [
                "Stop all application services",
                "Backup current database state",
                "Restore from previous backup",
                "Run migration rollback scripts",
                "Verify data integrity",
                "Restart services"
            ],
            "application_rollback": [
                "Switch load balancer to previous deployment",
                "Stop current application instances",
                "Deploy previous version",
                "Run smoke tests",
                "Switch load balancer back"
            ],
            "infrastructure_rollback": [
                "Export current Pulumi state",
                "Revert to previous infrastructure code",
                "Run pulumi preview",
                "Apply previous infrastructure state",
                "Verify all resources"
            ]
        }
    
    def _define_monitoring_alerts(self) -> List[Dict[str, Any]]:
        """Define monitoring alerts"""
        return [
            {
                "alert": "High API Response Time",
                "condition": "avg(response_time) > 500ms for 5 minutes",
                "severity": "warning",
                "action": "Check database queries, scale API servers"
            },
            {
                "alert": "Database Connection Pool Exhaustion",
                "condition": "available_connections < 5",
                "severity": "critical",
                "action": "Increase pool size, check for connection leaks"
            },
            {
                "alert": "High Memory Usage",
                "condition": "memory_usage > 90%",
                "severity": "warning",
                "action": "Check for memory leaks, scale instances"
            },
            {
                "alert": "Failed Health Checks",
                "condition": "health_check_failures > 3",
                "severity": "critical",
                "action": "Check service logs, restart if necessary"
            }
        ]
    
    def generate_final_report(self):
        """Generate final validation report"""
        report = {
            "validation_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_checks": len(self.validation_results),
                "critical_issues": len(self.critical_issues),
                "recommendations": len(self.recommendations)
            },
            "validation_details": self.validation_results,
            "handoff_package": self.handoff_package,
            "next_steps": [
                "Address all critical issues before deployment",
                "",
                "Execute deployment using orchestra_deployment_framework.py",
                "Monitor deployment with provided alerts",
                "Use debugging priorities for troubleshooting"
            ]
        }
        
        # Save report
        report_file = f"implementation_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_file

def main():
    """Main execution"""
    print("🎯 Orchestra Implementation Validation & Handoff")
    print("=" * 50)
    
    validator = ImplementationValidator()
    
    # Run all validations
    print("\n🔍 Running Validations...")
    validation_results = validator.validate_all_components()
    
    # Create handoff package
    print("\n📦 Creating Handoff Package...")
    handoff_package = validator.create_handoff_package()
    
    # Generate final report
    print("\n📄 Generating Final Report...")
    report_file = validator.generate_final_report()
    
    # Print summary
    print("\n📊 Validation Summary:")
    print(f"  Total Validations: {len(validation_results)}")
    print(f"  Critical Issues: {len(validator.critical_issues)}")
    print(f"  Recommendations: {len(validator.recommendations)}")
    
    if validator.critical_issues:
        print("\n⚠️  Critical Issues Found:")
        for issue in validator.critical_issues:
            print(f"  - {issue}")
    
    print("\n💡 Top Recommendations:")
    for i, rec in enumerate(validator.recommendations[:5], 1):
        print(f"  {i}. {rec}")
    
    print(f"\n📄 Full report saved to: {report_file}")
    print("\n🚀 Ready for handoff to debugging specialist!")
    
    # Create quick reference script
    quick_ref = """#!/bin/bash
# Orchestra Quick Reference Commands

# Check system status
echo "=== System Status ==="
python3 implementation_checklist.py

# Run tests
echo "=== Running Tests ==="
python3 cleaned_reference

# Deploy infrastructure
echo "=== Deploy Infrastructure ==="
cd infrastructure && pulumi up

# Monitor logs
echo "=== Monitor Logs ==="
tail -f logs/orchestra.log

# Database console
echo "=== Database Console ==="
psql $DATABASE_URL
"""
    
    with open('orchestra_quick_reference.sh', 'w') as f:
        f.write(quick_ref)
    
    os.chmod('orchestra_quick_reference.sh', 0o755)
    print("\n✅ Created orchestra_quick_reference.sh for quick commands")

if __name__ == "__main__":
    main()