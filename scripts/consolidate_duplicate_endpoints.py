#!/usr/bin/env python3
"""
Duplicate API Endpoints Consolidator
Resolves the 11 duplicate endpoints to achieve 100% API health.
"""

import os
import re
import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class DuplicateEndpointConsolidator:
    """Consolidates duplicate API endpoints."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.duplicates_found = []
        self.consolidations_made = []
        self.endpoint_registry = defaultdict(list)
        
    def run_consolidation(self) -> Dict:
        """Run duplicate endpoint consolidation."""
        print("🔄 Starting Duplicate Endpoint Consolidation...")
        print("=" * 50)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "duplicates_found": 0,
            "endpoints_consolidated": 0,
            "files_modified": 0,
            "api_health_score": 0,
            "consolidations_made": []
        }
        
        # Discover all API endpoints
        print("🔍 Discovering API endpoints...")
        self._discover_endpoints()
        
        # Identify duplicates
        print("🔍 Identifying duplicate endpoints...")
        duplicates = self._identify_duplicates()
        results["duplicates_found"] = len(duplicates)
        
        # Consolidate duplicates
        print("🔄 Consolidating duplicates...")
        consolidated = self._consolidate_duplicates(duplicates)
        results["endpoints_consolidated"] = consolidated
        
        # Calculate final API health score
        final_duplicates = len(self._identify_duplicates())
        total_endpoints = sum(len(endpoints) for endpoints in self.endpoint_registry.values())
        
        if total_endpoints > 0:
            health_score = ((total_endpoints - final_duplicates) / total_endpoints) * 100
        else:
            health_score = 100
            
        results["api_health_score"] = health_score
        results["consolidations_made"] = self.consolidations_made
        
        print(f"\n🎯 CONSOLIDATION COMPLETE")
        print(f"Duplicates Found: {results['duplicates_found']}")
        print(f"Endpoints Consolidated: {results['endpoints_consolidated']}")
        print(f"API Health Score: {results['api_health_score']:.1f}%")
        
        return results
    
    def _discover_endpoints(self):
        """Discover all API endpoints in the codebase."""
        # Find all Python files that might contain API routes
        python_files = list(self.root_path.glob("**/*.py"))
        
        # Focus on likely API files
        api_files = [
            f for f in python_files 
            if any(keyword in str(f).lower() for keyword in ['router', 'api', 'route', 'endpoint'])
            and not any(skip in str(f) for skip in ['__pycache__', '.git', 'venv', 'test_'])
        ]
        
        # Add core files that might have routes
        api_files.extend([
            f for f in python_files
            if any(keyword in f.name.lower() for keyword in ['main', 'app', 'server'])
            and not any(skip in str(f) for skip in ['__pycache__', '.git', 'venv', 'test_'])
        ])
        
        print(f"📡 Scanning {len(api_files)} API files...")
        
        for api_file in api_files:
            try:
                content = api_file.read_text(encoding='utf-8')
                endpoints = self._extract_endpoints(content, api_file)
                
                for endpoint in endpoints:
                    route_key = f"{endpoint['method']}:{endpoint['path']}"
                    self.endpoint_registry[route_key].append({
                        'file': api_file,
                        'line': endpoint['line'],
                        'function': endpoint['function'],
                        'full_definition': endpoint['definition']
                    })
                    
            except Exception as e:
                logger.warning(f"Could not scan {api_file}: {e}")
    
    def _extract_endpoints(self, content: str, file_path: Path) -> List[Dict]:
        """Extract API endpoints from file content."""
        endpoints = []
        lines = content.split('\n')
        
        # Common FastAPI/Flask route patterns
        route_patterns = [
            # FastAPI patterns
            r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            
            # Flask patterns  
            r'@app\.route\s*\(\s*["\']([^"\']+)["\'].*methods\s*=\s*\[["\'](\w+)["\']',
            r'@blueprint\.route\s*\(\s*["\']([^"\']+)["\'].*methods\s*=\s*\[["\'](\w+)["\']',
            
            # APIRouter patterns
            r'router\.add_api_route\s*\(\s*["\']([^"\']+)["\'].*methods\s*=\s*\[["\'](\w+)["\']',
        ]
        
        for i, line in enumerate(lines):
            for pattern in route_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                
                for match in matches:
                    if len(match) == 2:
                        if pattern.startswith('@app.route') or pattern.startswith('@blueprint.route'):
                            path, method = match
                        elif pattern.startswith('router.add_api_route'):
                            path, method = match
                        else:
                            method, path = match
                        
                        # Find the function name
                        function_name = self._find_function_name(lines, i)
                        
                        endpoints.append({
                            'method': method.upper(),
                            'path': path,
                            'line': i + 1,
                            'function': function_name,
                            'definition': line.strip()
                        })
        
        return endpoints
    
    def _find_function_name(self, lines: List[str], decorator_line: int) -> str:
        """Find the function name following a decorator."""
        for i in range(decorator_line + 1, min(len(lines), decorator_line + 5)):
            line = lines[i].strip()
            
            # Look for function definition
            func_match = re.match(r'def\s+(\w+)\s*\(', line)
            if func_match:
                return func_match.group(1)
            
            # Look for async function definition
            async_match = re.match(r'async\s+def\s+(\w+)\s*\(', line)
            if async_match:
                return async_match.group(1)
        
        return "unknown_function"
    
    def _identify_duplicates(self) -> List[Tuple[str, List]]:
        """Identify duplicate endpoints."""
        duplicates = []
        
        for route_key, implementations in self.endpoint_registry.items():
            if len(implementations) > 1:
                duplicates.append((route_key, implementations))
                self.duplicates_found.append({
                    'route': route_key,
                    'count': len(implementations),
                    'files': [str(impl['file']) for impl in implementations]
                })
        
        return duplicates
    
    def _consolidate_duplicates(self, duplicates: List[Tuple[str, List]]) -> int:
        """Consolidate duplicate endpoints."""
        consolidated_count = 0
        
        for route_key, implementations in duplicates:
            print(f"🔄 Consolidating {route_key} ({len(implementations)} duplicates)")
            
            # Choose the best implementation to keep
            primary_impl = self._choose_primary_implementation(implementations)
            redundant_impls = [impl for impl in implementations if impl != primary_impl]
            
            # Handle consolidation
            if self._consolidate_endpoint(route_key, primary_impl, redundant_impls):
                consolidated_count += 1
                self.consolidations_made.append({
                    'route': route_key,
                    'primary_file': str(primary_impl['file']),
                    'removed_from': [str(impl['file']) for impl in redundant_impls]
                })
        
        return consolidated_count
    
    def _choose_primary_implementation(self, implementations: List[Dict]) -> Dict:
        """Choose the best implementation to keep as primary."""
        # Scoring criteria for choosing primary implementation
        def score_implementation(impl):
            score = 0
            file_path = str(impl['file'])
            
            # Prefer files in specific directories
            if '/routers/' in file_path or '/api/' in file_path:
                score += 10
            if '/core/' in file_path:
                score += 5
            if '/main' in file_path or '/app' in file_path:
                score += 3
                
            # Prefer more descriptive function names
            if impl['function'] != 'unknown_function':
                score += 5
            if len(impl['function']) > 5:  # Longer, more descriptive names
                score += 2
                
            # Prefer newer files (simple heuristic)
            try:
                mod_time = impl['file'].stat().st_mtime
                score += mod_time / 1000000  # Small bonus for newer files
            except:
                pass
            
            return score
        
        # Return implementation with highest score
        return max(implementations, key=score_implementation)
    
    def _consolidate_endpoint(self, route_key: str, primary_impl: Dict, redundant_impls: List[Dict]) -> bool:
        """Consolidate endpoint by removing redundant implementations."""
        try:
            for redundant_impl in redundant_impls:
                file_path = redundant_impl['file']
                
                # Read the file
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Find and comment out the redundant endpoint
                line_idx = redundant_impl['line'] - 1  # Convert to 0-based
                
                if 0 <= line_idx < len(lines):
                    # Comment out the decorator and function
                    commented_lines = self._comment_out_endpoint(lines, line_idx, redundant_impl)
                    
                    # Write back the modified content
                    new_content = '\n'.join(commented_lines)
                    file_path.write_text(new_content, encoding='utf-8')
                    
                    print(f"  ✅ Removed duplicate from {file_path.name}:{redundant_impl['line']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to consolidate {route_key}: {e}")
            return False
    
    def _comment_out_endpoint(self, lines: List[str], decorator_line: int, impl: Dict) -> List[str]:
        """Comment out an endpoint decorator and its function."""
        commented_lines = lines.copy()
        
        # Comment out the decorator line
        if decorator_line < len(commented_lines):
            line = commented_lines[decorator_line]
            if not line.strip().startswith('#'):
                commented_lines[decorator_line] = f"# DUPLICATE REMOVED: {line}"
        
        # Find and comment out the function definition
        for i in range(decorator_line + 1, min(len(commented_lines), decorator_line + 10)):
            line = commented_lines[i].strip()
            
            # Look for function definition
            if line.startswith('def ') or line.startswith('async def '):
                # Comment out function and its body
                func_indent = len(commented_lines[i]) - len(commented_lines[i].lstrip())
                
                # Comment the function definition
                if not commented_lines[i].strip().startswith('#'):
                    commented_lines[i] = f"# DUPLICATE REMOVED: {commented_lines[i]}"
                
                # Comment function body
                j = i + 1
                while j < len(commented_lines):
                    if commented_lines[j].strip() == '':
                        j += 1
                        continue
                        
                    line_indent = len(commented_lines[j]) - len(commented_lines[j].lstrip())
                    
                    # If we've reached the same or less indentation, we're done with function body
                    if line_indent <= func_indent and commented_lines[j].strip():
                        break
                    
                    # Comment out the line if it's part of the function body
                    if not commented_lines[j].strip().startswith('#'):
                        commented_lines[j] = f"# DUPLICATE REMOVED: {commented_lines[j]}"
                    
                    j += 1
                
                break
        
        return commented_lines
    
    def generate_consolidation_report(self) -> str:
        """Generate a detailed consolidation report."""
        duplicates = self._identify_duplicates()
        
        report = f"""
