#!/usr/bin/env python3
"""
API Consistency Validator
Validates 100% API health and endpoint consistency.
"""

import os
import re
import json
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class APIConsistencyValidator:
    """Validates API consistency and health."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.validation_results = {}
        self.api_registry = {}
        self.health_score = 0
        
    def run_validation(self) -> Dict:
        """Run comprehensive API validation."""
        print("✅ Starting API Consistency Validation...")
        print("=" * 50)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_endpoints": 0,
            "valid_endpoints": 0,
            "invalid_endpoints": 0,
            "duplicate_endpoints": 0,
            "health_score": 0,
            "validation_details": {},
            "recommendations": []
        }
        
        # 1. Discover and catalog all endpoints
        print("🔍 1. Discovering API endpoints...")
        self._discover_api_endpoints()
        
        # 2. Validate endpoint definitions
        print("🔧 2. Validating endpoint definitions...")
        definition_results = self._validate_endpoint_definitions()
        
        # 3. Check for duplicates
        print("🔍 3. Checking for duplicate endpoints...")
        duplicate_results = self._check_duplicate_endpoints()
        
        # 4. Validate route patterns
        print("📋 4. Validating route patterns...")
        pattern_results = self._validate_route_patterns()
        
        # 5. Test endpoint accessibility (if server is running)
        print("🌐 5. Testing endpoint accessibility...")
        accessibility_results = self._test_endpoint_accessibility()
        
        # 6. Validate API documentation consistency
        print("📚 6. Validating documentation consistency...")
        doc_results = self._validate_documentation_consistency()
        
        # Compile final results
        results.update({
            "total_endpoints": len(self.api_registry),
            "duplicate_endpoints": duplicate_results["duplicates_found"],
            "validation_details": {
                "definitions": definition_results,
                "duplicates": duplicate_results,
                "patterns": pattern_results,
                "accessibility": accessibility_results,
                "documentation": doc_results
            }
        })
        
        # Calculate health score
        self._calculate_health_score(results)
        
        print(f"\n🎯 API VALIDATION COMPLETE")
        print(f"Total Endpoints: {results['total_endpoints']}")
        print(f"Health Score: {results['health_score']:.1f}%")
        print(f"Status: {'✅ HEALTHY' if results['health_score'] >= 95 else '⚠️ NEEDS ATTENTION' if results['health_score'] >= 80 else '❌ CRITICAL'}")
        
        return results
    
    def _discover_api_endpoints(self):
        """Discover all API endpoints in the codebase."""
        # Find API-related files
        python_files = list(self.root_path.glob("**/*.py"))
        api_files = [
            f for f in python_files
            if any(keyword in str(f).lower() for keyword in ['router', 'api', 'route', 'endpoint', 'main', 'app'])
            and not any(skip in str(f) for skip in ['__pycache__', '.git', 'venv', 'test_'])
        ]
        
        print(f"📡 Scanning {len(api_files)} API-related files...")
        
        for api_file in api_files:
            try:
                content = api_file.read_text(encoding='utf-8')
                endpoints = self._extract_api_endpoints(content, api_file)
                
                for endpoint in endpoints:
                    route_key = f"{endpoint['method']}:{endpoint['path']}"
                    
                    if route_key not in self.api_registry:
                        self.api_registry[route_key] = []
                    
                    self.api_registry[route_key].append({
                        'file': str(api_file),
                        'line': endpoint['line'],
                        'function': endpoint['function'],
                        'definition': endpoint['definition'],
                        'parameters': endpoint.get('parameters', []),
                        'return_type': endpoint.get('return_type', 'Any')
                    })
                    
            except Exception as e:
                logger.warning(f"Could not scan {api_file}: {e}")
    
    def _extract_api_endpoints(self, content: str, file_path: Path) -> List[Dict]:
        """Extract API endpoints from file content."""
        endpoints = []
        lines = content.split('\n')
        
        # Enhanced route patterns
        route_patterns = [
            # FastAPI patterns
            r'@router\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
            r'@app\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']',
            
            # Flask patterns
            r'@app\.route\s*\(\s*["\']([^"\']+)["\'].*methods\s*=\s*\[["\'](\w+)["\']',
            r'@blueprint\.route\s*\(\s*["\']([^"\']+)["\'].*methods\s*=\s*\[["\'](\w+)["\']',
            
            # APIRouter patterns
            r'router\.add_api_route\s*\(\s*["\']([^"\']+)["\'].*methods\s*=\s*\[["\'](\w+)["\']',
            
            # Include patterns
            r'app\.include_router\s*\(\s*(\w+).*prefix\s*=\s*["\']([^"\']+)["\']',
        ]
        
        for i, line in enumerate(lines):
            for pattern in route_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                
                for match in matches:
                    if len(match) == 2:
                        if 'methods' in pattern or pattern.startswith('@app.route'):
                            path, method = match
                        elif 'include_router' in pattern:
                            continue  # Handle router includes separately
                        else:
                            method, path = match
                        
                        # Find function details
                        function_info = self._analyze_function(lines, i)
                        
                        endpoints.append({
                            'method': method.upper(),
                            'path': path,
                            'line': i + 1,
                            'function': function_info['name'],
                            'definition': line.strip(),
                            'parameters': function_info['parameters'],
                            'return_type': function_info['return_type'],
                            'docstring': function_info['docstring']
                        })
        
        return endpoints
    
    def _analyze_function(self, lines: List[str], decorator_line: int) -> Dict:
        """Analyze function details following a decorator."""
        function_info = {
            'name': 'unknown_function',
            'parameters': [],
            'return_type': 'Any',
            'docstring': ''
        }
        
        # Find function definition
        for i in range(decorator_line + 1, min(len(lines), decorator_line + 10)):
            line = lines[i].strip()
            
            # Look for function definition
            func_match = re.match(r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:', line)
            if func_match:
                function_info['name'] = func_match.group(1)
                
                # Parse parameters
                params_str = func_match.group(2)
                if params_str:
                    params = [p.strip() for p in params_str.split(',') if p.strip() and p.strip() != 'self']
                    function_info['parameters'] = params
                
                # Parse return type
                if func_match.group(3):
                    function_info['return_type'] = func_match.group(3).strip()
                
                # Look for docstring
                for j in range(i + 1, min(len(lines), i + 5)):
                    doc_line = lines[j].strip()
                    if doc_line.startswith('"""') or doc_line.startswith("'''"):
                        function_info['docstring'] = doc_line
                        break
                
                break
        
        return function_info
    
    def _validate_endpoint_definitions(self) -> Dict:
        """Validate endpoint definitions for correctness."""
        validation = {
            "valid_definitions": 0,
            "invalid_definitions": 0,
            "issues": []
        }
        
        for route_key, implementations in self.api_registry.items():
            method, path = route_key.split(':', 1)
            
            for impl in implementations:
                issues = []
                
                # Validate path format
                if not path.startswith('/'):
                    issues.append("Path should start with '/'")
                
                # Validate path parameters
                path_params = re.findall(r'\{([^}]+)\}', path)
                func_params = [p.split(':')[0] for p in impl['parameters'] if ':' not in p or p.split(':')[0] != 'self']
                
                for path_param in path_params:
                    if path_param not in func_params:
                        issues.append(f"Path parameter '{path_param}' not in function parameters")
                
                # Validate HTTP method
                if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']:
                    issues.append(f"Invalid HTTP method: {method}")
                
                # Validate function naming
                if impl['function'] == 'unknown_function':
                    issues.append("Could not identify function name")
                
                # Check for docstring
                if not impl.get('docstring'):
                    issues.append("Missing function docstring")
                
                if issues:
                    validation["invalid_definitions"] += 1
                    validation["issues"].append({
                        "route": route_key,
                        "file": impl['file'],
                        "line": impl['line'],
                        "issues": issues
                    })
                else:
                    validation["valid_definitions"] += 1
        
        return validation
    
    def _check_duplicate_endpoints(self) -> Dict:
        """Check for duplicate endpoint definitions."""
        duplicates = {
            "duplicates_found": 0,
            "duplicate_routes": []
        }
        
        for route_key, implementations in self.api_registry.items():
            if len(implementations) > 1:
                duplicates["duplicates_found"] += 1
                duplicates["duplicate_routes"].append({
                    "route": route_key,
                    "count": len(implementations),
                    "locations": [
                        {"file": impl['file'], "line": impl['line']}
                        for impl in implementations
                    ]
                })
        
        return duplicates
    
    def _validate_route_patterns(self) -> Dict:
        """Validate route patterns follow RESTful conventions."""
        patterns = {
            "restful_routes": 0,
            "non_restful_routes": 0,
            "pattern_issues": []
        }
        
        restful_patterns = {
            'GET': [r'^/\w+$', r'^/\w+/\{[^}]+\}$'],  # Collections and resources
            'POST': [r'^/\w+$'],  # Create in collection
            'PUT': [r'^/\w+/\{[^}]+\}$'],  # Update resource
            'DELETE': [r'^/\w+/\{[^}]+\}$'],  # Delete resource
            'PATCH': [r'^/\w+/\{[^}]+\}$']  # Partial update
        }
        
        for route_key in self.api_registry.keys():
            method, path = route_key.split(':', 1)
            
            is_restful = False
            if method in restful_patterns:
                for pattern in restful_patterns[method]:
                    if re.match(pattern, path):
                        is_restful = True
                        break
            
            if is_restful:
                patterns["restful_routes"] += 1
            else:
                patterns["non_restful_routes"] += 1
                patterns["pattern_issues"].append({
                    "route": route_key,
                    "issue": f"{method} {path} doesn't follow RESTful conventions"
                })
        
        return patterns
    
    def _test_endpoint_accessibility(self) -> Dict:
        """Test if endpoints are accessible (if server is running)."""
        accessibility = {
            "server_running": False,
            "accessible_endpoints": 0,
            "inaccessible_endpoints": 0,
            "test_results": []
        }
        
        # Try to detect if a development server is running
        common_ports = [8000, 8080, 3000, 5000]
        server_url = None
        
        for port in common_ports:
            try:
                import urllib.request
                import urllib.error
                
                test_url = f"http://localhost:{port}/docs"  # FastAPI docs endpoint
                
                with urllib.request.urlopen(test_url, timeout=2) as response:
                    if response.status == 200:
                        server_url = f"http://localhost:{port}"
                        accessibility["server_running"] = True
                        break
            except Exception:
                continue
        
        if server_url:
            print(f"  🌐 Found server at {server_url}")
            
            # Test a few sample endpoints
            sample_routes = list(self.api_registry.keys())[:5]  # Test first 5 endpoints
            
            for route_key in sample_routes:
                method, path = route_key.split(':', 1)
                
                if method == 'GET':  # Only test GET endpoints for safety
                    test_url = f"{server_url}{path}"
                    
                    try:
                        # Replace path parameters with test values
                        test_path = re.sub(r'\{[^}]+\}', '1', path)
                        test_url = f"{server_url}{test_path}"
                        
                        req = urllib.request.Request(test_url, method='HEAD')
                        with urllib.request.urlopen(req, timeout=5) as response:
                            accessibility["accessible_endpoints"] += 1
                            accessibility["test_results"].append({
                                "route": route_key,
                                "status": "accessible",
                                "status_code": response.status
                            })
                    except Exception as e:
                        accessibility["inaccessible_endpoints"] += 1
                        accessibility["test_results"].append({
                            "route": route_key,
                            "status": "inaccessible",
                            "error": str(e)
                        })
        
        return accessibility
    
    def _validate_documentation_consistency(self) -> Dict:
        """Validate API documentation consistency."""
        documentation = {
            "documented_endpoints": 0,
            "undocumented_endpoints": 0,
            "documentation_issues": []
        }
        
        for route_key, implementations in self.api_registry.items():
            for impl in implementations:
                has_docstring = bool(impl.get('docstring'))
                
                if has_docstring:
                    documentation["documented_endpoints"] += 1
                else:
                    documentation["undocumented_endpoints"] += 1
                    documentation["documentation_issues"].append({
                        "route": route_key,
                        "file": impl['file'],
                        "function": impl['function'],
                        "issue": "Missing docstring"
                    })
        
        return documentation
    
    def _calculate_health_score(self, results: Dict):
        """Calculate overall API health score."""
        total_endpoints = results["total_endpoints"]
        
        if total_endpoints == 0:
            results["health_score"] = 100
            return
        
        # Scoring criteria
        definition_score = 0
        duplicate_score = 0
        pattern_score = 0
        doc_score = 0
        
        # Definition validity (40% weight)
        valid_defs = results["validation_details"]["definitions"]["valid_definitions"]
        if total_endpoints > 0:
            definition_score = (valid_defs / total_endpoints) * 40
        
        # No duplicates (30% weight)
        duplicates = results["duplicate_endpoints"]
        duplicate_score = max(0, 30 - (duplicates * 10))
        
        # RESTful patterns (20% weight)
        restful = results["validation_details"]["patterns"]["restful_routes"]
        if total_endpoints > 0:
            pattern_score = (restful / total_endpoints) * 20
        
        # Documentation (10% weight)
        documented = results["validation_details"]["documentation"]["documented_endpoints"]
        if total_endpoints > 0:
            doc_score = (documented / total_endpoints) * 10
        
        # Final score
        health_score = definition_score + duplicate_score + pattern_score + doc_score
        results["health_score"] = min(100, health_score)
        
        # Generate recommendations
        recommendations = []
        
        if duplicates > 0:
            recommendations.append("Eliminate duplicate endpoints")
        
        if results["validation_details"]["definitions"]["invalid_definitions"] > 0:
            recommendations.append("Fix endpoint definition issues")
        
        if results["validation_details"]["documentation"]["undocumented_endpoints"] > 0:
            recommendations.append("Add documentation to undocumented endpoints")
        
        if results["validation_details"]["patterns"]["non_restful_routes"] > total_endpoints * 0.5:
            recommendations.append("Consider adopting more RESTful route patterns")
        
        results["recommendations"] = recommendations
    
    def generate_validation_report(self) -> str:
        """Generate detailed validation report."""
        results = self.validation_results
        
        report = f"""
✅ API CONSISTENCY VALIDATION REPORT
===================================
Generated: {datetime.now().isoformat()}

📊 OVERALL HEALTH
----------------
Total Endpoints: {len(self.api_registry)}
Health Score: {self.health_score:.1f}%
Status: {'✅ HEALTHY' if self.health_score >= 95 else '⚠️ NEEDS ATTENTION' if self.health_score >= 80 else '❌ CRITICAL'}

📋 ENDPOINT REGISTRY
------------------
"""
        
        for route_key, implementations in self.api_registry.items():
            method, path = route_key.split(':', 1)
            report += f"\n{method:<7} {path}\n"
            
            for impl in implementations:
                file_name = Path(impl['file']).name
                report += f"        📁 {file_name}:{impl['line']} ({impl['function']})\n"
            
            if len(implementations) > 1:
                report += f"        ⚠️  DUPLICATE ({len(implementations)} implementations)\n"
        
        return report

def main():
    """Run the API consistency validation."""
    validator = APIConsistencyValidator(".")
    results = validator.run_validation()
    
    # Generate and display report
    validator.validation_results = results
    validator.health_score = results["health_score"]
    report = validator.generate_validation_report()
    print(report)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"api_validation_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save report
    report_file = f"API_VALIDATION_REPORT_{timestamp}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n📊 Results saved to: {results_file}")
    print(f"📄 Report saved to: {report_file}")
    
    # Return health status for pipeline
    if results["health_score"] >= 95:
        print("\n🎉 API is ready for production!")
        return 0
    else:
        print(f"\n⚠️  API needs improvement (Score: {results['health_score']:.1f}%)")
        return 1

if __name__ == "__main__":
    exit(main()) 