#!/usr/bin/env python3
"""
🔍 Enhanced Code Intelligence Server for Cursor AI Integration
Real-time code analysis, complexity detection, and quality feedback
"""

import asyncio
import ast
import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import subprocess
import re

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CodeAnalysis:
    """Code analysis result"""
    file_path: str
    complexity: int
    quality_score: float
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    metrics: Dict[str, Any]
    persona_insights: Dict[str, str]

class CodeComplexityAnalyzer:
    """Analyze code complexity and quality"""
    
    def __init__(self):
        self.complexity_threshold = 10
        self.quality_weights = {
            'complexity': 0.3,
            'documentation': 0.2,
            'naming': 0.2,
            'structure': 0.3
        }
    
    def analyze_file(self, file_path: str) -> CodeAnalysis:
        """Analyze a Python file for complexity and quality"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            # Calculate metrics
            complexity = self._calculate_complexity(tree)
            documentation_score = self._analyze_documentation(tree, source_code)
            naming_score = self._analyze_naming(tree)
            structure_score = self._analyze_structure(tree)
            
            # Calculate overall quality score
            quality_score = (
                (10 - min(complexity, 10)) / 10 * self.quality_weights['complexity'] +
                documentation_score * self.quality_weights['documentation'] +
                naming_score * self.quality_weights['naming'] +
                structure_score * self.quality_weights['structure']
            )
            
            # Generate issues and suggestions
            issues = self._identify_issues(tree, source_code, complexity)
            suggestions = self._generate_suggestions(complexity, documentation_score, naming_score)
            
            # Get persona insights
            persona_insights = self._get_persona_insights(file_path, complexity, quality_score)
            
            metrics = {
                'complexity': complexity,
                'lines_of_code': len(source_code.split('\n')),
                'functions': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                'classes': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                'documentation_score': documentation_score,
                'naming_score': naming_score,
                'structure_score': structure_score
            }
            
            return CodeAnalysis(
                file_path=file_path,
                complexity=complexity,
                quality_score=quality_score,
                issues=issues,
                suggestions=suggestions,
                metrics=metrics,
                persona_insights=persona_insights
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return CodeAnalysis(
                file_path=file_path,
                complexity=0,
                quality_score=0.0,
                issues=[{"type": "error", "message": f"Analysis failed: {str(e)}"}],
                suggestions=[],
                metrics={},
                persona_insights={}
            )
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
            elif isinstance(node, (ast.BoolOp, ast.Compare)):
                complexity += len(node.ops) if hasattr(node, 'ops') else 1
        
        return complexity
    
    def _analyze_documentation(self, tree: ast.AST, source_code: str) -> float:
        """Analyze documentation quality (0-1 score)"""
        docstring_nodes = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Str)):
                    docstring_nodes.append(node)
        
        # Count total functions and classes
        total_nodes = len([n for n in ast.walk(tree) 
                          if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))])
        
        if total_nodes == 0:
            return 1.0
        
        # Documentation coverage
        coverage = len(docstring_nodes) / total_nodes
        
        # Check for comments
        comment_lines = len([line for line in source_code.split('\n') if line.strip().startswith('#')])
        total_lines = len(source_code.split('\n'))
        comment_ratio = comment_lines / max(total_lines, 1)
        
        return min(coverage + comment_ratio * 0.5, 1.0)
    
    def _analyze_naming(self, tree: ast.AST) -> float:
        """Analyze naming conventions (0-1 score)"""
        naming_score = 1.0
        issues = 0
        total_names = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_names += 1
                if not self._is_snake_case(node.name):
                    issues += 1
            elif isinstance(node, ast.ClassDef):
                total_names += 1
                if not self._is_pascal_case(node.name):
                    issues += 1
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    total_names += 1
                    if len(node.id) < 2 or (node.id.isupper() and len(node.id) > 1):
                        continue  # Skip constants and single chars
                    if not self._is_snake_case(node.id):
                        issues += 1
        
        if total_names > 0:
            naming_score = 1.0 - (issues / total_names)
        
        return max(naming_score, 0.0)
    
    def _analyze_structure(self, tree: ast.AST) -> float:
        """Analyze code structure (0-1 score)"""
        structure_score = 1.0
        
        # Check for overly long functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    structure_score -= 0.1
        
        # Check for nested complexity
        max_nesting = self._calculate_max_nesting(tree)
        if max_nesting > 4:
            structure_score -= 0.2
        
        return max(structure_score, 0.0)
    
    def _identify_issues(self, tree: ast.AST, source_code: str, complexity: int) -> List[Dict[str, Any]]:
        """Identify code issues"""
        issues = []
        
        if complexity > self.complexity_threshold:
            issues.append({
                "type": "complexity",
                "severity": "warning",
                "message": f"High complexity ({complexity}). Consider refactoring.",
                "suggestion": "Break down into smaller functions"
            })
        
        # Check for long lines
        lines = source_code.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append({
                    "type": "style",
                    "severity": "info",
                    "line": i,
                    "message": "Line too long (>100 characters)",
                    "suggestion": "Break line or use variable assignment"
                })
        
        # Check for missing type hints
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.returns and node.name != '__init__':
                    issues.append({
                        "type": "typing",
                        "severity": "info",
                        "line": node.lineno,
                        "message": f"Function '{node.name}' missing return type annotation",
                        "suggestion": "Add type hints for better code clarity"
                    })
        
        return issues
    
    def _generate_suggestions(self, complexity: int, doc_score: float, naming_score: float) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if complexity > 10:
            suggestions.append("🔄 Refactor complex functions into smaller, focused functions")
            suggestions.append("🎯 Consider using design patterns to reduce complexity")
        
        if doc_score < 0.5:
            suggestions.append("📚 Add docstrings to functions and classes")
            suggestions.append("💬 Include inline comments for complex logic")
        
        if naming_score < 0.8:
            suggestions.append("🏷️ Use descriptive variable and function names")
            suggestions.append("📝 Follow Python naming conventions (snake_case, PascalCase)")
        
        suggestions.append("✨ Consider using type hints for better IDE support")
        suggestions.append("🧪 Add unit tests for critical functions")
        
        return suggestions
    
    def _get_persona_insights(self, file_path: str, complexity: int, quality_score: float) -> Dict[str, str]:
        """Get insights from different personas"""
        insights = {}
        
        # Cherry's coordination perspective
        insights['cherry'] = (
            f"From a project coordination view: "
            f"{'This code looks well-structured for team collaboration' if quality_score > 0.7 else 'Consider improving code clarity for better team productivity'}. "
            f"{'Complexity is manageable' if complexity < 10 else 'High complexity might slow down development'}"
        )
        
        # Sophia's business intelligence perspective
        if 'payready' in file_path.lower() or 'financial' in file_path.lower():
            insights['sophia'] = (
                f"Pay Ready business perspective: "
                f"{'Code quality supports reliable financial operations' if quality_score > 0.8 else 'Financial code should prioritize reliability and clarity'}. "
                f"Consider business logic separation and error handling."
            )
        
        # Karen's medical/compliance perspective
        if 'paragonrx' in file_path.lower() or 'medical' in file_path.lower():
            insights['karen'] = (
                f"ParagonRX compliance perspective: "
                f"{'Code structure supports medical data accuracy' if quality_score > 0.8 else 'Medical systems require higher code quality standards'}. "
                f"Ensure proper validation and error handling for patient data."
            )
        
        return insights
    
    def _is_snake_case(self, name: str) -> bool:
        """Check if name follows snake_case convention"""
        return re.match(r'^[a-z_][a-z0-9_]*$', name) is not None
    
    def _is_pascal_case(self, name: str) -> bool:
        """Check if name follows PascalCase convention"""
        return re.match(r'^[A-Z][a-zA-Z0-9]*$', name) is not None
    
    def _calculate_max_nesting(self, tree: ast.AST) -> int:
        """Calculate maximum nesting level"""
        max_nesting = 0
        
        def get_nesting_level(node, level=0):
            nonlocal max_nesting
            max_nesting = max(max_nesting, level)
            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                level += 1
            
            for child in ast.iter_child_nodes(node):
                get_nesting_level(child, level)
        
        get_nesting_level(tree)
        return max_nesting

class EnhancedCodeIntelligenceServer:
    """Enhanced MCP server for code intelligence and analysis"""
    
    def __init__(self):
        self.server = Server("code-intelligence")
        self.analyzer = CodeComplexityAnalyzer()
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools for code intelligence"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available code intelligence tools"""
            return [
                types.Tool(
                    name="analyze_file",
                    description="Analyze Python file for complexity, quality, and issues",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "include_suggestions": {"type": "boolean"},
                            "persona_insights": {"type": "boolean"}
                        },
                        "required": ["file_path"]
                    }
                ),
                types.Tool(
                    name="analyze_directory",
                    description="Analyze all Python files in a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "directory_path": {"type": "string"},
                            "recursive": {"type": "boolean"},
                            "max_files": {"type": "integer", "minimum": 1, "maximum": 50}
                        },
                        "required": ["directory_path"]
                    }
                ),
                types.Tool(
                    name="get_quality_report",
                    description="Generate comprehensive code quality report",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_path": {"type": "string"},
                            "include_metrics": {"type": "boolean"},
                            "persona_filter": {"type": "string", "enum": ["all", "cherry", "sophia", "karen"]}
                        },
                        "required": ["target_path"]
                    }
                ),
                types.Tool(
                    name="suggest_refactoring",
                    description="Suggest refactoring strategies for complex code",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "complexity_threshold": {"type": "integer", "minimum": 5, "maximum": 20}
                        },
                        "required": ["file_path"]
                    }
                ),
                types.Tool(
                    name="realtime_analysis",
                    description="Real-time analysis for Cursor AI integration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code_snippet": {"type": "string"},
                            "context": {"type": "string"},
                            "analysis_type": {"type": "string", "enum": ["syntax", "complexity", "quality", "suggestions"]}
                        },
                        "required": ["code_snippet"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls for code intelligence operations"""
            
            if name == "analyze_file":
                return await self._handle_analyze_file(arguments)
            elif name == "analyze_directory":
                return await self._handle_analyze_directory(arguments)
            elif name == "get_quality_report":
                return await self._handle_quality_report(arguments)
            elif name == "suggest_refactoring":
                return await self._handle_suggest_refactoring(arguments)
            elif name == "realtime_analysis":
                return await self._handle_realtime_analysis(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_analyze_file(self, args: dict) -> List[types.TextContent]:
        """Handle file analysis requests"""
        try:
            file_path = args['file_path']
            
            if not os.path.exists(file_path):
                return [types.TextContent(
                    type="text",
                    text=f"❌ File not found: {file_path}"
                )]
            
            analysis = self.analyzer.analyze_file(file_path)
            
            response = f"🔍 Code Analysis: {os.path.basename(file_path)}\n"
            response += "=" * 50 + "\n\n"
            
            response += f"📊 **Quality Score**: {analysis.quality_score:.2f}/1.0\n"
            response += f"🔄 **Complexity**: {analysis.complexity}\n"
            response += f"📏 **Lines of Code**: {analysis.metrics.get('lines_of_code', 0)}\n"
            response += f"🔧 **Functions**: {analysis.metrics.get('functions', 0)}\n"
            response += f"🏗️ **Classes**: {analysis.metrics.get('classes', 0)}\n\n"
            
            if analysis.issues:
                response += "⚠️ **Issues Found**:\n"
                for i, issue in enumerate(analysis.issues[:5], 1):
                    response += f"{i}. [{issue['severity'].upper()}] {issue['message']}\n"
                if len(analysis.issues) > 5:
                    response += f"   ... and {len(analysis.issues) - 5} more issues\n"
                response += "\n"
            
            if args.get('include_suggestions', True) and analysis.suggestions:
                response += "💡 **Suggestions**:\n"
                for suggestion in analysis.suggestions[:3]:
                    response += f"• {suggestion}\n"
                response += "\n"
            
            if args.get('persona_insights', True) and analysis.persona_insights:
                response += "🎭 **Persona Insights**:\n"
                for persona, insight in analysis.persona_insights.items():
                    response += f"**{persona.title()}**: {insight}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error analyzing file: {str(e)}"
            )]
    
    async def _handle_analyze_directory(self, args: dict) -> List[types.TextContent]:
        """Handle directory analysis requests"""
        try:
            directory_path = args['directory_path']
            recursive = args.get('recursive', True)
            max_files = args.get('max_files', 20)
            
            if not os.path.exists(directory_path):
                return [types.TextContent(
                    type="text",
                    text=f"❌ Directory not found: {directory_path}"
                )]
            
            # Find Python files
            python_files = []
            if recursive:
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        if file.endswith('.py'):
                            python_files.append(os.path.join(root, file))
            else:
                python_files = [os.path.join(directory_path, f) 
                              for f in os.listdir(directory_path) 
                              if f.endswith('.py')]
            
            python_files = python_files[:max_files]
            
            if not python_files:
                return [types.TextContent(
                    type="text",
                    text=f"📁 No Python files found in {directory_path}"
                )]
            
            # Analyze files
            analyses = []
            for file_path in python_files:
                analysis = self.analyzer.analyze_file(file_path)
                analyses.append(analysis)
            
            # Generate summary
            avg_quality = sum(a.quality_score for a in analyses) / len(analyses)
            avg_complexity = sum(a.complexity for a in analyses) / len(analyses)
            total_issues = sum(len(a.issues) for a in analyses)
            
            response = f"📁 Directory Analysis: {os.path.basename(directory_path)}\n"
            response += "=" * 60 + "\n\n"
            
            response += f"📊 **Summary**:\n"
            response += f"• Files analyzed: {len(analyses)}\n"
            response += f"• Average quality: {avg_quality:.2f}/1.0\n"
            response += f"• Average complexity: {avg_complexity:.1f}\n"
            response += f"• Total issues: {total_issues}\n\n"
            
            response += "🏆 **Top Files by Quality**:\n"
            top_files = sorted(analyses, key=lambda x: x.quality_score, reverse=True)[:5]
            for i, analysis in enumerate(top_files, 1):
                filename = os.path.basename(analysis.file_path)
                response += f"{i}. {filename}: {analysis.quality_score:.2f} (complexity: {analysis.complexity})\n"
            
            response += "\n⚠️ **Files Needing Attention**:\n"
            problem_files = sorted(analyses, key=lambda x: x.quality_score)[:3]
            for i, analysis in enumerate(problem_files, 1):
                filename = os.path.basename(analysis.file_path)
                response += f"{i}. {filename}: {analysis.quality_score:.2f} ({len(analysis.issues)} issues)\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error analyzing directory: {str(e)}"
            )]
    
    async def _handle_quality_report(self, args: dict) -> List[types.TextContent]:
        """Handle quality report generation"""
        try:
            target_path = args['target_path']
            include_metrics = args.get('include_metrics', True)
            persona_filter = args.get('persona_filter', 'all')
            
            response = f"📋 Code Quality Report\n"
            response += "=" * 50 + "\n\n"
            response += f"🎯 **Target**: {target_path}\n"
            response += f"📅 **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            if os.path.isfile(target_path):
                analysis = self.analyzer.analyze_file(target_path)
                response += self._format_quality_report(analysis, include_metrics, persona_filter)
            else:
                response += "📁 Directory analysis not implemented in quality report yet.\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error generating quality report: {str(e)}"
            )]
    
    async def _handle_suggest_refactoring(self, args: dict) -> List[types.TextContent]:
        """Handle refactoring suggestions"""
        try:
            file_path = args['file_path']
            threshold = args.get('complexity_threshold', 10)
            
            analysis = self.analyzer.analyze_file(file_path)
            
            response = f"🔄 Refactoring Suggestions: {os.path.basename(file_path)}\n"
            response += "=" * 60 + "\n\n"
            
            if analysis.complexity > threshold:
                response += f"⚠️ **High Complexity Detected**: {analysis.complexity}\n\n"
                response += "🎯 **Refactoring Strategies**:\n"
                response += "1. **Extract Method**: Break large functions into smaller ones\n"
                response += "2. **Extract Class**: Group related functionality\n"
                response += "3. **Simplify Conditionals**: Use guard clauses and early returns\n"
                response += "4. **Remove Code Duplication**: Create reusable functions\n"
                response += "5. **Use Design Patterns**: Consider Strategy or Command patterns\n\n"
            else:
                response += f"✅ **Complexity is manageable**: {analysis.complexity}\n\n"
            
            response += "💡 **General Improvements**:\n"
            for suggestion in analysis.suggestions:
                response += f"• {suggestion}\n"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error generating refactoring suggestions: {str(e)}"
            )]
    
    async def _handle_realtime_analysis(self, args: dict) -> List[types.TextContent]:
        """Handle real-time analysis for Cursor integration"""
        try:
            code_snippet = args['code_snippet']
            analysis_type = args.get('analysis_type', 'quality')
            
            # Create temporary file for analysis
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code_snippet)
                temp_file = f.name
            
            try:
                analysis = self.analyzer.analyze_file(temp_file)
                
                if analysis_type == 'syntax':
                    response = "✅ Syntax is valid" if not analysis.issues else "❌ Syntax errors detected"
                elif analysis_type == 'complexity':
                    response = f"🔄 Complexity: {analysis.complexity} ({'High' if analysis.complexity > 10 else 'Normal'})"
                elif analysis_type == 'quality':
                    response = f"📊 Quality: {analysis.quality_score:.2f}/1.0"
                else:  # suggestions
                    response = "💡 Suggestions:\n" + "\n".join(f"• {s}" for s in analysis.suggestions[:3])
                
            finally:
                os.unlink(temp_file)
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error in real-time analysis: {str(e)}"
            )]
    
    def _format_quality_report(self, analysis: CodeAnalysis, include_metrics: bool, persona_filter: str) -> str:
        """Format detailed quality report"""
        response = f"📊 **Overall Quality**: {analysis.quality_score:.2f}/1.0\n\n"
        
        if include_metrics:
            response += "📈 **Detailed Metrics**:\n"
            for metric, value in analysis.metrics.items():
                response += f"• {metric.replace('_', ' ').title()}: {value}\n"
            response += "\n"
        
        if analysis.issues:
            response += "⚠️ **Issues**:\n"
            for issue in analysis.issues:
                response += f"• [{issue['severity'].upper()}] {issue['message']}\n"
            response += "\n"
        
        if persona_filter != 'all' and persona_filter in analysis.persona_insights:
            response += f"🎭 **{persona_filter.title()} Insight**:\n"
            response += analysis.persona_insights[persona_filter] + "\n"
        elif persona_filter == 'all' and analysis.persona_insights:
            response += "🎭 **Persona Insights**:\n"
            for persona, insight in analysis.persona_insights.items():
                response += f"**{persona.title()}**: {insight}\n"
        
        return response

async def main():
    """Main server execution"""
    logger.info("🔍 Starting Enhanced Code Intelligence Server")
    logger.info("🎯 Features: Real-time analysis, complexity detection, persona insights")
    logger.info("🔗 Integration: Cursor AI compatible with MCP protocol")
    
    server = EnhancedCodeIntelligenceServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            None
        )

if __name__ == "__main__":
    asyncio.run(main()) 