#!/usr/bin/env python3
"""
Intelligent Code Restoration System - Advanced pattern recognition and reconstruction
"""

import ast
import re
import json
import difflib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import subprocess

class IntelligentCodeRestorer:
    """
    Sophisticated code restoration engine employing pattern recognition,
    contextual analysis, and strategic reconstruction methodologies.
    """
    
    def __init__(self):
        self.pattern_library = self._build_pattern_library()
        self.restoration_strategies = {
            'orphaned_docstring': self._restore_orphaned_docstring,
            'import_chaos': self._restore_import_order
        }
        self.context_cache = {}
        
    def _build_pattern_library(self) -> Dict[str, re.Pattern]:
        """Construct sophisticated pattern recognition library"""
        return {
            'class_definition': re.compile(r'^class\s+(\w+).*?:', re.MULTILINE),
            'function_definition': re.compile(r'^def\s+(\w+)\s*\(.*?\).*?:', re.MULTILINE),
            'docstring': re.compile(r'^\s*""".*?"""', re.MULTILINE | re.DOTALL),
            'import_statement': re.compile(r'^(?:from\s+\S+\s+)?import\s+.+$', re.MULTILINE),
            'decorator': re.compile(r'^@\w+.*$', re.MULTILINE),
            'async_function': re.compile(r'^async\s+def\s+(\w+)\s*\(.*?\).*?:', re.MULTILINE),
            'type_hint': re.compile(r':\s*(?:List|Dict|Tuple|Optional|Union)\[.*?\]'),
            'assignment': re.compile(r'^\s*(\w+)\s*=\s*.+$', re.MULTILINE)
        }
    
    def analyze_corruption_patterns(self, file_path: str) -> Dict[str, any]:
        """
        Perform sophisticated analysis to identify corruption patterns
        with strategic intelligence.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            analysis = {
                'file': file_path,
                'corruption_type': None,
                'confidence': 0.0,
                'patterns_found': [],
                'reconstruction_strategy': None,
                'contextual_hints': []
            }
            
            # Detect orphaned docstrings
            orphaned_docstrings = []
            for i, line in enumerate(lines):
                if line.strip().startswith('"""') and i > 0:
                    # Check if previous line is a definition
                    prev_line = lines[i-1].strip()
                    if not (prev_line.startswith('def ') or 
                           prev_line.startswith('class ') or
                           prev_line.startswith('async def ')):
                        orphaned_docstrings.append(i)
            
            if orphaned_docstrings:
                analysis['patterns_found'].append('orphaned_docstrings')
                analysis['corruption_type'] = 'structural_displacement'
                analysis['confidence'] = 0.85
            
            # Detect import chaos
            import_lines = [i for i, line in enumerate(lines) 
                          if self.pattern_library['import_statement'].match(line.strip())]
            if import_lines and max(import_lines) > 20:  # Imports scattered throughout
                analysis['patterns_found'].append('scattered_imports')
                analysis['corruption_type'] = 'import_disorder'
                analysis['confidence'] = max(analysis['confidence'], 0.75)
            
            # Detect missing structure
            has_functions = bool(self.pattern_library['function_definition'].search(content))
            has_classes = bool(self.pattern_library['class_definition'].search(content))
            has_code = len([l for l in lines if l.strip() and not l.strip().startswith('#')]) > 10
            
            if has_code and not (has_functions or has_classes):
                analysis['patterns_found'].append('missing_structure')
                analysis['corruption_type'] = 'structural_absence'
                analysis['confidence'] = 0.90
            
            # Determine reconstruction strategy
            if analysis['corruption_type']:
                analysis['reconstruction_strategy'] = self._determine_strategy(analysis)
            
            return analysis
            
        except Exception as e:
            return {
                'file': file_path,
                'error': str(e),
                'corruption_type': 'unreadable',
                'confidence': 1.0
            }
    
    def _determine_strategy(self, analysis: Dict) -> str:
        """Determine optimal reconstruction strategy with analytical precision"""
        corruption_type = analysis['corruption_type']
        patterns = analysis['patterns_found']
        
        if corruption_type == 'structural_displacement':
            if 'orphaned_docstrings' in patterns:
                return 'docstring_reattachment'
            return 'structural_reorganization'
        
        elif corruption_type == 'import_disorder':
            return 'import_consolidation'
        
        elif corruption_type == 'structural_absence':
            return 'wrapper_generation'
        
        return 'conservative_restructuring'
    
    def restore_file(self, file_path: str, analysis: Dict) -> Tuple[bool, str, Optional[str]]:
        """
        Execute sophisticated restoration with strategic intelligence
        Returns: (success, message, restored_content)
        """
        strategy = analysis.get('reconstruction_strategy')
        
        if not strategy:
            return False, "No restoration strategy identified", None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            if strategy == 'docstring_reattachment':
                restored = self._restore_orphaned_docstring(original_content)
            elif strategy == 'import_consolidation':
                restored = self._restore_import_order(original_content)
            elif strategy == 'wrapper_generation':
                restored = self._generate_wrapper_structure(original_content, file_path)
            else:
                restored = self._conservative_restructure(original_content)
            
            # Validate restoration
            try:
                compile(restored, file_path, 'exec')
                return True, f"Successfully restored using {strategy}", restored
            except SyntaxError as e:
                return False, f"Restoration failed validation: {e}", None
                
        except Exception as e:
            return False, f"Restoration error: {e}", None
    
    def _restore_orphaned_docstring(self, content: str) -> str:
        """Intelligently reattach orphaned docstrings to their logical owners"""
        lines = content.splitlines()
        restored_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # If we find an orphaned docstring
            if (line.strip().startswith('"""') and 
                i > 0 and 
                not any(lines[i-1].strip().startswith(x) for x in ['def ', 'class ', 'async def '])):
                
                # Look ahead for the next function/class
                for j in range(i+1, min(i+10, len(lines))):
                    if any(lines[j].strip().startswith(x) for x in ['def ', 'class ', 'async def ']):
                        # Move the docstring to after the definition
                        restored_lines.append(lines[j])  # Add the definition
                        restored_lines.append(line)      # Add the docstring
                        i = j + 1  # Skip past what we've processed
                        break
                else:
                    # No definition found, skip this docstring
                    i += 1
            else:
                restored_lines.append(line)
                i += 1
        
        return '\n'.join(restored_lines)
    
    def _restore_import_order(self, content: str) -> str:
        """Consolidate and organize imports with sophisticated grouping"""
        lines = content.splitlines()
        
        # Extract all imports
        imports = {
            'standard': [],
            'third_party': [],
            'local': []
        }
        
        other_lines = []
        
        for line in lines:
            if self.pattern_library['import_statement'].match(line.strip()):
                # Classify import
                if line.strip().startswith('from .') or line.strip().startswith('import .'):
                    imports['local'].append(line)
                elif any(line.startswith(f'import {lib}') or line.startswith(f'from {lib}') 
                        for lib in ['os', 'sys', 'json', 'datetime', 're', 'pathlib']):
                    imports['standard'].append(line)
                else:
                    imports['third_party'].append(line)
            else:
                other_lines.append(line)
        
        # Reconstruct with proper import ordering
        restored = []
        
        # Add shebang if present
        if other_lines and other_lines[0].startswith('#!'):
            restored.append(other_lines.pop(0))
        
        # Add module docstring if present
        for i, line in enumerate(other_lines):
            if line.strip().startswith('"""'):
                restored.extend(other_lines[:i+1])
                other_lines = other_lines[i+1:]
                break
        
        # Add imports in proper order
        for group in ['standard', 'third_party', 'local']:
            if imports[group]:
                restored.extend(sorted(set(imports[group])))
                restored.append('')  # Blank line between groups
        
        # Add remaining content
        restored.extend(other_lines)
        
        return '\n'.join(restored)
    
    def _generate_wrapper_structure(self, content: str, file_path: str) -> str:
        """Generate sophisticated wrapper structure for orphaned code"""
        module_name = Path(file_path).stem.replace('_', ' ').title().replace(' ', '')
        
        lines = content.splitlines()
        
        # Analyze code to determine appropriate wrapper
        has_async = any('async' in line or 'await' in line for line in lines)
        has_classes = any(line.strip().startswith('class ') for line in lines)
        
        restored = []
        
        # Add header
        restored.append('#!/usr/bin/env python3')
        restored.append(f'"""{module_name} module - Restored"""')
        restored.append('')
        
        # Add imports at top
        imports = [line for line in lines if self.pattern_library['import_statement'].match(line.strip())]
        if imports:
            restored.extend(imports)
            restored.append('')
            lines = [line for line in lines if line not in imports]
        
        # Wrap orphaned code in a main function
        if not has_classes:
            restored.append('def main():')
            restored.append('    """Main execution function"""')
            for line in lines:
                if line.strip():
                    restored.append('    ' + line)
                else:
                    restored.append('')
            
            restored.append('')
            restored.append('if __name__ == "__main__":')
            restored.append('    main()')
        else:
            restored.extend(lines)
        
        return '\n'.join(restored)
    
    def _conservative_restructure(self, content: str) -> str:
        """Apply conservative restructuring with minimal intervention"""
        lines = content.splitlines()
        
        # Just ensure basic structure
        restored = []
        
        # Ensure shebang is first
        shebang_idx = None
        for i, line in enumerate(lines):
            if line.startswith('#!'):
                shebang_idx = i
                break
        
        if shebang_idx is not None and shebang_idx > 0:
            restored.append(lines[shebang_idx])
            lines.pop(shebang_idx)
        
        # Add remaining lines
        restored.extend(lines)
        
        return '\n'.join(restored)