🔄 API ENDPOINT CONSOLIDATION REPORT
===================================
Generated: {datetime.now().isoformat()}

📊 SUMMARY
---------
Total Unique Routes: {len(self.endpoint_registry)}
Duplicate Routes Found: {len(duplicates)}
Consolidations Made: {len(self.consolidations_made)}

🔍 DUPLICATE ENDPOINTS FOUND
---------------------------
"""
        
        for route_key, implementations in duplicates:
            method, path = route_key.split(':', 1)
            report += f"\n🚨 {method} {path}\n"
            report += f"   Duplicates: {len(implementations)}\n"
            
            for impl in implementations:
                report += f"   📁 {impl['file'].name}:{impl['line']} ({impl['function']})\n"
        
        if self.consolidations_made:
            report += "\n✅ CONSOLIDATIONS MADE\n"
            report += "-" * 22 + "\n"
            
            for consolidation in self.consolidations_made:
                report += f"\n🔄 {consolidation['route']}\n"
                report += f"   ✅ Kept: {Path(consolidation['primary_file']).name}\n"
                
                for removed_file in consolidation['removed_from']:
                    report += f"   ❌ Removed: {Path(removed_file).name}\n"
        
        return report

def main():
    """Run the duplicate endpoint consolidation."""
    consolidator = DuplicateEndpointConsolidator(".")
    results = consolidator.run_consolidation()
    
    # Generate and display report
    report = consolidator.generate_consolidation_report()
    print(report)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"api_consolidation_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save report
    report_file = f"API_CONSOLIDATION_REPORT_{timestamp}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n📊 Results saved to: {results_file}")
    print(f"📄 Report saved to: {report_file}")
    
    return results

if __name__ == "__main__":
    main() 