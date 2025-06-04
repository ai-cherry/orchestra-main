# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
Database Schema Validation Script for Cherry AI
Comprehensive validation of database schemas, migrations, and model definitions.
"""

import os
import re
import json
import ast
import sqlparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from typing_extensions import Optional
from collections.abc import defaultdict
from datetime import datetime

class DatabaseSchemaValidator:
    """Validates database schemas, migrations, and model definitions."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "duplicate_tables": [],
            "invalid_foreign_keys": [],
            "duplicate_indexes": [],
            "migration_conflicts": [],
            "model_schema_mismatches": [],
            "recommendations": []
        }
        
        # Track discovered elements
        self.tables = defaultdict(list)  # table_name -> [(file, definition)]
        self.indexes = defaultdict(list)  # index_name -> [(file, definition)]
        self.foreign_keys = []  # List of foreign key definitions
        self.migrations = []  # List of migration files with sequence numbers
        self.models = {}  # model_name -> model_definition
        
    def find_database_files(self) -> Dict[str, List[Path]]:
        """Find all database-related files."""
        db_files = {
            "migration_files": [],
            "sql_files": [],
            "model_files": [],
            "schema_files": []
        }
        
        # Find migration files
        migrations_dir = self.root_path / "migrations"
        if migrations_dir.exists():
            # TODO: Consider using list comprehension for better performance

            for sql_file in migrations_dir.rglob("*.sql"):
                db_files["migration_files"].append(sql_file)
        
        # Find other SQL files
        for sql_file in self.root_path.rglob("*.sql"):
            if self._should_include(sql_file) and sql_file not in db_files["migration_files"]:
                db_files["sql_files"].append(sql_file)
        
        # Find Python model files
        model_patterns = ["*models.py", "*model.py", "models/*.py"]
        for pattern in model_patterns:
            for py_file in self.root_path.rglob(pattern):
                if self._should_include(py_file):
                    db_files["model_files"].append(py_file)
        
        # Find schema files
        schema_patterns = ["*schema*.py", "*schema*.sql", "*schema*.json"]
        for pattern in schema_patterns:
            for schema_file in self.root_path.rglob(pattern):
                if self._should_include(schema_file):
                    db_files["schema_files"].append(schema_file)
        
        return db_files
    
    def _should_include(self, file_path: Path) -> bool:
        """Check if file should be included in validation."""
        exclude_dirs = {"venv", "node_modules", "__pycache__", ".git", "build", "dist"}
        
        for parent in file_path.parents:
            if parent.name in exclude_dirs:
                return False
        
        return True
    
    def validate_migrations(self, migration_files: List[Path]) -> None:
        """Validate migration files for sequence and conflicts."""
        print(f"🔍 Validating {len(migration_files)} migration files...")
        
        migration_sequences = []
        migration_tables = defaultdict(list)
        
        for migration_file in migration_files:
            try:
                # Extract sequence number from filename
                sequence_match = re.search(r'(\d+)', migration_file.name)
                sequence_num = int(sequence_match.group(1)) if sequence_match else 999
                
                content = migration_file.read_text(encoding='utf-8')
                self._parse_sql_content(content, migration_file)
                
                # Track tables created in this migration
                tables_in_migration = self._extract_tables_from_sql(content)
                for table in tables_in_migration:
                    migration_tables[table].append((migration_file, sequence_num))
                
                migration_sequences.append({
                    "file": migration_file,
                    "sequence": sequence_num,
                    "tables": tables_in_migration
                })
                
            except Exception as e:
                print(f"⚠️  Error parsing migration {migration_file}: {e}")
        
        # Check for sequence conflicts
        self._check_migration_sequence(migration_sequences)
        
        # Check for table conflicts across migrations
        self._check_migration_table_conflicts(migration_tables)
    
    def _extract_tables_from_sql(self, sql_content: str) -> List[str]:
        """Extract table names from SQL content."""
        tables = []
        
        # Parse CREATE TABLE statements
        create_table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"]?\w+[`"]?)'
        matches = re.findall(create_table_pattern, sql_content, re.IGNORECASE)
        
        for match in matches:
            table_name = match.strip('`"')
            tables.append(table_name)
        
        return tables
    
    def _check_migration_sequence(self, migration_sequences: List[Dict]) -> None:
        """Check for migration sequence conflicts."""
        # Sort by sequence number
        sorted_migrations = sorted(migration_sequences, key=lambda x: x["sequence"])
        
        # Check for duplicate sequence numbers
        seen_sequences = set()
        for migration in sorted_migrations:
            seq_num = migration["sequence"]
            if seq_num in seen_sequences:
                self.validation_results["migration_conflicts"].append({
                    "type": "duplicate_sequence",
                    "sequence": seq_num,
                    "files": [str(m["file"]) for m in sorted_migrations if m["sequence"] == seq_num],
                    "severity": "high"
                })
            seen_sequences.add(seq_num)
        
        # Check for gaps in sequence
        expected_seq = 1
        for migration in sorted_migrations:
            if migration["sequence"] != expected_seq and migration["sequence"] != 999:  # 999 for non-numbered files
                self.validation_results["migration_conflicts"].append({
                    "type": "sequence_gap",
                    "expected": expected_seq,
                    "found": migration["sequence"],
                    "file": str(migration["file"]),
                    "severity": "medium"
                })
                break
            expected_seq += 1
    
    def _check_migration_table_conflicts(self, migration_tables: Dict) -> None:
        """Check for table definition conflicts across migrations."""
        for table_name, occurrences in migration_tables.items():
            if len(occurrences) > 1:
                self.validation_results["migration_conflicts"].append({
                    "type": "duplicate_table_creation",
                    "table": table_name,
                    "occurrences": [(str(file), seq) for file, seq in occurrences],
                    "severity": "high"
                })
    
    def _parse_sql_content(self, content: str, file_path: Path) -> None:
        """Parse SQL content to extract tables, indexes, and foreign keys."""
        try:
            # Parse with sqlparse
            statements = sqlparse.split(content)
            
            for statement in statements:
                parsed = sqlparse.parse(statement)[0] if sqlparse.parse(statement) else None
                if parsed:
                    self._analyze_sql_statement(parsed, file_path)
                    
        except Exception as e:
            # Fallback to regex parsing if sqlparse fails
            self._parse_sql_with_regex(content, file_path)
    
    def _analyze_sql_statement(self, parsed_statement, file_path: Path) -> None:
        """Analyze a parsed SQL statement."""
        statement_str = str(parsed_statement).strip().upper()
        
        # Extract table definitions
        if statement_str.startswith('CREATE TABLE'):
            table_match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"]?\w+[`"]?)', 
                                  statement_str, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1).strip('`"')
                self.tables[table_name].append({
                    "file": str(file_path),
                    "definition": str(parsed_statement)[:200] + "..." if len(str(parsed_statement)) > 200 else str(parsed_statement)
                })
        
        # Extract index definitions
        elif statement_str.startswith('CREATE INDEX') or statement_str.startswith('CREATE UNIQUE INDEX'):
            index_match = re.search(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+([`"]?\w+[`"]?)', 
                                  statement_str, re.IGNORECASE)
            if index_match:
                index_name = index_match.group(1).strip('`"')
                self.indexes[index_name].append({
                    "file": str(file_path),
                    "definition": str(parsed_statement)
                })
        
        # Extract foreign key constraints
        if 'FOREIGN KEY' in statement_str:
            fk_matches = re.findall(r'FOREIGN\s+KEY\s*\([^)]+\)\s+REFERENCES\s+(\w+)', 
                                  statement_str, re.IGNORECASE)
            for fk_match in fk_matches:
                self.foreign_keys.append({
                    "file": str(file_path),
                    "references": fk_match,
                    "definition": str(parsed_statement)
                })
    
    def _parse_sql_with_regex(self, content: str, file_path: Path) -> None:
        """Fallback regex-based SQL parsing."""
        # Extract table definitions
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`"]?\w+[`"]?)'
        table_matches = re.findall(table_pattern, content, re.IGNORECASE)
        
        for table_name in table_matches:
            table_name = table_name.strip('`"')
            self.tables[table_name].append({
                "file": str(file_path),
                "definition": "Regex extracted - full definition not available"
            })
        
        # Extract index definitions
        index_pattern = r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+([`"]?\w+[`"]?)'
        index_matches = re.findall(index_pattern, content, re.IGNORECASE)
        
        for index_name in index_matches:
            index_name = index_name.strip('`"')
            self.indexes[index_name].append({
                "file": str(file_path),
                "definition": "Regex extracted - full definition not available"
            })
    
    def validate_sql_files(self, sql_files: List[Path]) -> None:
        """Validate standalone SQL files."""
        print(f"📄 Validating {len(sql_files)} SQL schema files...")
        
        for sql_file in sql_files:
            try:
                content = sql_file.read_text(encoding='utf-8')
                self._parse_sql_content(content, sql_file)
            except Exception as e:
                print(f"⚠️  Error parsing SQL file {sql_file}: {e}")
    
    def validate_models(self, model_files: List[Path]) -> None:
        """Validate Python model files."""
        print(f"🐍 Validating {len(model_files)} Python model files...")
        
        for model_file in model_files:
            try:
                content = model_file.read_text(encoding='utf-8')
                self._parse_python_models(content, model_file)
            except Exception as e:
                print(f"⚠️  Error parsing model file {model_file}: {e}")
    
    def _parse_python_models(self, content: str, file_path: Path) -> None:
        """Parse Python model files to extract model definitions."""
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's likely a database model
                    if self._is_database_model(node, content):
                        model_info = self._extract_model_info(node, content)
                        self.models[node.name] = {
                            "file": str(file_path),
                            "fields": model_info["fields"],
                            "table_name": model_info.get("table_name", node.name.lower()),
                            "relationships": model_info["relationships"]
                        }
                        
        except SyntaxError as e:
            print(f"⚠️  Syntax error in {file_path}: {e}")
    
    def _is_database_model(self, class_node: ast.ClassDef, content: str) -> bool:
        """Check if a class is likely a database model."""
        # Check for common ORM base classes
        base_classes = ['Model', 'Base', 'DeclarativeBase', 'SQLModel']
        
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in base_classes:
                return True
            elif isinstance(base, ast.Attribute) and base.attr in base_classes:
                return True
        
        # Check for common ORM field types in the class
        model_indicators = ['Column', 'Field', 'relationship', 'ForeignKey', '__tablename__']
        class_content = ast.get_source_segment(content, class_node) or ""
        
        return any(indicator in class_content for indicator in model_indicators)
    
    def _extract_model_info(self, class_node: ast.ClassDef, content: str) -> Dict:
        """Extract field and relationship information from model class."""
        info = {
            "fields": [],
            "relationships": [],
            "table_name": None
        }
        
        class_content = ast.get_source_segment(content, class_node) or ""
        
        # Extract table name if defined
        table_match = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', class_content)
        if table_match:
            info["table_name"] = table_match.group(1)
        
        # Extract field definitions (basic regex approach)
        field_patterns = [
            r'(\w+)\s*=\s*Column\(',
            r'(\w+)\s*=\s*Field\(',
            r'(\w+)\s*:\s*.*=\s*Field\('
        ]
        
        for pattern in field_patterns:
            field_matches = re.findall(pattern, class_content)
            info["fields"].extend(field_matches)
        
        # Extract relationships
        relationship_patterns = [
            r'(\w+)\s*=\s*relationship\(',
            r'(\w+)\s*=\s*ForeignKey\('
        ]
        
        for pattern in relationship_patterns:
            rel_matches = re.findall(pattern, class_content)
            info["relationships"].extend(rel_matches)
        
        return info
    
    def check_duplicate_tables(self) -> None:
        """Check for duplicate table definitions."""
        print("🔍 Checking for duplicate table definitions...")
        
        for table_name, definitions in self.tables.items():
            if len(definitions) > 1:
                # Check if definitions are actually different
                unique_defs = set(d["definition"] for d in definitions)
                
                self.validation_results["duplicate_tables"].append({
                    "table": table_name,
                    "count": len(definitions),
                    "files": [d["file"] for d in definitions],
                    "different_definitions": len(unique_defs) > 1,
                    "severity": "high" if len(unique_defs) > 1 else "medium"
                })
    
    def check_duplicate_indexes(self) -> None:
        """Check for duplicate index definitions."""
        print("🔍 Checking for duplicate index definitions...")
        
        for index_name, definitions in self.indexes.items():
            if len(definitions) > 1:
                self.validation_results["duplicate_indexes"].append({
                    "index": index_name,
                    "count": len(definitions),
                    "files": [d["file"] for d in definitions],
                    "severity": "medium"
                })
    
    def validate_foreign_keys(self) -> None:
        """Validate foreign key relationships."""
        print("🔗 Validating foreign key relationships...")
        
        # Get list of all defined tables
        defined_tables = set(self.tables.keys())
        
        # Add tables from models
        for model_name, model_info in self.models.items():
            defined_tables.add(model_info["table_name"])
        
        # Check each foreign key reference
        for fk in self.foreign_keys:
            referenced_table = fk["references"]
            if referenced_table not in defined_tables:
                self.validation_results["invalid_foreign_keys"].append({
                    "file": fk["file"],
                    "referenced_table": referenced_table,
                    "defined_tables": list(defined_tables),
                    "severity": "high"
                })
    
    def check_model_schema_consistency(self) -> None:
        """Check consistency between model definitions and SQL schemas."""
        print("🔄 Checking model-schema consistency...")
        
        for model_name, model_info in self.models.items():
            table_name = model_info["table_name"]
            
            # Check if corresponding table exists in SQL
            if table_name not in self.tables:
                self.validation_results["model_schema_mismatches"].append({
                    "type": "missing_table",
                    "model": model_name,
                    "expected_table": table_name,
                    "model_file": model_info["file"],
                    "severity": "high"
                })
            else:
                # TODO: Add more detailed field-level comparison
                # This would require more sophisticated SQL parsing
                pass
    
    def generate_recommendations(self) -> None:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Duplicate tables
        if self.validation_results["duplicate_tables"]:
            recommendations.append({
                "category": "Schema Consistency",
                "issue": f"{len(self.validation_results['duplicate_tables'])} duplicate table definitions found",
                "recommendation": "Consolidate duplicate table definitions and ensure single source of truth",
                "priority": "high"
            })
        
        # Migration conflicts
        if self.validation_results["migration_conflicts"]:
            recommendations.append({
                "category": "Migration Management",
                "issue": f"{len(self.validation_results['migration_conflicts'])} migration conflicts found",
                "recommendation": "Fix migration sequence and resolve table creation conflicts",
                "priority": "critical"
            })
        
        # Invalid foreign keys
        if self.validation_results["invalid_foreign_keys"]:
            recommendations.append({
                "category": "Data Integrity",
                "issue": f"{len(self.validation_results['invalid_foreign_keys'])} invalid foreign key references",
                "recommendation": "Create missing referenced tables or fix foreign key references",
                "priority": "high"
            })
        
        # Model-schema mismatches
        if self.validation_results["model_schema_mismatches"]:
            recommendations.append({
                "category": "Model Consistency",
                "issue": f"{len(self.validation_results['model_schema_mismatches'])} model-schema mismatches",
                "recommendation": "Ensure model definitions match actual database schema",
                "priority": "medium"
            })
        
        self.validation_results["recommendations"] = recommendations
    
    def run_validation(self) -> Dict:
        """Run complete database schema validation."""
        print("🔍 Starting Database Schema Validation...")
        
        # Find all database files
        db_files = self.find_database_files()
        
        # Validate each category
        self.validate_migrations(db_files["migration_files"])
        self.validate_sql_files(db_files["sql_files"])
        self.validate_models(db_files["model_files"])
        
        # Run consistency checks
        self.check_duplicate_tables()
        self.check_duplicate_indexes()
        self.validate_foreign_keys()
        self.check_model_schema_consistency()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Compile summary
        self.validation_results["summary"] = {
            "migration_files": len(db_files["migration_files"]),
            "sql_files": len(db_files["sql_files"]),
            "model_files": len(db_files["model_files"]),
            "schema_files": len(db_files["schema_files"]),
            "total_tables": len(self.tables),
            "total_indexes": len(self.indexes),
            "total_models": len(self.models),
            "duplicate_tables_count": len(self.validation_results["duplicate_tables"]),
            "invalid_fks_count": len(self.validation_results["invalid_foreign_keys"]),
            "duplicate_indexes_count": len(self.validation_results["duplicate_indexes"]),
            "migration_conflicts_count": len(self.validation_results["migration_conflicts"]),
            "model_mismatches_count": len(self.validation_results["model_schema_mismatches"])
        }
        
        return self.validation_results
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report."""
        summary = self.validation_results["summary"]
        
        report = f"""
🗄️  Database Schema Validation Report
====================================
Generated: {self.validation_results['timestamp']}

📊 VALIDATION SUMMARY
--------------------
Database Files Analyzed:
• Migration Files: {summary['migration_files']}
• SQL Schema Files: {summary['sql_files']}
• Model Files: {summary['model_files']}
• Schema Definition Files: {summary['schema_files']}

Schema Elements Found:
• Tables: {summary['total_tables']}
• Indexes: {summary['total_indexes']}
• Models: {summary['total_models']}

🚨 ISSUES FOUND
---------------
• Duplicate Tables: {summary['duplicate_tables_count']}
• Invalid Foreign Keys: {summary['invalid_fks_count']}
• Duplicate Indexes: {summary['duplicate_indexes_count']}
• Migration Conflicts: {summary['migration_conflicts_count']}
• Model-Schema Mismatches: {summary['model_mismatches_count']}

"""
        
        # Migration conflicts
        if self.validation_results["migration_conflicts"]:
            report += """
⚠️  MIGRATION CONFLICTS
----------------------
"""
            for conflict in self.validation_results["migration_conflicts"]:
                if conflict["type"] == "duplicate_sequence":
                    report += f"❌ Duplicate sequence {conflict['sequence']}: {', '.join(conflict['files'])}\n"
                elif conflict["type"] == "sequence_gap":
                    report += f"⚠️  Sequence gap: Expected {conflict['expected']}, found {conflict['found']} in {conflict['file']}\n"
                elif conflict["type"] == "duplicate_table_creation":
                    report += f"❌ Table '{conflict['table']}' created multiple times: {conflict['occurrences']}\n"
        
        # Duplicate tables
        if self.validation_results["duplicate_tables"]:
            report += """
🔄 DUPLICATE TABLES
------------------
"""
            for dup in self.validation_results["duplicate_tables"]:
                severity_icon = "❌" if dup["different_definitions"] else "⚠️ "
                report += f"{severity_icon} Table '{dup['table']}' defined {dup['count']} times:\n"
                for file in dup['files']:
                    report += f"   📁 {file}\n"
                report += "\n"
        
        # Invalid foreign keys
        if self.validation_results["invalid_foreign_keys"]:
            report += """
🔗 INVALID FOREIGN KEY REFERENCES
--------------------------------
"""
            for fk in self.validation_results["invalid_foreign_keys"]:
                report += f"❌ References missing table '{fk['referenced_table']}' in {fk['file']}\n"
        
        # Recommendations
        if self.validation_results["recommendations"]:
            report += """
🔧 PRIORITY RECOMMENDATIONS
--------------------------
"""
            for rec in self.validation_results["recommendations"]:
                priority_icon = {"critical": "🔴", "high": "🟡", "medium": "🟠", "low": "🟢"}
                icon = priority_icon.get(rec["priority"], "ℹ️")
                report += f"{icon} {rec['category']}: {rec['recommendation']}\n"
        
        report += """
📋 NEXT STEPS
-------------
1. Fix migration sequence conflicts
2. Consolidate duplicate table definitions
3. Resolve invalid foreign key references
4. Ensure model definitions match schema
5. Establish database schema governance
"""
        
        return report


def main():
    """Run the database schema validation."""
    validator = DatabaseSchemaValidator(".")
    results = validator.run_validation()
    
    # Generate and save report
    report = validator.generate_report()
    print(report)
    
    # Save detailed results to JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = f"database_schema_validation_{timestamp}.json"
    
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed validation results saved to: {json_file}")
    
    return results


if __name__ == "__main__":
    main() 