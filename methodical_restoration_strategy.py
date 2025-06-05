import logging
logger = logging.getLogger(__name__)

#!/usr/bin/env python3
"""
Methodical Code Restoration Strategy - A deliberate, measured approach to codebase recovery
"""

import json
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import shutil

class MethodicalRestorationStrategy:
    """
    A careful, deliberate approach to analyzing and restoring corrupted code files.
    Each step is measured, with full consideration of implications and outcomes.
    """
    
    def __init__(self):
        self.analysis_depth = 0
        self.decision_log = []
        self.restoration_candidates = []
        self.risk_assessment = {}
        
    def deliberate_analysis(self, file_path: str) -> Dict[str, any]:
        """
        Conduct thorough, multi-layered analysis with careful consideration
        of each finding's implications.
        """
        analysis = {
            'file': file_path,
            'timestamp': datetime.now().isoformat(),
            'layers': {},
            'risk_level': 'unknown',
            'restoration_feasibility': 0.0,
            'recommended_approach': None,
            'considerations': []
        }
        
        # Layer 1: Basic file health
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            analysis['layers']['basic'] = {
                'readable': True,
                'line_count': len(lines),
                'size_bytes': len(content.encode('utf-8')),
                'encoding': 'utf-8'
            }
        except Exception as e:
            analysis['layers']['basic'] = {
                'readable': False,
                'error': str(e)
            }
            analysis['risk_level'] = 'critical'
            return analysis
        
        # Layer 2: Syntax validation
        try:
            compile(content, file_path, 'exec')
            analysis['layers']['syntax'] = {
                'valid': True,
                'compilation': 'successful'
            }
        except SyntaxError as e:
            analysis['layers']['syntax'] = {
                'valid': False,
                'error_type': type(e).__name__,
                'line': e.lineno,
                'message': e.msg,
                'text': e.text
            }
        
        # Layer 3: Structural integrity
        structure_analysis = self._analyze_structure(content, lines)
        analysis['layers']['structure'] = structure_analysis
        
        # Layer 4: Version control history
        vcs_analysis = self._check_version_history(file_path)
        analysis['layers']['version_control'] = vcs_analysis
        
        # Layer 5: Contextual relationships
        context_analysis = self._analyze_context(file_path)
        analysis['layers']['context'] = context_analysis
        
        # Deliberate risk assessment
        analysis['risk_level'] = self._assess_risk(analysis['layers'])
        
        # Feasibility calculation with careful weighting
        analysis['restoration_feasibility'] = self._calculate_feasibility(analysis['layers'])
        
        # Thoughtful recommendation
        analysis['recommended_approach'] = self._recommend_approach(analysis)
        
        # Document considerations
        analysis['considerations'] = self._document_considerations(analysis)
        
        return analysis
    
    def _analyze_structure(self, content: str, lines: List[str]) -> Dict:
        """Carefully examine code structure for patterns and anomalies"""
        structure = {
            'imports': {'count': 0, 'locations': [], 'scattered': False},
            'functions': {'count': 0, 'names': []},
            'classes': {'count': 0, 'names': []},
            'docstrings': {'count': 0, 'orphaned': []},
            'indentation': {'consistent': True, 'style': None, 'issues': []},
            'anomalies': []
        }
        
        import_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Track imports
            if stripped.startswith(('import ', 'from ')) and ' import ' in stripped:
                import_lines.append(i)
                structure['imports']['locations'].append(i)
            
            # Track functions
            if stripped.startswith('def '):
                func_name = stripped[4:].split('(')[0].strip()
                structure['functions']['names'].append(func_name)
                structure['functions']['count'] += 1
            
            # Track classes
            if stripped.startswith('class '):
                class_name = stripped[6:].split('(')[0].split(':')[0].strip()
                structure['classes']['names'].append(class_name)
                structure['classes']['count'] += 1
            
            # Detect orphaned docstrings
            if stripped.startswith('"""') and i > 0:
                prev_line = lines[i-1].strip()
                if not any(prev_line.startswith(x) for x in ['def ', 'class ', 'async def ']):
                    structure['docstrings']['orphaned'].append(i)
            
            # Check indentation consistency
            if line and line[0] in ' \t':
                if '\t' in line and ' ' in line[:len(line) - len(line.lstrip())]:
                    structure['indentation']['issues'].append(f"Mixed tabs/spaces at line {i+1}")
                    structure['indentation']['consistent'] = False
        
        # Assess import scattering
        if import_lines and len(import_lines) > 1:
            if max(import_lines) - min(import_lines) > len(import_lines) + 5:
                structure['imports']['scattered'] = True
                structure['anomalies'].append("Imports are scattered throughout the file")
        
        # Detect structural anomalies
        if structure['functions']['count'] == 0 and structure['classes']['count'] == 0 and len(lines) > 20:
            structure['anomalies'].append("No functions or classes defined despite significant code")
        
        if structure['docstrings']['orphaned']:
            structure['anomalies'].append(f"{len(structure['docstrings']['orphaned'])} orphaned docstrings found")
        
        return structure
    
    def _check_version_history(self, file_path: str) -> Dict:
        """Carefully examine version control history for insights"""
        vcs_info = {
            'has_history': False,
            'last_known_good': None,
            'recent_changes': [],
            'recommendation': None
        }
        
        try:
            # Check if file is in git
            result = subprocess.run(
                ['git', 'ls-files', file_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(file_path) or '.'
            )
            
            if result.returncode == 0 and result.stdout.strip():
                vcs_info['has_history'] = True
                
                # Get last 5 commits for this file
                log_result = subprocess.run(
                    ['git', 'log', '--oneline', '-n', '5', '--', file_path],
                    capture_output=True,
                    text=True
                )
                
                if log_result.returncode == 0:
                    commits = log_result.stdout.strip().split('\n')
                    vcs_info['recent_changes'] = commits
                    
                    if commits:
                        # Check if we can find a working version
                        for commit in commits[:3]:  # Check last 3 commits
                            commit_hash = commit.split()[0]
                            
                            # Get file content at that commit
                            show_result = subprocess.run(
                                ['git', 'show', f'{commit_hash}:{file_path}'],
                                capture_output=True,
                                text=True
                            )
                            
                            if show_result.returncode == 0:
                                try:
                                    # Test if it compiles
                                    compile(show_result.stdout, file_path, 'exec')
                                    vcs_info['last_known_good'] = commit_hash
                                    vcs_info['recommendation'] = f"Restore from commit {commit_hash}"
                                    break
                                except:
                                    continue
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            pass
        
        return vcs_info
    
    def _analyze_context(self, file_path: str) -> Dict:
        """Examine file's relationship to surrounding codebase"""
        context = {
            'directory': str(Path(file_path).parent),
            'module_type': 'unknown',
            'dependencies': [],
            'related_files': []
        }
        
        # Determine module type from path
        path_parts = Path(file_path).parts
        if 'tests' in path_parts or 'test_' in Path(file_path).name:
            context['module_type'] = 'test'
        elif 'scripts' in path_parts:
            context['module_type'] = 'script'
        elif 'mcp_server' in path_parts:
            context['module_type'] = 'mcp_component'
        elif 'core' in path_parts:
            context['module_type'] = 'core_component'
        
        # Find related files
        parent_dir = Path(file_path).parent
        if parent_dir.exists():
            related = [
                str(f.relative_to(parent_dir)) 
                for f in parent_dir.glob('*.py') 
                if f.name != Path(file_path).name
            ]
            context['related_files'] = related[:5]  # Limit to 5
        
        return context
    
    def _assess_risk(self, layers: Dict) -> str:
        """Carefully assess risk level based on all analysis layers"""
        risk_score = 0
        
        # Basic readability
        if not layers['basic'].get('readable', False):
            return 'critical'
        
        # Syntax validity
        if not layers['syntax'].get('valid', False):
            risk_score += 3
        
        # Structural issues
        structure = layers['structure']
        if structure['anomalies']:
            risk_score += len(structure['anomalies'])
        if not structure['indentation']['consistent']:
            risk_score += 2
        
        # Version control
        if layers['version_control'].get('last_known_good'):
            risk_score -= 2  # Reduce risk if we have a backup
        
        # Determine risk level
        if risk_score <= 1:
            return 'low'
        elif risk_score <= 3:
            return 'medium'
        elif risk_score <= 5:
            return 'high'
        else:
            return 'critical'
    
    def _calculate_feasibility(self, layers: Dict) -> float:
        """Calculate restoration feasibility with careful consideration"""
        feasibility = 0.0
        
        # Version control restoration
        if layers['version_control'].get('last_known_good'):
            feasibility = 0.95  # Very high if we have a good version
            return feasibility
        
        # Structural restoration
        structure = layers['structure']
        if layers['syntax'].get('valid', False):
            feasibility = 0.8  # High if syntax is valid
        elif len(structure['anomalies']) <= 2:
            feasibility = 0.6  # Moderate if few anomalies
        elif structure['functions']['count'] > 0 or structure['classes']['count'] > 0:
            feasibility = 0.4  # Low but possible if has structure
        else:
            feasibility = 0.2  # Very low otherwise
        
        return feasibility
    
    def _recommend_approach(self, analysis: Dict) -> str:
        """Provide thoughtful recommendation based on comprehensive analysis"""
        feasibility = analysis['restoration_feasibility']
        vcs = analysis['layers']['version_control']
        risk = analysis['risk_level']
        
        if vcs.get('last_known_good'):
            return f"restore_from_vcs:{vcs['last_known_good']}"
        elif feasibility >= 0.6:
            return "automated_restructuring"
        elif feasibility >= 0.4:
            return "guided_manual_restoration"
        elif risk == 'critical':
            return "archive_and_rewrite"
        else:
            return "deep_manual_analysis"
    
    def _document_considerations(self, analysis: Dict) -> List[str]:
        """Document key considerations for decision-making"""
        considerations = []
        
        structure = analysis['layers']['structure']
        
        if structure['imports']['scattered']:
            considerations.append("Imports are scattered - suggests merge conflict or automated corruption")
        
        if structure['docstrings']['orphaned']:
            considerations.append(f"{len(structure['docstrings']['orphaned'])} orphaned docstrings indicate structural displacement")
        
        if not structure['indentation']['consistent']:
            considerations.append("Inconsistent indentation requires careful normalization")
        
        if analysis['layers']['context']['module_type'] == 'core_component':
            considerations.append("Core component - restoration is high priority")
        
        if analysis['layers']['context']['module_type'] == 'test':
            considerations.append("Test file - consider regeneration from tested code")
        
        return considerations
    
    def execute_restoration_plan(self, analyses: List[Dict]) -> Dict:
        """Execute restoration with careful deliberation and full documentation"""
        restoration_log = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(analyses),
            'actions_taken': [],
            'files_restored': 0,
            'files_archived': 0,
            'manual_intervention_required': []
        }
        
        for analysis in analyses:
            file_path = analysis['file']
            approach = analysis['recommended_approach']
            
            action = {
                'file': file_path,
                'approach': approach,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'details': {}
            }
            
            if approach.startswith('restore_from_vcs:'):
                commit_hash = approach.split(':')[1]
                success = self._restore_from_vcs(file_path, commit_hash)
                action['success'] = success
                action['details']['commit'] = commit_hash
                if success:
                    restoration_log['files_restored'] += 1
            
            elif approach == 'automated_restructuring':
                # For now, mark for manual intervention
                restoration_log['manual_intervention_required'].append({
                    'file': file_path,
                    'reason': 'Automated restructuring not yet implemented',
                    'feasibility': analysis['restoration_feasibility']
                })
            
            elif approach == 'archive_and_rewrite':
                # Archive the corrupted file
                archive_path = file_path + '.corrupted_archive'
                shutil.copy2(file_path, archive_path)
                action['details']['archived_to'] = archive_path
                restoration_log['files_archived'] += 1
            
            restoration_log['actions_taken'].append(action)
        
        return restoration_log
    
    def _restore_from_vcs(self, file_path: str, commit_hash: str) -> bool:
        """Carefully restore file from version control"""
        try:
            # Get content from specific commit
            result = subprocess.run(
                ['git', 'show', f'{commit_hash}:{file_path}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Backup current corrupted version
                backup_path = file_path + '.corrupted_backup'
                shutil.copy2(file_path, backup_path)
                
                # Write restored content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                
                # Verify restoration
                try:
                    compile(result.stdout, file_path, 'exec')
                    return True
                except:
                    # Restore backup if compilation fails
                    shutil.move(backup_path, file_path)
                    return False
            
            return False
        except Exception:
            return False

def main():
    """Execute methodical restoration strategy with careful deliberation"""
    print("🎯 METHODICAL CODE RESTORATION STRATEGY")
    print("=" * 80)
    print("Approaching restoration with careful deliberation and thorough analysis...")
    print()
    
    # Load critical issues
    with open('critical_issues_action_items.json', 'r') as f:
        critical_issues = json.load(f)
    
    strategy = MethodicalRestorationStrategy()
    
    # Select high-priority files for careful analysis
    priority_files = critical_issues['sample_fixes']['python_indentation'][:3]
    
    analyses = []
    
    print("📊 CONDUCTING DELIBERATE ANALYSIS")
    print("-" * 80)
    
    for file_info in priority_files:
        file_path = file_info['file']
        print(f"\nAnalyzing: {file_path}")
        
        analysis = strategy.deliberate_analysis(file_path)
        analyses.append(analysis)
        
        print(f"  Risk Level: {analysis['risk_level']}")
        print(f"  Feasibility: {analysis['restoration_feasibility']:.1%}")
        print(f"  Recommendation: {analysis['recommended_approach']}")
        
        if analysis['considerations']:
            print("  Considerations:")
            for consideration in analysis['considerations']:
                print(f"    - {consideration}")
    
    print("\n" + "=" * 80)
    print("RESTORATION PLAN EXECUTION")
    print("-" * 80)
    
    restoration_log = strategy.execute_restoration_plan(analyses)
    
    print(f"\nFiles analyzed: {restoration_log['total_files']}")
    print(f"Files restored: {restoration_log['files_restored']}")
    print(f"Files archived: {restoration_log['files_archived']}")
    print(f"Manual intervention required: {len(restoration_log['manual_intervention_required'])}")
    
    # Save comprehensive report
    report = {
        'strategy': 'methodical_restoration',
        'timestamp': datetime.now().isoformat(),
        'analyses': analyses,
        'restoration_log': restoration_log,
        'next_steps': [
            "Review restored files for functionality",
            "Test restored code in isolation",
            "Address files requiring manual intervention",
            "Consider full module rewrites where restoration is infeasible"
        ]
    }
    
    with open('methodical_restoration_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n📄 Comprehensive report saved: methodical_restoration_report.json")
    
    print("\n💡 THOUGHTFUL RECOMMENDATIONS:")
    print("-" * 80)
    print("1. Files with VCS history should be restored from last known good commits")
    print("2. Files with moderate corruption may benefit from guided restructuring")
    print("3. Critically corrupted files without history should be archived and rewritten")
    print("4. Each restoration should be tested in isolation before integration")
    print("5. Consider the broader impact of each file's role in the system")

if __name__ == "__main__":
    main()