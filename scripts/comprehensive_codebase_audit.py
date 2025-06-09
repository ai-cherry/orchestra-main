import ast
#!/usr/bin/env python3
"""
"""
    """Comprehensive auditor for the integrated system"""
            "duplications": [],
            "naming_conflicts": [],
            "dependency_mismatches": [],
            "config_inconsistencies": [],
            "runtime_errors": [],
            "integration_issues": [],
            "circular_dependencies": [],
            "version_conflicts": [],
            "redundant_implementations": [],
            "api_contract_violations": [],
            "error_handling_issues": [],
            "pattern_inconsistencies": []
        }
        self.modules = {}
        self.imports = defaultdict(set)
        self.functions = defaultdict(list)
        self.classes = defaultdict(list)
        self.configs = {}
        
    def audit_all(self):
        """Run comprehensive audit"""
        print("🔍 COMPREHENSIVE CODEBASE AUDIT")
        print("="*60)
        
        # Phase 1: Discovery
        print("\n📊 Phase 1: Discovery")
        self.discover_modules()
        self.load_configurations()
        
        # Phase 2: Analysis
        print("\n🔬 Phase 2: Analysis")
        self.analyze_code_duplication()
        self.analyze_naming_conflicts()
        self.analyze_dependencies()
        self.analyze_configurations()
        self.analyze_integration_points()
        self.analyze_error_handling()
        self.analyze_coding_patterns()
        self.analyze_api_contracts()
        
        # Phase 3: Validation
        print("\n✅ Phase 3: Validation")
        self.validate_circular_dependencies()
        self.validate_version_compatibility()
        self.validate_runtime_safety()
        
        # Phase 4: Report & Fix
        print("\n📝 Phase 4: Report & Fix")
        self.generate_report()
        self.propose_fixes()
        
    def discover_modules(self):
        """Discover all Python modules in the project"""
        print("  → Discovering modules...")
        
            if any(skip in str(py_file) for skip in ["venv/", "__pycache__", ".git"]):
                continue
                
            self.modules[str(rel_path)] = {
                "path": py_file,
                "imports": set(),
                "functions": [],
                "classes": [],
                "size": py_file.stat().st_size
            }
            
            try:

            
                pass
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    self.analyze_ast(tree, str(rel_path))
            except Exception:

                pass
                self.issues["runtime_errors"].append({
                    "file": str(rel_path),
                    "error": f"Parse error: {str(e)}"
                })
        
        print(f"    ✓ Found {len(self.modules)} Python modules")
    
    def analyze_ast(self, tree: ast.AST, module_path: str):
        """Analyze AST of a module"""
                    self.modules[module_path]["imports"].add(alias.name)
                    self.imports[alias.name].add(module_path)
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.modules[module_path]["imports"].add(node.module)
                    self.imports[node.module].add(module_path)
                    
            elif isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "lineno": node.lineno
                }
                self.modules[module_path]["functions"].append(func_info)
                self.functions[node.name].append((module_path, func_info))
                
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "bases": [self.get_name(base) for base in node.bases],
                    "lineno": node.lineno
                }
                self.modules[module_path]["classes"].append(class_info)
                self.classes[node.name].append((module_path, class_info))
    
    def get_name(self, node):
        """Get name from AST node"""
            return f"{self.get_name(node.value)}.{node.attr}"
        return str(node)
    
    def load_configurations(self):
        """Load all configuration files"""
        print("  → Loading configurations...")
        
        config_patterns = ["*.json", "*.yaml", "*.yml", "*.toml", ".env*"]
        for pattern in config_patterns:
                if any(skip in str(config_file) for skip in ["venv/", "node_modules/", ".git"]):
                    continue
                    
                try:

                    pass
                    if pattern.endswith(".json"):
                        with open(config_file, 'r') as f:
                            self.configs[str(rel_path)] = json.load(f)
                    elif pattern.startswith(".env"):
                        self.configs[str(rel_path)] = self.parse_env_file(config_file)
                except Exception:

                    pass
                    self.issues["config_inconsistencies"].append({
                        "file": str(rel_path),
                        "error": f"Failed to load: {str(e)}"
                    })
        
        print(f"    ✓ Loaded {len(self.configs)} configuration files")
    
    def parse_env_file(self, env_file: Path) -> Dict:
        """Parse .env file"""
        """Analyze code duplication across modules"""
        print("  → Analyzing code duplication...")
        
        # Check for duplicate function implementations
        for func_name, occurrences in self.functions.items():
            if len(occurrences) > 1:
                # Compare function signatures
                signatures = set()
                for module, func_info in occurrences:
                    sig = f"{func_name}({', '.join(func_info['args'])})"
                    signatures.add(sig)
                
                if len(signatures) == 1:  # Same signature in multiple places
                    self.issues["duplications"].append({
                        "type": "function",
                        "name": func_name,
                        "locations": [module for module, _ in occurrences],
                        "severity": "high" if len(occurrences) > 2 else "medium"
                    })
        
        # Check for duplicate class definitions
        for class_name, occurrences in self.classes.items():
            if len(occurrences) > 1:
                self.issues["duplications"].append({
                    "type": "class",
                    "name": class_name,
                    "locations": [module for module, _ in occurrences],
                    "severity": "high"
                })
        
        # Check for similar file names that might indicate duplication
        file_names = defaultdict(list)
        for module_path in self.modules:
            base_name = Path(module_path).stem
            file_names[base_name].append(module_path)
        
        for base_name, paths in file_names.items():
            if len(paths) > 1:
                self.issues["duplications"].append({
                    "type": "file",
                    "name": base_name,
                    "locations": paths,
                    "severity": "low"
                })
    
    def analyze_naming_conflicts(self):
        """Analyze naming conflicts"""
        print("  → Analyzing naming conflicts...")
        
        # Check for conflicting function names across different contexts
        mcp_functions = set()
        conductor_functions = set()
        
        for module_path, module_info in self.modules.items():
            for func in module_info["functions"]:
                if "mcp" in module_path:
                    mcp_functions.add(func["name"])
                elif "cherry_ait" in module_path:
                    conductor_functions.add(func["name"])
        
        # Find overlaps
        mcp_orch = mcp_functions & conductor_functions
        
        if mcp_orch:
            self.issues["naming_conflicts"].append({
                "type": "function_overlap",
                "components": ["MCP", "conductor"],
                "names": list(mcp_orch),
                "severity": "medium"
            })
        
        # Check for reserved name usage
        reserved_names = {"run", "start", "stop", "init", "setup", "config", "main"}
        for module_path, module_info in self.modules.items():
            for func in module_info["functions"]:
                if func["name"] in reserved_names:
                    component = self.identify_component(module_path)
                    if component:
                        self.issues["naming_conflicts"].append({
                            "type": "reserved_name",
                            "component": component,
                            "name": func["name"],
                            "location": module_path,
                            "severity": "low"
                        })
    
    def identify_component(self, path: str) -> str:
        """Identify which component a path belongs to"""
        if "mcp" in path:
            return "MCP"
        elif "cherry_ait" in path:
            return "conductor"
            return ""
        return "Core"
    
    def analyze_dependencies(self):
        """Analyze dependency issues"""
        print("  → Analyzing dependencies...")
        
        # Check for missing imports
        for module_path, module_info in self.modules.items():
            for import_name in module_info["imports"]:
                # Check if it's a local import
                if not import_name.startswith((".", "mcp", "ai_components", "agent", "core")):
                    continue
                    
                # Try to resolve the import
                if import_name.startswith("."):
                    # Relative import
                    base_path = Path(module_path).parent
                    import_parts = import_name.lstrip(".").split(".")
                    expected_path = base_path / "/".join(import_parts[:-1]) / f"{import_parts[-1]}.py"
                else:
                    # Absolute import
                    import_parts = import_name.split(".")
                    if not expected_path.exists():
                
                if not expected_path.exists():
                    self.issues["dependency_mismatches"].append({
                        "type": "missing_module",
                        "importer": module_path,
                        "import": import_name,
                        "severity": "high"
                    })
        
        # Check for version conflicts in requirements
        self.check_requirements_conflicts()
    
    def check_requirements_conflicts(self):
        """Check for version conflicts in requirements files"""
        all_deps = defaultdict(list)
        
        for req_file in requirements_files:
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        match = re.match(r'([a-zA-Z0-9-_]+)([><=~!]+.*)?', line)
                        if match:
                            pkg_name = match.group(1)
                            version_spec = match.group(2) or ""
        
        # Check for conflicts
        for pkg_name, specs in all_deps.items():
            if len(specs) > 1:
                unique_specs = set(spec for _, spec in specs)
                if len(unique_specs) > 1:
                    self.issues["version_conflicts"].append({
                        "package": pkg_name,
                        "specifications": [{"file": file, "spec": spec} for file, spec in specs],
                        "severity": "high"
                    })
    
    def analyze_configurations(self):
        """Analyze configuration consistency"""
        print("  → Analyzing configurations...")
        
        # Check for MCP server configurations
        mcp_config = self.configs.get(".mcp.json", {})
        conductor_config = self.configs.get("config/conductor_config.json", {})
        
        # Verify MCP servers are consistently defined
        if mcp_config and conductor_config:
            mcp_servers = set(mcp_config.get("servers", {}).keys())
            
            # Check for missing mode configurations
            expected_modes = {"code", "architect", "ask", "debug", "conductor", "strategy", 
                            "research", "analytics", "implementation", "quality", "documentation"}
            missing_modes = expected_modes - orch_modes
            
            if missing_modes:
                self.issues["config_inconsistencies"].append({
                    "type": "missing_modes",
                    "modes": list(missing_modes),
                    "severity": "medium"
                })
        
        # Check environment variable usage
        self.check_env_var_consistency()
    
    def check_env_var_consistency(self):
        """Check environment variable consistency"""
                env_matches = re.findall(r'os\.environ\.get\(["\']([^"\']+)["\']', content)
                env_vars_used.update(env_matches)
                env_matches = re.findall(r'os\.environ\[["\']([^"\']+)["\']', content)
                env_vars_used.update(env_matches)
        
        # Get defined env vars
        for config_path, config in self.configs.items():
            if config_path.startswith(".env"):
                env_vars_defined.update(config.keys())
        
        # Find undefined vars
        undefined_vars = env_vars_used - env_vars_defined
        if undefined_vars:
            self.issues["config_inconsistencies"].append({
                "type": "undefined_env_vars",
                "variables": list(undefined_vars),
                "severity": "high"
            })
    
    def analyze_integration_points(self):
        """Analyze integration points between components"""
        print("  → Analyzing integration points...")
        
        # Find MCP server implementations
        mcp_servers = []
        for module_path in self.modules:
            if "mcp_server/servers" in module_path and module_path.endswith("_server.py"):
                mcp_servers.append(module_path)
        
        # Check each MCP server for proper integration
        for server_path in mcp_servers:
            server_name = Path(server_path).stem
            module_info = self.modules[server_path]
            
            # Check for required methods
            required_methods = ["__init__", "setup_handlers", "run"]
            implemented_methods = [f["name"] for f in module_info["functions"]]
            
            missing_methods = set(required_methods) - set(implemented_methods)
            if missing_methods:
                self.issues["integration_issues"].append({
                    "type": "incomplete_mcp_server",
                    "server": server_name,
                    "missing_methods": list(missing_methods),
                    "severity": "high"
                })
        
        # Check conductor integration
        self.check_conductor_integration()
    
    def check_conductor_integration(self):
        """Check conductor integration with MCP and """
        conductor_modules = [m for m in self.modules if "cherry_ait" in m]
        
        for module_path in conductor_modules:
            module_info = self.modules[module_path]
            
            # Check for MCP client usage
            has_mcp_import = any("mcp" in imp for imp in module_info["imports"])
            
            # Check for  mode handling
            with open(module_file, 'r') as f:
                content = f.read()
            
            if not has_mcp_import and "cli" not in module_path:
                self.issues["integration_issues"].append({
                    "type": "missing_mcp_integration",
                    "module": module_path,
                    "severity": "medium"
                })
    
    def analyze_error_handling(self):
        """Analyze error handling patterns"""
        print("  → Analyzing error handling...")
        
        for module_path, module_info in self.modules.items():
            with open(module_file, 'r') as f:
                content = f.read()
                
            # Count try-except blocks
            try_count = content.count("try:")
            except_count = content.count("except")
            
            # Check for bare excepts
            bare_except_count = len(re.findall(r'except\s*:', content))
            if bare_except_count > 0:
                self.issues["error_handling_issues"].append({
                    "type": "bare_except",
                    "module": module_path,
                    "count": bare_except_count,
                    "severity": "medium"
                })
            
            # Check for missing error handling in async functions
            async_funcs = re.findall(r'async\s+def\s+(\w+)', content)
            for func_name in async_funcs:
                # Simple heuristic: check if function has try-except
                func_match = re.search(rf'async\s+def\s+{func_name}.*?(?=\nasync\s+def|\ndef|\nclass|\Z)', content, re.DOTALL)
                if func_match:
                    func_body = func_match.group(0)
                    if "await" in func_body and "try:" not in func_body:
                        self.issues["error_handling_issues"].append({
                            "type": "unprotected_await",
                            "module": module_path,
                            "function": func_name,
                            "severity": "low"
                        })
    
    def analyze_coding_patterns(self):
        """Analyze coding pattern consistency"""
        print("  → Analyzing coding patterns...")
        
        patterns = {
            "string_quotes": {"single": 0, "double": 0},
            "class_naming": {"PascalCase": 0, "other": 0},
            "function_naming": {"snake_case": 0, "camelCase": 0, "other": 0}
        }
        
        for module_path, module_info in self.modules.items():
            with open(module_file, 'r') as f:
                content = f.read()
            
            # Check string quotes
            patterns["string_quotes"]["single"] += len(re.findall(r"'[^']*'", content))
            patterns["string_quotes"]["double"] += len(re.findall(r'"[^"]*"', content))
            
            # Check naming conventions
            for class_info in module_info["classes"]:
                if re.match(r'^[A-Z][a-zA-Z0-9]*$', class_info["name"]):
                    patterns["class_naming"]["PascalCase"] += 1
                else:
                    patterns["class_naming"]["other"] += 1
            
            for func_info in module_info["functions"]:
                if re.match(r'^[a-z_][a-z0-9_]*$', func_info["name"]):
                    patterns["function_naming"]["snake_case"] += 1
                elif re.match(r'^[a-z][a-zA-Z0-9]*$', func_info["name"]):
                    patterns["function_naming"]["camelCase"] += 1
                else:
                    patterns["function_naming"]["other"] += 1
        
        # Report inconsistencies
        if patterns["string_quotes"]["single"] > 0 and patterns["string_quotes"]["double"] > 0:
            ratio = patterns["string_quotes"]["single"] / patterns["string_quotes"]["double"]
            if ratio < 0.2 or ratio > 5:
                self.issues["pattern_inconsistencies"].append({
                    "type": "mixed_quotes",
                    "single_count": patterns["string_quotes"]["single"],
                    "double_count": patterns["string_quotes"]["double"],
                    "severity": "low"
                })
    
    def analyze_api_contracts(self):
        """Analyze API contract consistency"""
        print("  → Analyzing API contracts...")
        
        # Find all API endpoints
        api_endpoints = defaultdict(list)
        
        for module_path, module_info in self.modules.items():
            if "router" in module_path or "api" in module_path:
                with open(module_file, 'r') as f:
                    content = f.read()
                
                # Find FastAPI/Flask routes
                route_patterns = [
                    r'@\w+\.(?:get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                    r'@app\.route\(["\']([^"\']+)["\']'
                ]
                
                for pattern in route_patterns:
                    routes = re.findall(pattern, content)
                    for route in routes:
                        api_endpoints[route].append(module_path)
        
        # Check for duplicate endpoints
        for endpoint, modules in api_endpoints.items():
            if len(modules) > 1:
                self.issues["api_contract_violations"].append({
                    "type": "duplicate_endpoint",
                    "endpoint": endpoint,
                    "modules": modules,
                    "severity": "high"
                })
    
    def validate_circular_dependencies(self):
        """Validate for circular dependencies"""
        print("  → Validating circular dependencies...")
        
        # Build dependency graph
        dep_graph = defaultdict(set)
        for module_path, module_info in self.modules.items():
            for imp in module_info["imports"]:
                if imp.startswith((".", "mcp", "ai_components", "agent", "core")):
                    dep_graph[module_path].add(imp)
        
        # DFS to find cycles
        def find_cycle(node, visited, rec_stack, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dep_graph.get(node, []):
                if neighbor not in visited:
                    cycle = find_cycle(neighbor, visited, rec_stack, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:]
            
            path.pop()
            rec_stack.remove(node)
            return None
        
        visited = set()
        for node in dep_graph:
            if node not in visited:
                rec_stack = set()
                cycle = find_cycle(node, visited, rec_stack, [])
                if cycle:
                    self.issues["circular_dependencies"].append({
                        "cycle": cycle,
                        "severity": "critical"
                    })
    
    def validate_version_compatibility(self):
        """Validate version compatibility"""
        print("  → Validating version compatibility...")
        
        # Check Python version requirements
        python_versions = set()
            with open(req_file, 'r') as f:
                for line in f:
                    if "python_version" in line:
                        match = re.search(r'python_version[><=~!]+([0-9.]+)', line)
                        if match:
                            python_versions.add(match.group(1))
        
        if len(python_versions) > 1:
            self.issues["version_conflicts"].append({
                "type": "python_version",
                "versions": list(python_versions),
                "severity": "high"
            })
    
    def validate_runtime_safety(self):
        """Validate runtime safety"""
        print("  → Validating runtime safety...")
        
        # Check for common runtime issues
        for module_path, module_info in self.modules.items():
            with open(module_file, 'r') as f:
                content = f.read()
            
            # Check for eval/exec usage
            if "ast.literal_eval(" in content or "# SECURITY: exec() removed - " in content:
                self.issues["runtime_errors"].append({
                    "type": "unsafe_eval",
                    "module": module_path,
                    "severity": "high"
                }
            
            # Check for hardcoded secrets
            secret_patterns = [
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'password\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']'
            ]
            
            for pattern in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    self.issues["runtime_errors"].append({
                        "type": "hardcoded_secret",
                        "module": module_path,
                        "severity": "critical"
                    })
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n📊 AUDIT REPORT")
        print("="*60)
        
        total_issues = sum(len(issues) for issues in self.issues.values())
        critical_count = sum(1 for issues in self.issues.values() for issue in issues if issue.get("severity") == "critical")
        high_count = sum(1 for issues in self.issues.values() for issue in issues if issue.get("severity") == "high")
        
        print(f"\nTotal Issues Found: {total_issues}")
        print(f"  • Critical: {critical_count}")
        print(f"  • High: {high_count}")
        print(f"  • Medium: {sum(1 for issues in self.issues.values() for issue in issues if issue.get('severity') == 'medium')}")
        print(f"  • Low: {sum(1 for issues in self.issues.values() for issue in issues if issue.get('severity') == 'low')}")
        
        # Detailed breakdown
        for category, issues in self.issues.items():
            if issues:
                print(f"\n{category.upper().replace('_', ' ')} ({len(issues)} issues):")
                for issue in issues[:3]:  # Show first 3
                    print(f"  • {issue}")
                if len(issues) > 3:
                    print(f"  ... and {len(issues) - 3} more")
        
        # Save full report
        from datetime import datetime
        with open(report_path, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_issues": total_issues,
                    "critical": critical_count,
                    "high": high_count,
                    "modules_analyzed": len(self.modules),
                    "configs_analyzed": len(self.configs)
                },
                "issues": self.issues
            }, f, indent=2)
        
        print(f"\n✓ Full report saved to: {report_path}")
    
    def propose_fixes(self):
        """Propose fixes for identified issues"""
        print("\n🔧 PROPOSED FIXES")
        print("="*60)
        
        fixes = []
        
        # Fix duplications
        if self.issues["duplications"]:
            fixes.append({
                "category": "Code Duplication",
                "action": "Consolidate duplicate functions into shared modules",
                "files_to_create": ["core/shared_utils.py", "core/shared_validators.py"],
                "priority": "high"
            })
        
        # Fix naming conflicts
        if self.issues["naming_conflicts"]:
            fixes.append({
                "category": "Naming Conflicts",
                "action": "Implement component-specific naming prefixes",
                "changes": {
                    "MCP functions": "Prefix with 'mcp_'",
                    "conductor functions": "Prefix with 'orch_'",
                    " functions": "Keep current naming"
                },
                "priority": "medium"
            })
        
        # Fix missing dependencies
        if self.issues["dependency_mismatches"]:
            fixes.append({
                "category": "Dependencies",
                "action": "Create missing __init__.py files and fix imports",
                "commands": [
                    "touch mcp_server/__init__.py",
                    "touch ai_components/__init__.py",
                    "touch agent/app/__init__.py"
                ],
                "priority": "high"
            })
        
        # Fix configuration
        if self.issues["config_inconsistencies"]:
            fixes.append({
                "category": "Configuration",
                "action": "Synchronize configurations across components",
                "tasks": [
                    "Update .env.example with all required variables",
                    "Ensure MCP server configs match conductor modes",
                    "Add missing environment variables"
                ],
                "priority": "high"
            })
        
        # Fix error handling
        if self.issues["error_handling_issues"]:
            fixes.append({
                "category": "Error Handling",
                "action": "Implement consistent error handling patterns",
                "pattern": "Use specific exceptions and proper logging",
                "priority": "medium"
            })
        
        # Print fixes
        for fix in fixes:
            print(f"\n{fix['category']}:")
            print(f"  Action: {fix['action']}")
            print(f"  Priority: {fix['priority']}")
            if "commands" in fix:
                print("  Commands to run:")
                for cmd in fix["commands"]:
                    print(f"    $ {cmd}")
        
        # Create fix script
        self.create_fix_script(fixes)
    
    def create_fix_script(self, fixes):
        """Create automated fix script"""
        with open(fix_script_path, 'w') as f:
            f.write('''
'''