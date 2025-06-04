#!/usr/bin/env python3
"""
"""
    """Comprehensive Python codebase analyzer."""
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.python_files = []
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "broken_imports": [],
            "circular_dependencies": [],
            "unused_functions": [],
            "unused_classes": [],
            "duplicate_functions": [],
            "duplicate_classes": [],
            "import_style_issues": [],
            "pep8_issues": [],
            "file_analysis": {}
        }
        self.all_functions = defaultdict(list)  # function_name -> [(file, line)]
        self.all_classes = defaultdict(list)    # class_name -> [(file, line)]
        self.imports_graph = defaultdict(set)   # module -> set of imported modules
        
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
            "venv", "node_modules", "__pycache__", "site-packages", 
            ".git", "migrations", ".pytest_cache", "build", "dist",
            "ui_projects_backup_20250603_162302"
        }
        
        python_files = []
        for py_file in self.root_path.rglob("*.py"):
            # Check if any parent directory is in exclude_dirs
            exclude = False
            for parent in py_file.parents:
                if parent.name in exclude_dirs:
                    exclude = True
                    break
            
            # Also exclude if the file itself is in an excluded directory
            if py_file.parent.name in exclude_dirs:
                exclude = True
            
            if not exclude:
                python_files.append(py_file)
        
        return python_files
    
    def parse_file_safely(self, file_path: Path) -> Optional[ast.AST]:
        """Safely parse a Python file to AST."""
            print(f"⚠️  Failed to parse {file_path}: {e}")
            return None
    
    def extract_imports(self, tree: ast.AST, file_path: Path) -> Dict:
        """Extract import information from AST."""
            "standard": [],    # import module
            "from": [],        # from module import item
            "relative": [],    # from shared.module import item
            "star": []         # from module import *
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # TODO: Consider using list comprehension for better performance

                for alias in node.names:
                    imports["standard"].append({
                        "module": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                level = node.level
                
                for alias in node.names:
                    import_info = {
                        "module": module,
                        "item": alias.name,
                        "alias": alias.asname,
                        "line": node.lineno,
                        "level": level
                    }
                    
                    if level > 0:  # Relative import
                        imports["relative"].append(import_info)
                    elif alias.name == "*":
                        imports["star"].append(import_info)
                    else:
                        imports["from"].append(import_info)
        
        return imports
    
    def extract_definitions(self, tree: ast.AST, file_path: Path) -> Dict:
        """Extract function and class definitions from AST."""
            "functions": [],
            "classes": [],
            "function_calls": set(),
            "class_instantiations": set()
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "is_private": node.name.startswith("_"),
                    "is_dunder": node.name.startswith("__") and node.name.endswith("__"),
                    "decorators": [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list]
                }
                definitions["functions"].append(func_info)
                self.all_functions[node.name].append((str(file_path), node.lineno))
                
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [self._get_name(base) for base in node.bases],
                    "decorators": [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list]
                }
                definitions["classes"].append(class_info)
                self.all_classes[node.name].append((str(file_path), node.lineno))
                
            elif isinstance(node, ast.Call):
                # Track function calls
                func_name = self._get_name(node.func)
                if func_name:
                    definitions["function_calls"].add(func_name)
        
        return definitions
    
    def _get_name(self, node) -> Optional[str]:
        """Extract name from AST node."""
        """Check if imports can be resolved."""
        for imp in imports["standard"]:
            if not self._can_resolve_import(imp["module"], file_dir):
                broken_imports.append({
                    "file": str(file_path),
                    "line": imp["line"],
                    "module": imp["module"],
                    "type": "standard",
                    "issue": "Module not found"
                })
        
        # Check from imports
        for imp in imports["from"]:
            if not self._can_resolve_import(imp["module"], file_dir):
                broken_imports.append({
                    "file": str(file_path),
                    "line": imp["line"],
                    "module": imp["module"],
                    "item": imp["item"],
                    "type": "from",
                    "issue": "Module not found"
                })
        
        return broken_imports
    
    def _can_resolve_import(self, module_name: str, current_dir: Path) -> bool:
        """Check if a module can be resolved."""
                raise TimeoutError("Import resolution timeout")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(2)  # 2 second timeout
            
            try:

            
                pass
                spec = importlib.util.find_spec(module_name)
                result = spec is not None
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
            return result
            
        except Exception:

            
            pass
            # If import fails, check if it's a local module
            pass
        
        # Check if it's a local module
        module_parts = module_name.split('.')
        current_path = current_dir
        
        for part in module_parts:
            potential_file = current_path / f"{part}.py"
            potential_dir = current_path / part
            
            if potential_file.exists():
                return True
            elif potential_dir.exists() and (potential_dir / "__init__.py").exists():
                current_path = potential_dir
            else:
                # Try going up to project root and check from there
                project_root = self.root_path
                potential_from_root = project_root / "/".join(module_parts[:-1]) / f"{module_parts[-1]}.py"
                potential_dir_from_root = project_root / "/".join(module_parts)
                
                if potential_from_root.exists():
                    return True
                elif (potential_dir_from_root.exists() and 
                      (potential_dir_from_root / "__init__.py").exists()):
                    return True
                break
        
        return False
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular import dependencies using DFS."""
        """Find unused functions and classes."""
            definitions = analysis["definitions"]
            
            # Check functions
            for func in definitions["functions"]:
                # Skip private functions, dunder methods, and decorated functions
                if (func["is_private"] or func["is_dunder"] or 
                    func["decorators"] or func["name"] == "main"):
                    continue
                
                # Check if function is called anywhere in the project
                is_used = False
                for other_file, other_analysis in file_analysis.items():
                    if func["name"] in other_analysis["definitions"]["function_calls"]:
                        is_used = True
                        break
                
                if not is_used:
                    unused_functions.append({
                        "file": file_path,
                        "name": func["name"],
                        "line": func["line"]
                    })
            
            # Check classes
            for cls in definitions["classes"]:
                # Check if class is used anywhere
                is_used = False
                for other_file, other_analysis in file_analysis.items():
                    if cls["name"] in other_analysis["definitions"]["class_instantiations"]:
                        is_used = True
                        break
                
                if not is_used and not cls["name"].startswith("_"):
                    unused_classes.append({
                        "file": file_path,
                        "name": cls["name"],
                        "line": cls["line"]
                    })
        
        return unused_functions, unused_classes
    
    def find_duplicates(self) -> Tuple[List[Dict], List[Dict]]:
        """Find duplicate function and class definitions."""
                    "name": func_name,
                    "locations": locations,
                    "count": len(locations)
                })
        
        # Check for duplicate classes
        for class_name, locations in self.all_classes.items():
            if len(locations) > 1:
                duplicate_classes.append({
                    "name": class_name,
                    "locations": locations,
                    "count": len(locations)
                })
        
        return duplicate_functions, duplicate_classes
    
    def check_import_styles(self, file_analysis: Dict) -> List[Dict]:
        """Check for inconsistent import styles."""
            imports = analysis["imports"]
            
            # Check for mix of relative and absolute imports
            has_relative = len(imports["relative"]) > 0
            has_absolute = len(imports["standard"]) + len(imports["from"]) > 0
            
            if has_relative and has_absolute:
                import_style_issues.append({
                    "file": file_path,
                    "issue": "Mixed relative and absolute imports",
                    "relative_count": len(imports["relative"]),
                    "absolute_count": len(imports["standard"]) + len(imports["from"])
                })
            
            # Check for star imports (usually discouraged)
            if imports["star"]:
                import_style_issues.append({
                    "file": file_path,
                    "issue": "Star imports found",
                    "star_imports": imports["star"]
                })
        
        return import_style_issues
    
    def run_analysis(self) -> Dict:
        """Run the complete codebase analysis."""
        print("🔍 Starting Python Codebase Analysis...")
        
        # Find all Python files
        self.python_files = self.find_python_files()
        print(f"📁 Found {len(self.python_files)} Python files to analyze")
        
        # Analyze each file
        file_analysis = {}
        broken_imports = []
        
        for i, file_path in enumerate(self.python_files):
            if i % 50 == 0:
                print(f"📊 Analyzing file {i+1}/{len(self.python_files)}: {file_path.name}")
            
            tree = self.parse_file_safely(file_path)
            if tree is None:
                continue
            
            # Extract imports and definitions
            imports = self.extract_imports(tree, file_path)
            definitions = self.extract_definitions(tree, file_path)
            
            # Check for broken imports
            file_broken_imports = self.check_import_resolution(imports, file_path)
            broken_imports.extend(file_broken_imports)
            
            # Build imports graph for circular dependency detection
            relative_path = str(file_path.relative_to(self.root_path))
            module_name = relative_path.replace('/', '.').replace('.py', '')
            
            for imp in imports["standard"] + imports["from"]:
                if imp["module"]:
                    self.imports_graph[module_name].add(imp["module"])
            
            file_analysis[str(file_path)] = {
                "imports": imports,
                "definitions": definitions,
                "broken_imports": file_broken_imports
            }
        
        print("🔄 Analyzing dependencies and usage...")
        
        # Detect circular dependencies
        circular_deps = self.detect_circular_dependencies()
        
        # Find unused definitions
        unused_functions, unused_classes = self.find_unused_definitions(file_analysis)
        
        # Find duplicates
        duplicate_functions, duplicate_classes = self.find_duplicates()
        
        # Check import styles
        import_style_issues = self.check_import_styles(file_analysis)
        
        # Compile results
        self.results.update({
            "broken_imports": broken_imports,
            "circular_dependencies": circular_deps,
            "unused_functions": unused_functions,
            "unused_classes": unused_classes,
            "duplicate_functions": duplicate_functions,
            "duplicate_classes": duplicate_classes,
            "import_style_issues": import_style_issues,
            "file_analysis": file_analysis,
            "summary": {
                "total_files": len(self.python_files),
                "files_with_broken_imports": len(set(imp["file"] for imp in broken_imports)),
                "broken_import_count": len(broken_imports),
                "circular_dependency_count": len(circular_deps),
                "unused_function_count": len(unused_functions),
                "unused_class_count": len(unused_classes),
                "duplicate_function_count": len(duplicate_functions),
                "duplicate_class_count": len(duplicate_classes),
                "import_style_issue_count": len(import_style_issues)
            }
        })
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        summary = self.results["summary"]
        
        report = f"""