def main():
    """Execute intelligent restoration workflow"""
    print("🧠 INTELLIGENT CODE RESTORATION SYSTEM")
    print("=" * 80)
    print("Employing sophisticated pattern recognition and strategic reconstruction...\n")
    
    # Load previous analysis
    with open('critical_issues_action_items.json', 'r') as f:
        critical_issues = json.load(f)
    
    restorer = IntelligentCodeRestorer()
    
    # Analyze sample of most problematic files
    sample_files = critical_issues['sample_fixes']['python_indentation'][:5]
    
    restoration_results = []
    
    for file_info in sample_files:
        file_path = file_info['file']
        print(f"\n📊 Analyzing: {file_path}")
        
        analysis = restorer.analyze_corruption_patterns(file_path)
        print(f"  Corruption type: {analysis['corruption_type']}")
        print(f"  Confidence: {analysis['confidence']:.2%}")
        print(f"  Strategy: {analysis.get('reconstruction_strategy', 'None')}")
        
        if analysis.get('reconstruction_strategy'):
            success, message, restored_content = restorer.restore_file(file_path, analysis)
            
            if success and restored_content:
                # Save restored version
                backup_path = file_path + '.corrupted'
                restored_path = file_path + '.restored'
                
                # Create backup of corrupted version
                Path(file_path).rename(backup_path)
                
                # Write restored version
                with open(restored_path, 'w') as f:
                    f.write(restored_content)
                
                print(f"  ✅ {message}")
                print(f"  Saved: {restored_path}")
            else:
                print(f"  ❌ {message}")
        
        restoration_results.append({
            'file': file_path,
            'analysis': analysis,
            'restored': success if 'success' in locals() else False
        })
    
    # Save restoration report
    from datetime import datetime
    with open('intelligent_restoration_report.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'files_analyzed': len(restoration_results),
            'files_restored': sum(1 for r in restoration_results if r['restored']),
            'results': restoration_results
        }, f, indent=2)
    
    print("\n" + "=" * 80)
    print("RESTORATION SUMMARY")
    print("=" * 80)
    print(f"Files analyzed: {len(restoration_results)}")
    print(f"Files restored: {sum(1 for r in restoration_results if r['restored'])}")
    print("\n📄 Report saved: intelligent_restoration_report.json")
    print("\n💡 Next steps:")
    print("1. Review .restored files")
    print("2. Test restored code")
    print("3. Apply successful patterns to remaining files")

if __name__ == "__main__":
    main()