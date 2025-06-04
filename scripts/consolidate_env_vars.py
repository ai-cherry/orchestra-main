# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
Environment Variables Consolidation Script
Consolidates duplicate environment variables from multiple .env files into a master template.
"""

import os
import re
from pathlib import Path
from collections.abc import defaultdict, OrderedDict
from typing import Dict, List, Tuple

class EnvConsolidator:
    """Consolidates environment variables from multiple .env files."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.env_vars = defaultdict(list)  # var_name -> [(file, value, line)]
        self.consolidated = OrderedDict()
        
    def find_env_files(self) -> List[Path]:
        """Find all .env files in the project."""
        env_files = []
        
        # Find .env files
        for env_file in self.root_path.rglob("*.env*"):
            if self._should_include(env_file):
                env_files.append(env_file)
        
        # Find .envrc files
        for envrc_file in self.root_path.rglob(".envrc*"):
            if self._should_include(envrc_file):
                env_files.append(envrc_file)
        
        return sorted(env_files)
    
    def _should_include(self, file_path: Path) -> bool:
        """Check if file should be included."""
        # Exclude certain directories
        exclude_dirs = {"venv", "node_modules", "__pycache__", ".git", "ui_projects_backup_20250603_162302"}
        
        for parent in file_path.parents:
            if parent.name in exclude_dirs:
                return False
        
        # Only include actual .env files, not backups or temp files
        if file_path.suffix in ['.bak', '.tmp', '.old']:
            return False
            
        return True
    
    def parse_env_files(self, env_files: List[Path]) -> None:
        """Parse all environment files and collect variables."""
        print(f"📄 Parsing {len(env_files)} environment files...")
        
        for env_file in env_files:
            print(f"  📂 {env_file}")
            try:
                self._parse_env_file(env_file)
            except Exception as e:
                print(f"⚠️  Error parsing {env_file}: {e}")
    
    def _parse_env_file(self, file_path: Path) -> None:
        """Parse a single environment file."""
        content = file_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse environment variable
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                self.env_vars[key].append({
                    "file": str(file_path.relative_to(self.root_path)),
                    "value": value,
                    "line": line_num,
                    "original_line": original_line
                })
    
    def analyze_duplicates(self) -> Dict:
        """Analyze duplicate environment variables."""
        analysis = {
            "duplicates": [],
            "unique": [],
            "conflicts": []
        }
        
        for var_name, occurrences in self.env_vars.items():
            if len(occurrences) > 1:
                # Check if values are different
                values = set(occ["value"].strip('"').strip("'") # TODO: Consider using list comprehension for better performance
 for occ in occurrences)
                
                if len(values) > 1:
                    analysis["conflicts"].append({
                        "variable": var_name,
                        "occurrences": occurrences,
                        "values": list(values),
                        "severity": "high" if any(sensitive in var_name.lower() 
                                                for sensitive in ["password", "secret", "key", "token"]) else "medium"
                    })
                else:
                    analysis["duplicates"].append({
                        "variable": var_name,
                        "occurrences": occurrences,
                        "value": list(values)[0],
                        "severity": "low"
                    })
            else:
                analysis["unique"].append({
                    "variable": var_name,
                    "occurrence": occurrences[0]
                })
        
        return analysis
    
    def create_master_template(self, analysis: Dict) -> str:
        """Create a master environment template."""
        template_content = []
        
        # Header
        template_content.extend([
            "# =================================================================",
            "# Cherry AI - Master Environment Variables Template",
            "# =================================================================",
            "# This file consolidates all environment variables from the project",
            "# Generated automatically - edit with caution",
            "#",
            "# Usage:",
            "#   - Copy to .env.local for local development",
            "#   - Use as reference for staging/production configuration",
            "# =================================================================",
            "",
        ])
        
        # Group variables by category
        categories = {
            "API Keys & Authentication": [],
            "Database Configuration": [],
            "Service URLs & Endpoints": [],
            "Application Settings": [],
            "Infrastructure": [],
            "Development & Debug": [],
            "Other": []
        }
        
        # Categorize variables
        for conflict in analysis["conflicts"]:
            var_name = conflict["variable"]
            self._categorize_variable(var_name, conflict, categories)
        
        for duplicate in analysis["duplicates"]:
            var_name = duplicate["variable"]
            self._categorize_variable(var_name, duplicate, categories)
        
        for unique in analysis["unique"]:
            var_name = unique["variable"]
            self._categorize_variable(var_name, unique, categories)
        
        # Generate template sections
        for category, variables in categories.items():
            if variables:
                template_content.extend([
                    f"# {category}",
                    "# " + "=" * (len(category) + 2),
                    ""
                ])
                
                for var_info in variables:
                    template_content.extend(self._format_variable_for_template(var_info))
                
                template_content.append("")
        
        return "\n".join(template_content)
    
    def _categorize_variable(self, var_name: str, var_info: Dict, categories: Dict) -> None:
        """Categorize a variable based on its name."""
        var_lower = var_name.lower()
        
        if any(keyword in var_lower for keyword in ["key", "token", "secret", "password", "credential"]):
            categories["API Keys & Authentication"].append(var_info)
        elif any(keyword in var_lower for keyword in ["postgres", "database", "db_", "weaviate", "mongo", "redis"]):
            categories["Database Configuration"].append(var_info)
        elif any(keyword in var_lower for keyword in ["url", "host", "port", "endpoint", "api_"]):
            categories["Service URLs & Endpoints"].append(var_info)
        elif any(keyword in var_lower for keyword in ["debug", "log", "dev", "test"]):
            categories["Development & Debug"].append(var_info)
        elif any(keyword in var_lower for keyword in ["gcp", "aws", "vultr", "cloud", "project"]):
            categories["Infrastructure"].append(var_info)
        elif any(keyword in var_lower for keyword in ["app_", "environment", "mode", "config"]):
            categories["Application Settings"].append(var_info)
        else:
            categories["Other"].append(var_info)
    
    def _format_variable_for_template(self, var_info: Dict) -> List[str]:
        """Format a variable for the template."""
        lines = []
        
        if "occurrences" in var_info:  # Conflict or duplicate with occurrences
            var_name = var_info["variable"]
            
            if "values" in var_info:  # Conflict
                lines.append(f"# ⚠️  CONFLICT: {var_name} has different values across files:")
                for i, occ in enumerate(var_info["occurrences"]):
                    lines.append(f"#   {occ['file']}: {occ['value']}")
                lines.append(f"# Choose appropriate value:")
                lines.append(f"{var_name}=CHOOSE_VALUE_FROM_ABOVE")
            else:  # Duplicate
                lines.append(f"# Duplicated in: {', '.join(occ['file'] for occ in var_info['occurrences'])}")
                lines.append(f"{var_name}={var_info['value']}")
        elif "occurrence" in var_info:  # Unique variable
            var_name = var_info["variable"]
            occ = var_info["occurrence"]
            lines.append(f"# From: {occ['file']}")
            lines.append(f"{var_name}={occ['value']}")
        else:
            # Fallback - extract variable name and value directly
            if "variable" in var_info:
                var_name = var_info["variable"]
                if "value" in var_info:
                    lines.append(f"{var_name}={var_info['value']}")
                else:
                    lines.append(f"{var_name}=VALUE_MISSING")
        
        lines.append("")
        return lines
    
    def generate_consolidation_report(self, analysis: Dict) -> str:
        """Generate a detailed consolidation report."""
        report = f"""
🔧 Environment Variables Consolidation Report
=============================================

📊 SUMMARY
----------
Total Variables Found: {len(self.env_vars)}
• Conflicts (different values): {len(analysis['conflicts'])}
• Duplicates (same values): {len(analysis['duplicates'])}
• Unique variables: {len(analysis['unique'])}

🚨 CRITICAL CONFLICTS REQUIRING ATTENTION
-----------------------------------------
"""
        
        # Show conflicts
        high_priority_conflicts = [c for c in analysis["conflicts"] if c["severity"] == "high"]
        medium_priority_conflicts = [c for c in analysis["conflicts"] if c["severity"] == "medium"]
        
        if high_priority_conflicts:
            report += "HIGH PRIORITY (Security-related):\n"
            for conflict in high_priority_conflicts:
                report += f"❌ {conflict['variable']}:\n"
                for occ in conflict['occurrences']:
                    report += f"   📁 {occ['file']}: {occ['value']}\n"
                report += "\n"
        
        if medium_priority_conflicts:
            report += "MEDIUM PRIORITY:\n"
            for conflict in medium_priority_conflicts:
                report += f"⚠️  {conflict['variable']}:\n"
                for occ in conflict['occurrences']:
                    report += f"   📁 {occ['file']}: {occ['value']}\n"
                report += "\n"
        
        # Show duplicates
        report += """
🔄 DUPLICATED VARIABLES (same values)
------------------------------------
"""
        for duplicate in analysis["duplicates"][:10]:  # Show first 10
            files = ", ".join(occ['file'] for occ in duplicate['occurrences'])
            report += f"• {duplicate['variable']} (in: {files})\n"
        
        if len(analysis["duplicates"]) > 10:
            report += f"... and {len(analysis['duplicates']) - 10} more\n"
        
        report += """
📋 RECOMMENDED ACTIONS
---------------------
1. Review conflicts and choose appropriate values
2. Update .env.master with consolidated variables
3. Remove duplicates from individual .env files
4. Standardize variable naming conventions
5. Add .env.local to .gitignore for local overrides

🔧 NEXT STEPS
-------------
1. Copy generated .env.master to your preferred location
2. Review and resolve all conflicts manually
3. Update your applications to use the consolidated configuration
4. Remove duplicate variables from original files
"""
        
        return report
    
    def run_consolidation(self) -> Tuple[str, str]:
        """Run the complete consolidation process."""
        print("🔧 Starting Environment Variables Consolidation...")
        
        # Find and parse env files
        env_files = self.find_env_files()
        print(f"📁 Found {len(env_files)} environment files:")
        for file in env_files:
            print(f"  • {file.relative_to(self.root_path)}")
        
        self.parse_env_files(env_files)
        
        # Analyze duplicates
        analysis = self.analyze_duplicates()
        
        # Create master template
        master_template = self.create_master_template(analysis)
        
        # Generate report
        report = self.generate_consolidation_report(analysis)
        
        return master_template, report


def main():
    """Run the environment variables consolidation."""
    consolidator = EnvConsolidator(".")
    
    # Run consolidation
    master_template, report = consolidator.run_consolidation()
    
    # Save master template
    with open(".env.master", "w") as f:
        f.write(master_template)
    
    # Save report
    with open("env_consolidation_report.txt", "w") as f:
        f.write(report)
    
    print(report)
    print(f"\n📁 Master template saved to: .env.master")
    print(f"📁 Detailed report saved to: env_consolidation_report.txt")


if __name__ == "__main__":
    main() 