"""
        if self.results["broken_imports"]:
            report += """
"""
            for imp in self.results["broken_imports"][:20]:  # Show first 20
                report += f"❌ {imp['file']}:{imp['line']} - Cannot import '{imp['module']}'\n"
            
            if len(self.results["broken_imports"]) > 20:
                report += f"... and {len(self.results['broken_imports']) - 20} more\n"
        
        # Circular Dependencies
        if self.results["circular_dependencies"]:
            report += """
"""
            for cycle in self.results["circular_dependencies"][:10]:
                report += f"🔄 {' → '.join(cycle)}\n"
        
        # Duplicate Functions
        if self.results["duplicate_functions"]:
            report += """
"""
            for dup in self.results["duplicate_functions"][:10]:
                report += f"⚠️  {dup['name']} defined in {dup['count']} places:\n"
                for file_path, line in dup['locations']:
                    report += f"   - {file_path}:{line}\n"
        
        # Unused Functions (top 20)
        if self.results["unused_functions"]:
            report += """
"""
            for unused in self.results["unused_functions"][:20]:
                report += f"❓ {unused['file']}:{unused['line']} - {unused['name']}()\n"
        
        # Import Style Issues
        if self.results["import_style_issues"]:
            report += """
"""
            for issue in self.results["import_style_issues"][:10]:
                report += f"⚠️  {issue['file']} - {issue['issue']}\n"
        
        report += """
"""
    """Run the Python codebase analysis."""
    analyzer = PythonCodebaseAnalyzer(".")
    results = analyzer.run_analysis()
    
    # Generate and save report
    report = analyzer.generate_report()
    print(report)
    
    # Save detailed results to JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = f"python_analysis_results_{timestamp}.json"
    
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {json_file}")
    
    return results


if __name__ == "__main__":
    main() 