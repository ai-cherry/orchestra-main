#!/usr/bin/env python3
"""
Enhanced Mock Analyzer for EigenCode
Provides comprehensive code analysis capabilities when EigenCode is unavailable
"""

import os
import ast
import json
import time
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import re
import tokenize
import io

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai_components.orchestration.ai_orchestrator import DatabaseLogger, WeaviateManager


@dataclass
class FileMetrics:
    """Metrics for a single file"""
    path: str
    language: str
    lines_total: int = 0
    lines_code: int = 0
    lines_comment: int = 0
    lines_blank: int = 0
    complexity: int = 0
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    issues: List[Dict] = field(default_factory=list)


@dataclass
class ProjectMetrics:
    """Aggregated project metrics"""
    total_files: int = 0
    total_lines: int = 0
    total_code_lines: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    complexity_score: float = 0.0
    maintainability_index: float = 0.0
    test_coverage_estimate: float = 0.0
    security_score: float = 0.0
    performance_score: float = 0.0


class EnhancedMockAnalyzer:
    """Enhanced mock analyzer that mimics EigenCode functionality"""
    
    def __init__(self):
        self.db_logger = DatabaseLogger()
        self.weaviate_manager = WeaviateManager()
        self.language_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.m': 'matlab',
            '.jl': 'julia',
            '.lua': 'lua',
            '.pl': 'perl',
            '.sh': 'bash',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sql': 'sql',
            '.md': 'markdown'
        }
        
        # Performance optimization patterns
        self.performance_patterns = {
            'python': [
                (r'for\s+\w+\s+in\s+range\(len\(', 'Use enumerate() instead of range(len())'),
                (r'\.append\(\)\s+in\s+loop', 'Consider list comprehension for better performance'),
                (r'global\s+\w+', 'Avoid global variables for better performance'),
                (r'except\s*:', 'Avoid bare except clauses'),
                (r'eval\(|exec\(', 'Avoid eval/exec for security and performance')
            ],
            'javascript': [
                (r'document\.querySelector.*\s+in\s+loop', 'Cache DOM queries outside loops'),
                (r'\.forEach\(', 'Consider for...of for better performance'),
                (r'new\s+Date\(\)\.getTime\(\)', 'Use Date.now() instead'),
                (r'setTimeout.*,\s*0\)', 'Consider requestAnimationFrame for UI updates')
            ]
        }
        
        # Security patterns
        self.security_patterns = {
            'python': [
                (r'pickle\.load', 'Pickle can execute arbitrary code'),
                (r'os\.system\(|subprocess\.call\(.*shell=True', 'Command injection risk'),
                (r'sql.*%s|sql.*\+', 'Potential SQL injection'),
                (r'hashlib\.md5\(|hashlib\.sha1\(', 'Weak hashing algorithm')
            ],
            'javascript': [
                (r'innerHTML\s*=', 'XSS vulnerability risk'),
                (r'eval\(', 'Code injection risk'),
                (r'document\.write\(', 'Security and performance risk')
            ]
        }
    
    async def analyze_codebase(self, codebase_path: str, options: Dict = None) -> Dict:
        """Analyze codebase with EigenCode-like functionality"""
        start_time = time.time()
        
        # Default options
        options = options or {}
        depth = options.get('depth', 'comprehensive')
        include_metrics = options.get('include_metrics', True)
        include_suggestions = options.get('include_suggestions', True)
        
        # Initialize results
        results = {
            'status': 'completed',
            'analyzer': 'mock_eigencode_enhanced',
            'timestamp': datetime.now().isoformat(),
            'codebase_path': codebase_path,
            'analysis_options': options,
            'summary': {},
            'files': [],
            'metrics': ProjectMetrics(),
            'issues': [],
            'suggestions': [],
            'dependencies': {},
            'architecture': {}
        }
        
        # Analyze files
        path = Path(codebase_path)
        if path.is_file():
            file_metrics = await self._analyze_file(path)
            results['files'].append(file_metrics.__dict__)
        else:
            for file_path in self._get_files_to_analyze(path):
                try:
                    file_metrics = await self._analyze_file(file_path)
                    results['files'].append(file_metrics.__dict__)
                    
                    # Update project metrics
                    self._update_project_metrics(results['metrics'], file_metrics)
                    
                except Exception as e:
                    results['issues'].append({
                        'file': str(file_path),
                        'type': 'analysis_error',
                        'message': str(e)
                    })
        
        # Calculate aggregate metrics
        if include_metrics:
            results['metrics'] = self._calculate_aggregate_metrics(results)
        
        # Generate suggestions
        if include_suggestions:
            results['suggestions'] = self._generate_suggestions(results)
        
        # Analyze dependencies
        results['dependencies'] = await self._analyze_dependencies(codebase_path)
        
        # Analyze architecture
        if depth == 'comprehensive':
            results['architecture'] = await self._analyze_architecture(codebase_path, results)
        
        # Calculate summary
        results['summary'] = {
            'total_files': len(results['files']),
            'total_lines': results['metrics'].total_lines,
            'languages': results['metrics'].languages,
            'analysis_time': time.time() - start_time,
            'issues_found': len(results['issues']),
            'complexity_score': results['metrics'].complexity_score,
            'maintainability_index': results['metrics'].maintainability_index
        }
        
        # Log analysis
        self.db_logger.log_action(
            workflow_id="mock_eigencode_analysis",
            task_id=f"analysis_{int(time.time())}",
            agent_role="analyzer",
            action="codebase_analysis",
            status="completed",
            metadata=results['summary']
        )
        
        # Store in Weaviate
        self.weaviate_manager.store_context(
            workflow_id="mock_eigencode_analysis",
            task_id=f"analysis_{hashlib.md5(codebase_path.encode()).hexdigest()}",
            context_type="code_analysis",
            content=json.dumps(results),
            metadata={
                'timestamp': results['timestamp'],
                'codebase_path': codebase_path,
                'total_files': results['summary']['total_files']
            }
        )
        
        return results
    
    def _get_files_to_analyze(self, path: Path) -> List[Path]:
        """Get list of files to analyze"""
        files = []
        ignore_patterns = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
        
        for item in path.rglob('*'):
            if item.is_file():
                # Skip if in ignored directory
                if any(ignored in item.parts for ignored in ignore_patterns):
                    continue
                
                # Skip binary files
                if item.suffix in self.language_extensions:
                    files.append(item)
        
        return files
    
    async def _analyze_file(self, file_path: Path) -> FileMetrics:
        """Analyze a single file"""
        metrics = FileMetrics(
            path=str(file_path),
            language=self.language_extensions.get(file_path.suffix, 'unknown')
        )
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Count lines
            for line in lines:
                metrics.lines_total += 1
                stripped = line.strip()
                
                if not stripped:
                    metrics.lines_blank += 1
                elif self._is_comment(stripped, metrics.language):
                    metrics.lines_comment += 1
                else:
                    metrics.lines_code += 1
            
            # Language-specific analysis
            if metrics.language == 'python':
                await self._analyze_python_file(file_path, content, metrics)
            elif metrics.language in ['javascript', 'typescript']:
                await self._analyze_javascript_file(file_path, content, metrics)
            
            # Check for performance issues
            self._check_performance_issues(content, metrics)
            
            # Check for security issues
            self._check_security_issues(content, metrics)
            
        except Exception as e:
            metrics.issues.append({
                'type': 'file_error',
                'severity': 'error',
                'message': str(e)
            })
        
        return metrics
    
    def _is_comment(self, line: str, language: str) -> bool:
        """Check if line is a comment"""
        comment_markers = {
            'python': ['#'],
            'javascript': ['//', '/*', '*/', '*'],
            'typescript': ['//', '/*', '*/', '*'],
            'java': ['//', '/*', '*/', '*'],
            'cpp': ['//', '/*', '*/', '*'],
            'c': ['//', '/*', '*/', '*'],
            'go': ['//', '/*', '*/', '*'],
            'rust': ['//', '/*', '*/', '*'],
            'ruby': ['#'],
            'php': ['//', '/*', '*/', '*', '#'],
            'bash': ['#'],
            'yaml': ['#'],
            'sql': ['--', '/*', '*/', '*']
        }
        
        markers = comment_markers.get(language, ['#', '//'])
        return any(line.startswith(marker) for marker in markers)
    
    async def _analyze_python_file(self, file_path: Path, content: str, metrics: FileMetrics):
        """Analyze Python file using AST"""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    metrics.functions.append(node.name)
                    metrics.complexity += self._calculate_complexity(node)
                elif isinstance(node, ast.ClassDef):
                    metrics.classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            metrics.imports.append(alias.name)
                    else:
                        metrics.imports.append(node.module or '')
            
            # Check for code quality issues
            if len(metrics.functions) > 20:
                metrics.issues.append({
                    'type': 'complexity',
                    'severity': 'warning',
                    'message': f'File has {len(metrics.functions)} functions, consider splitting'
                })
            
        except SyntaxError as e:
            metrics.issues.append({
                'type': 'syntax_error',
                'severity': 'error',
                'line': e.lineno,
                'message': str(e)
            })
    
    async def _analyze_javascript_file(self, file_path: Path, content: str, metrics: FileMetrics):
        """Analyze JavaScript/TypeScript file"""
        # Simple regex-based analysis
        function_pattern = r'function\s+(\w+)|(\w+)\s*:\s*function|(\w+)\s*=\s*\([^)]*\)\s*=>'
        class_pattern = r'class\s+(\w+)'
        import_pattern = r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]'
        
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1) or match.group(2) or match.group(3)
            if func_name:
                metrics.functions.append(func_name)
        
        for match in re.finditer(class_pattern, content):
            metrics.classes.append(match.group(1))
        
        for match in re.finditer(import_pattern, content):
            metrics.imports.append(match.group(1))
        
        # Estimate complexity
        metrics.complexity = len(metrics.functions) + len(metrics.classes)
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for Python AST node"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _check_performance_issues(self, content: str, metrics: FileMetrics):
        """Check for performance issues"""
        patterns = self.performance_patterns.get(metrics.language, [])
        
        for pattern, message in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                metrics.issues.append({
                    'type': 'performance',
                    'severity': 'warning',
                    'message': message
                })
    
    def _check_security_issues(self, content: str, metrics: FileMetrics):
        """Check for security issues"""
        patterns = self.security_patterns.get(metrics.language, [])
        
        for pattern, message in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                metrics.issues.append({
                    'type': 'security',
                    'severity': 'high',
                    'message': message
                })
    
    def _update_project_metrics(self, project_metrics: ProjectMetrics, file_metrics: FileMetrics):
        """Update project metrics with file metrics"""
        project_metrics.total_files += 1
        project_metrics.total_lines += file_metrics.lines_total
        project_metrics.total_code_lines += file_metrics.lines_code
        
        # Update language distribution
        if file_metrics.language not in project_metrics.languages:
            project_metrics.languages[file_metrics.language] = 0
        project_metrics.languages[file_metrics.language] += 1
        
        # Update complexity
        project_metrics.complexity_score += file_metrics.complexity
    
    def _calculate_aggregate_metrics(self, results: Dict) -> Dict:
        """Calculate aggregate metrics"""
        metrics = results['metrics']
        
        # Calculate average complexity
        if metrics.total_files > 0:
            metrics.complexity_score = metrics.complexity_score / metrics.total_files
        
        # Calculate maintainability index (simplified)
        # Based on Halstead volume, cyclomatic complexity, and lines of code
        if metrics.total_code_lines > 0:
            volume = metrics.total_code_lines * 2.0  # Simplified Halstead volume
            maintainability = 171 - 5.2 * (volume / 1000) - 0.23 * metrics.complexity_score
            metrics.maintainability_index = max(0, min(100, maintainability))
        
        # Estimate test coverage (based on test file presence)
        test_files = sum(1 for f in results['files'] if 'test' in f['path'].lower())
        if metrics.total_files > 0:
            metrics.test_coverage_estimate = (test_files / metrics.total_files) * 100
        
        # Calculate security score
        security_issues = sum(1 for f in results['files'] 
                            for i in f.get('issues', []) 
                            if i['type'] == 'security')
        metrics.security_score = max(0, 100 - (security_issues * 10))
        
        # Calculate performance score
        perf_issues = sum(1 for f in results['files'] 
                         for i in f.get('issues', []) 
                         if i['type'] == 'performance')
        metrics.performance_score = max(0, 100 - (perf_issues * 5))
        
        return metrics.__dict__
    
    def _generate_suggestions(self, results: Dict) -> List[Dict]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Complexity suggestions
        if results['metrics']['complexity_score'] > 10:
            suggestions.append({
                'category': 'complexity',
                'priority': 'high',
                'message': 'High average complexity detected. Consider refactoring complex functions.',
                'files_affected': [f['path'] for f in results['files'] if f.get('complexity', 0) > 15]
            })
        
        # Maintainability suggestions
        if results['metrics']['maintainability_index'] < 50:
            suggestions.append({
                'category': 'maintainability',
                'priority': 'high',
                'message': 'Low maintainability index. Focus on reducing complexity and improving code organization.'
            })
        
        # Test coverage suggestions
        if results['metrics']['test_coverage_estimate'] < 30:
            suggestions.append({
                'category': 'testing',
                'priority': 'medium',
                'message': 'Low test coverage estimate. Consider adding more unit tests.'
            })
        
        # Security suggestions
        security_issues = [i for f in results['files'] for i in f.get('issues', []) if i['type'] == 'security']
        if security_issues:
            suggestions.append({
                'category': 'security',
                'priority': 'critical',
                'message': f'Found {len(security_issues)} security issues that need immediate attention.',
                'issues': security_issues[:5]  # Top 5 issues
            })
        
        # Performance suggestions
        perf_issues = [i for f in results['files'] for i in f.get('issues', []) if i['type'] == 'performance']
        if perf_issues:
            suggestions.append({
                'category': 'performance',
                'priority': 'medium',
                'message': f'Found {len(perf_issues)} performance optimization opportunities.',
                'issues': perf_issues[:5]  # Top 5 issues
            })
        
        return suggestions
    
    async def _analyze_dependencies(self, codebase_path: str) -> Dict:
        """Analyze project dependencies"""
        dependencies = {
            'languages': {},
            'packages': {},
            'vulnerabilities': []
        }
        
        path = Path(codebase_path)
        
        # Python dependencies
        requirements_files = list(path.glob('**/requirements*.txt')) + list(path.glob('**/Pipfile'))
        if requirements_files:
            dependencies['languages']['python'] = {
                'files': [str(f) for f in requirements_files],
                'packages': self._parse_requirements(requirements_files[0])
            }
        
        # JavaScript/Node dependencies
        package_files = list(path.glob('**/package.json'))
        if package_files:
            dependencies['languages']['javascript'] = {
                'files': [str(f) for f in package_files],
                'packages': self._parse_package_json(package_files[0])
            }
        
        # Check for known vulnerabilities (simplified)
        vulnerable_packages = {
            'python': ['pickle', 'eval', 'exec'],
            'javascript': ['eval', 'child_process']
        }
        
        for lang, packages in dependencies['languages'].items():
            for pkg in packages.get('packages', []):
                if any(vuln in pkg.lower() for vuln in vulnerable_packages.get(lang, [])):
                    dependencies['vulnerabilities'].append({
                        'language': lang,
                        'package': pkg,
                        'severity': 'high',
                        'message': f'Potentially vulnerable package: {pkg}'
                    })
        
        return dependencies
    
    def _parse_requirements(self, requirements_file: Path) -> List[str]:
        """Parse Python requirements file"""
        packages = []
        try:
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extract package name
                        pkg = re.split('[<>=!]', line)[0].strip()
                        if pkg:
                            packages.append(pkg)
        except:
            pass
        return packages
    
    def _parse_package_json(self, package_file: Path) -> List[str]:
        """Parse package.json file"""
        packages = []
        try:
            with open(package_file, 'r') as f:
                data = json.load(f)
                packages.extend(data.get('dependencies', {}).keys())
                packages.extend(data.get('devDependencies', {}).keys())
        except:
            pass
        return packages
    
    async def _analyze_architecture(self, codebase_path: str, results: Dict) -> Dict:
        """Analyze project architecture"""
        architecture = {
            'structure': {},
            'patterns': [],
            'recommendations': []
        }
        
        # Analyze directory structure
        path = Path(codebase_path)
        structure = {}
        
        for item in path.rglob('*'):
            if item.is_dir() and not any(ignored in str(item) for ignored in ['.git', '__pycache__', 'node_modules']):
                rel_path = item.relative_to(path)
                parts = rel_path.parts
                
                current = structure
                for part in parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
        
        architecture['structure'] = structure
        
        # Detect common patterns
        if 'src' in structure or 'lib' in structure:
            architecture['patterns'].append('Standard source directory structure')
        
        if 'tests' in structure or 'test' in structure:
            architecture['patterns'].append('Test directory present')
        
        if 'docs' in structure or 'documentation' in structure:
            architecture['patterns'].append('Documentation directory present')
        
        # Architecture recommendations
        if 'tests' not in structure and 'test' not in structure:
            architecture['recommendations'].append({
                'category': 'testing',
                'message': 'Consider adding a dedicated test directory'
            })
        
        if results['metrics']['total_files'] > 50 and 'src' not in structure:
            architecture['recommendations'].append({
                'category': 'organization',
                'message': 'Consider organizing code in a src/ directory for better structure'
            })
        
        return architecture


# Singleton instance
_mock_analyzer_instance = None

def get_mock_analyzer() -> EnhancedMockAnalyzer:
    """Get singleton instance of mock analyzer"""
    global _mock_analyzer_instance
    if _mock_analyzer_instance is None:
        _mock_analyzer_instance = EnhancedMockAnalyzer()
    return _mock_analyzer_instance


async def main():
    """Test the mock analyzer"""
    analyzer = get_mock_analyzer()
    
    # Test analysis
    results = await analyzer.analyze_codebase(
        "/root/orchestra-main",
        {
            "depth": "comprehensive",
            "include_metrics": True,
            "include_suggestions": True
        }
    )
    
    # Save results
    with open("mock_analysis_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analysis complete!")
    print(f"Total files: {results['summary']['total_files']}")
    print(f"Total lines: {results['summary']['total_lines']}")
    print(f"Languages: {results['summary']['languages']}")
    print(f"Complexity score: {results['summary']['complexity_score']:.2f}")
    print(f"Maintainability index: {results['summary']['maintainability_index']:.2f}")
    print(f"Issues found: {results['summary']['issues_found']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())