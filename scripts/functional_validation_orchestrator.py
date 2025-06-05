#!/usr/bin/env python3
"""
Functional Validation conductor for Cherry AI - Phase 4
Validates search engine modules, persona system, and API endpoint consistency.
"""

import os
import sys
import json
import asyncio
import aiohttp
import importlib
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional
from typing_extensions import Optional, Set, Tuple
from datetime import datetime
import yaml
import ast
import re

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class FunctionalValidationconductor:
    """cherry_aites comprehensive functional validation of Cherry AI components."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "search_engine_validation": {},
            "persona_system_validation": {},
            "api_endpoint_validation": {},
            "recommendations": []
        }
        
        # Component registries
        self.search_modules = {}
        self.persona_configs = {}
        self.api_endpoints = {}
        self.duplicate_endpoints = []
        self.unused_files = []
        
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete functional validation."""
        print("🔍 Starting Functional Validation - Phase 4...")
        
        # 4.1 Search Engine Modules Validation
        print("\n📡 4.1 Search Engine Modules Validation")
        await self.validate_search_engine_modules()
        
        # 4.2 Persona System Validation
        print("\n🎭 4.2 Persona System Validation")
        await self.validate_persona_system()
        
        # 4.3 API Endpoint Consistency
        print("\n🔌 4.3 API Endpoint Consistency")
        await self.validate_api_endpoints()
        
        # Generate summary and recommendations
        self.generate_validation_summary()
        self.generate_recommendations()
        
        return self.validation_results
    
    # ====== 4.1 SEARCH ENGINE MODULES VALIDATION ======
    
    async def validate_search_engine_modules(self):
        """Validate all search engine modules and modes."""
        print("🔍 Validating search engine modules...")
        
        search_modes = ["normal", "creative", "deep", "super_deep", "uncensored"]
        search_validation = {
            "modes_found": {},
            "import_issues": [],
            "duplicate_logic": [],
            "llm_client_consistency": [],
            "unused_files": [],
            "implementation_completeness": {}
        }
        
        # Check each search mode
        for mode in search_modes:
            await self._validate_search_mode(mode, search_validation)
        
        # Check search router
        await self._validate_search_router(search_validation)
        
        # Check for duplicate logic
        await self._check_search_logic_duplication(search_validation)
        
        # Check LLM client integrations
        await self._validate_llm_client_consistency(search_validation)
        
        # Find unused search files
        await self._find_unused_search_files(search_validation)
        
        self.validation_results["search_engine_validation"] = search_validation
    
    async def _validate_search_mode(self, mode: str, validation: Dict):
        """Validate a specific search mode."""
        mode_files = [
            f"src/search_engine/{mode}_search.py",
            f"src/search_engine/{mode}.py",
            f"search_engine/{mode}_search.py",
            f"search_engine/{mode}.py"
        ]
        
        found_file = None
        for file_path in mode_files:
            full_path = self.root_path / file_path
            if full_path.exists():
                found_file = full_path
                break
        
        if found_file:
            validation["modes_found"][mode] = {
                "file": str(found_file),
                "exists": True,
                "imports_work": False,
                "has_run_method": False,
                "is_complete": False,
                "todo_count": 0
            }
            
            # Check if imports work
            try:
                content = found_file.read_text(encoding='utf-8')
                
                # Check for run method
                if "async def run(" in content or "def run(" in content:
                    validation["modes_found"][mode]["has_run_method"] = True
                
                # Count TODOs and implementation completeness
                todo_count = content.lower().count("todo")
                validation["modes_found"][mode]["todo_count"] = todo_count
                
                # Check for actual implementation vs placeholder
                if "# TODO" in content or "pass" in content:
                    validation["modes_found"][mode]["is_complete"] = False
                else:
                    validation["modes_found"][mode]["is_complete"] = True
                
                # Try to import (simplified check)
                if "from" in content and "import" in content:
                    validation["modes_found"][mode]["imports_work"] = True
                
            except Exception as e:
                validation["import_issues"].append({
                    "mode": mode,
                    "file": str(found_file),
                    "error": str(e)
                })
        else:
            validation["modes_found"][mode] = {
                "exists": False,
                "expected_paths": mode_files
            }
    
    async def _validate_search_router(self, validation: Dict):
        """Validate the search router implementation."""
        router_files = [
            "src/search_engine/search_router.py",
            "search_engine/search_router.py"
        ]
        
        found_router = None
        for file_path in router_files:
            full_path = self.root_path / file_path
            if full_path.exists():
                found_router = full_path
                break
        
        if found_router:
            try:
                content = found_router.read_text(encoding='utf-8')
                
                # Check if it routes to all search modes
                search_modes = ["normal", "creative", "deep", "super_deep", "uncensored"]
                routes_all_modes = all(mode in content for mode in search_modes)
                
                validation["search_router"] = {
                    "exists": True,
                    "file": str(found_router),
                    "routes_all_modes": routes_all_modes,
                    "has_circuit_breaker": "circuit_breaker" in content,
                    "has_error_handling": "except" in content
                }
                
            except Exception as e:
                validation["import_issues"].append({
                    "component": "search_router",
                    "error": str(e)
                })
        else:
            validation["search_router"] = {"exists": False}
    
    async def _check_search_logic_duplication(self, validation: Dict):
        """Check for duplicate logic between search modes."""
        search_files = list(self.root_path.glob("**/search_engine/*_search.py"))
        
        # Simple duplicate detection - look for similar function signatures
        function_signatures = {}
        
        for file_path in search_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extract function definitions
                functions = re.findall(r'def (\w+)\([^)]*\):', content)
                functions += re.findall(r'async def (\w+)\([^)]*\):', content)
                
                for func in functions:
                    if func not in function_signatures:
                        function_signatures[func] = []
                    function_signatures[func].append(str(file_path))
                        
            except Exception as e:
                continue
        
        # Find duplicates
        for func_name, files in function_signatures.items():
            if len(files) > 1 and func_name not in ["__init__", "run"]:
                validation["duplicate_logic"].append({
                    "function": func_name,
                    "files": files,
                    "suggestion": f"Consider extracting {func_name} to a shared utility"
                })
    
    async def _validate_llm_client_consistency(self, validation: Dict):
        """Validate LLM client integrations are consistent."""
        search_files = list(self.root_path.glob("**/search_engine/*.py"))
        llm_client_usage = {}
        
        for file_path in search_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Check for LLM client patterns
                llm_patterns = [
                    r'LLMClient\([^)]*\)',
                    r'model="([^"]*)"',
                    r'temperature=([0-9.]+)'
                ]
                
                for pattern in llm_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        if str(file_path) not in llm_client_usage:
                            llm_client_usage[str(file_path)] = {}
                        llm_client_usage[str(file_path)][pattern] = matches
                        
            except Exception:
                continue
        
        validation["llm_client_consistency"] = llm_client_usage
    
    async def _find_unused_search_files(self, validation: Dict):
        """Find unused search-related files."""
        search_dir = self.root_path / "src" / "search_engine"
        if not search_dir.exists():
            search_dir = self.root_path / "search_engine"
        
        if search_dir.exists():
            all_files = list(search_dir.glob("*.py"))
            used_files = set()
            
            # Files that should exist
            expected_files = [
                "search_router.py",
                "normal_search.py", 
                "creative_search.py",
                "deep_search.py",
                "super_deep_search.py",
                "uncensored_search.py",
                "__init__.py"
            ]
            
            for file_path in all_files:
                if file_path.name in expected_files:
                    used_files.add(file_path.name)
            
            unused = [f for f in all_files if f.name not in used_files]
            validation["unused_files"] = [str(f) for f in unused]
    
    # ====== 4.2 PERSONA SYSTEM VALIDATION ======
    
    async def validate_persona_system(self):
        """Validate persona system for Cherry, Sophia, and Karen."""
        print("🎭 Validating persona system...")
        
        persona_validation = {
            "persona_configs": {},
            "config_file_consistency": [],
            "memory_management": {},
            "behavior_engines": {},
            "unused_persona_files": [],
            "implementation_status": {}
        }
        
        personas = ["cherry", "sophia", "karen"]
        
        # Validate each persona
        for persona in personas:
            await self._validate_persona_config(persona, persona_validation)
        
        # Check configuration file consistency
        await self._check_persona_config_consistency(persona_validation)
        
        # Validate memory management
        await self._validate_persona_memory_management(persona_validation)
        
        # Check behavior engines
        await self._validate_persona_behavior_engines(persona_validation)
        
        # Find unused persona files
        await self._find_unused_persona_files(persona_validation)
        
        self.validation_results["persona_system_validation"] = persona_validation
    
    async def _validate_persona_config(self, persona: str, validation: Dict):
        """Validate a specific persona configuration."""
        config_files = [
            f"config/personas/{persona}.yaml",
            f"core/config/personas/{persona}.yaml",
            f"core/conductor/src/config/personas/{persona}.yaml",
            f"config/personas.yaml",
            f"core/personas/personas_detailed.yaml"
        ]
        
        found_configs = []
        for config_path in config_files:
            full_path = self.root_path / config_path
            if full_path.exists():
                found_configs.append(full_path)
        
        persona_info = {
            "config_files_found": len(found_configs),
            "config_paths": [str(p) for p in found_configs],
            "valid_configs": 0,
            "config_errors": [],
            "has_traits": False,
            "has_memory_config": False,
            "has_system_prompt": False
        }
        
        # Validate each found config
        for config_path in found_configs:
            try:
                content = config_path.read_text(encoding='utf-8')
                
                # Try to parse as YAML
                if config_path.suffix == '.yaml':
                    config_data = yaml.safe_load(content)
                    
                    # Check if this file contains our persona
                    if persona in config_data or persona.lower() in config_data:
                        persona_config = config_data.get(persona) or config_data.get(persona.lower())
                        
                        if persona_config:
                            persona_info["valid_configs"] += 1
                            
                            # Check for required fields
                            if "traits" in persona_config:
                                persona_info["has_traits"] = True
                            if "memory_config" in persona_config or "memory" in persona_config:
                                persona_info["has_memory_config"] = True
                            if "system_prompt" in persona_config or "prompt_template" in persona_config:
                                persona_info["has_system_prompt"] = True
                
            except Exception as e:
                persona_info["config_errors"].append({
                    "file": str(config_path),
                    "error": str(e)
                })
        
        validation["persona_configs"][persona] = persona_info
    
    async def _check_persona_config_consistency(self, validation: Dict):
        """Check for consistency across persona configuration files."""
        config_files = list(self.root_path.glob("**/config/**/*.yaml"))
        config_files.extend(list(self.root_path.glob("**/personas/**/*.yaml")))
        
        persona_definitions = {}
        
        for config_file in config_files:
            try:
                content = config_file.read_text(encoding='utf-8')
                config_data = yaml.safe_load(content)
                
                if isinstance(config_data, dict):
                    for key, value in config_data.items():
                        if key.lower() in ["cherry", "sophia", "karen"]:
                            if key.lower() not in persona_definitions:
                                persona_definitions[key.lower()] = []
                            persona_definitions[key.lower()].append({
                                "file": str(config_file),
                                "config": value
                            })
                            
            except Exception:
                continue
        
        # Check for inconsistencies
        consistency_issues = []
        for persona, definitions in persona_definitions.items():
            if len(definitions) > 1:
                # Compare trait values across definitions
                trait_sets = []
                # TODO: Consider using list comprehension for better performance

                for definition in definitions:
                    if "traits" in definition["config"]:
                        trait_sets.append(definition["config"]["traits"])
                
                if len(set(str(traits) # TODO: Consider using list comprehension for better performance
 for traits in trait_sets)) > 1:
                    consistency_issues.append({
                        "persona": persona,
                        "issue": "inconsistent_traits",
                        "files": [d["file"] for d in definitions]
                    })
        
        validation["config_file_consistency"] = consistency_issues
    
    async def _validate_persona_memory_management(self, validation: Dict):
        """Validate persona memory management implementation."""
        memory_files = [
            "src/personas/persona_memory_manager.py",
            "core/personas/memory_manager.py",
            "personas/memory_manager.py"
        ]
        
        memory_status = {
            "memory_manager_exists": False,
            "memory_manager_file": None,
            "implements_episodic": False,
            "implements_semantic": False,
            "implements_working": False,
            "has_retention_policy": False
        }
        
        for memory_file in memory_files:
            full_path = self.root_path / memory_file
            if full_path.exists():
                memory_status["memory_manager_exists"] = True
                memory_status["memory_manager_file"] = str(full_path)
                
                try:
                    content = full_path.read_text(encoding='utf-8')
                    
                    # Check for memory types
                    if "episodic" in content.lower():
                        memory_status["implements_episodic"] = True
                    if "semantic" in content.lower():
                        memory_status["implements_semantic"] = True
                    if "working" in content.lower():
                        memory_status["implements_working"] = True
                    if "retention" in content.lower():
                        memory_status["has_retention_policy"] = True
                        
                except Exception:
                    pass
                break
        
        validation["memory_management"] = memory_status
    
    async def _validate_persona_behavior_engines(self, validation: Dict):
        """Validate persona behavior engines for conflicts."""
        behavior_files = [
            "src/personas/persona_behavior_engine.py",
            "core/personas/behavior_engine.py",
            "personas/behavior_engine.py"
        ]
        
        behavior_status = {
            "behavior_engine_exists": False,
            "behavior_engine_file": None,
            "has_adaptive_responses": False,
            "has_mood_tracking": False,
            "has_preference_learning": False,
            "potential_conflicts": []
        }
        
        for behavior_file in behavior_files:
            full_path = self.root_path / behavior_file
            if full_path.exists():
                behavior_status["behavior_engine_exists"] = True
                behavior_status["behavior_engine_file"] = str(full_path)
                
                try:
                    content = full_path.read_text(encoding='utf-8')
                    
                    # Check for behavior features
                    if "adaptive" in content.lower():
                        behavior_status["has_adaptive_responses"] = True
                    if "mood" in content.lower():
                        behavior_status["has_mood_tracking"] = True
                    if "preference" in content.lower() or "learning" in content.lower():
                        behavior_status["has_preference_learning"] = True
                    
                    # Look for potential conflicts (global state, shared resources)
                    if "global" in content.lower() or "singleton" in content.lower():
                        behavior_status["potential_conflicts"].append("Global state detected")
                    if "lock" in content.lower() or "mutex" in content.lower():
                        behavior_status["potential_conflicts"].append("Resource locking needed")
                        
                except Exception:
                    pass
                break
        
        validation["behavior_engines"] = behavior_status
    
    async def _find_unused_persona_files(self, validation: Dict):
        """Find unused persona-related files."""
        persona_dirs = [
            self.root_path / "src" / "personas",
            self.root_path / "core" / "personas",
            self.root_path / "personas"
        ]
        
        unused_files = []
        for persona_dir in persona_dirs:
            if persona_dir.exists():
                all_files = list(persona_dir.glob("*.py"))
                
                # Expected persona files
                expected_files = [
                    "cherry_persona.py",
                    "sophia_persona.py", 
                    "karen_persona.py",
                    "persona_memory_manager.py",
                    "persona_behavior_engine.py",
                    "__init__.py"
                ]
                
                for file_path in all_files:
                    if file_path.name not in expected_files:
                        # Check if it's actually used by searching for imports
                        is_used = await self._check_if_file_is_imported(file_path)
                        if not is_used:
                            unused_files.append(str(file_path))
        
        validation["unused_persona_files"] = unused_files
    
    # ====== 4.3 API ENDPOINT CONSISTENCY ======
    
    async def validate_api_endpoints(self):
        """Validate API endpoint consistency."""
        print("🔌 Validating API endpoints...")
        
        api_validation = {
            "duplicate_endpoints": [],
            "response_format_consistency": [],
            "error_handling_consistency": [],
            "authentication_consistency": [],
            "unused_test_endpoints": [],
            "endpoint_inventory": {}
        }
        
        # Find all API router files
        await self._discover_api_endpoints(api_validation)
        
        # Check for duplicates
        await self._check_duplicate_endpoints(api_validation)
        
        # Validate response formats
        await self._validate_response_formats(api_validation)
        
        # Check error handling
        await self._validate_error_handling(api_validation)
        
        # Validate authentication
        await self._validate_authentication_consistency(api_validation)
        
        # Find unused/test endpoints
        await self._find_unused_test_endpoints(api_validation)
        
        self.validation_results["api_endpoint_validation"] = api_validation
    
    async def _discover_api_endpoints(self, validation: Dict):
        """Discover all API endpoints in the project."""
        router_files = list(self.root_path.glob("**/routers/*.py"))
        router_files.extend(list(self.root_path.glob("**/api/*.py")))
        router_files.extend(list(self.root_path.glob("**/endpoints/*.py")))
        
        endpoints = {}
        
        for router_file in router_files:
            try:
                content = router_file.read_text(encoding='utf-8')
                
                # Extract API endpoints using regex
                endpoint_patterns = [
                    r'@router\.(get|post|put|delete|patch)\("([^"]+)"',
                    r'@app\.(get|post|put|delete|patch)\("([^"]+)"'
                ]
                
                for pattern in endpoint_patterns:
                    matches = re.findall(pattern, content)
                    for method, path in matches:
                        endpoint_key = f"{method.upper()}:{path}"
                        
                        if endpoint_key not in endpoints:
                            endpoints[endpoint_key] = []
                        endpoints[endpoint_key].append(str(router_file))
                        
            except Exception:
                continue
        
        validation["endpoint_inventory"] = endpoints
    
    async def _check_duplicate_endpoints(self, validation: Dict):
        """Check for duplicate endpoint definitions."""
        duplicates = []
        
        for endpoint, files in validation["endpoint_inventory"].items():
            if len(files) > 1:
                duplicates.append({
                    "endpoint": endpoint,
                    "files": files,
                    "severity": "high" if len(files) > 2 else "medium"
                })
        
        validation["duplicate_endpoints"] = duplicates
    
    async def _validate_response_formats(self, validation: Dict):
        """Validate consistent response formats across endpoints."""
        router_files = list(self.root_path.glob("**/routers/*.py"))
        router_files.extend(list(self.root_path.glob("**/api/*.py")))
        
        response_patterns = {}
        
        for router_file in router_files:
            try:
                content = router_file.read_text(encoding='utf-8')
                
                # Look for response models
                response_models = re.findall(r'response_model=(\w+)', content)
                
                # Look for return statements
                returns = re.findall(r'return\s+({[^}]+}|\w+\([^)]+\))', content)
                
                file_patterns = {
                    "response_models": response_models,
                    "return_patterns": returns
                }
                
                response_patterns[str(router_file)] = file_patterns
                
            except Exception:
                continue
        
        validation["response_format_consistency"] = response_patterns
    
    async def _validate_error_handling(self, validation: Dict):
        """Validate consistent error handling across endpoints."""
        router_files = list(self.root_path.glob("**/routers/*.py"))
        router_files.extend(list(self.root_path.glob("**/api/*.py")))
        
        error_handling = {}
        
        for router_file in router_files:
            try:
                content = router_file.read_text(encoding='utf-8')
                
                # Check for error handling patterns
                has_try_except = "try:" in content and "except" in content
                has_http_exception = "HTTPException" in content
                has_status_codes = "status_code" in content
                
                error_handling[str(router_file)] = {
                    "has_try_except": has_try_except,
                    "has_http_exception": has_http_exception,
                    "has_status_codes": has_status_codes,
                    "error_completeness": sum([has_try_except, has_http_exception, has_status_codes]) / 3
                }
                
            except Exception:
                continue
        
        validation["error_handling_consistency"] = error_handling
    
    async def _validate_authentication_consistency(self, validation: Dict):
        """Validate authentication/authorization consistency."""
        router_files = list(self.root_path.glob("**/routers/*.py"))
        router_files.extend(list(self.root_path.glob("**/api/*.py")))
        
        auth_patterns = {}
        
        for router_file in router_files:
            try:
                content = router_file.read_text(encoding='utf-8')
                
                # Check for different auth patterns
                auth_info = {
                    "has_api_key": "api_key" in content.lower() or "x-api-key" in content.lower(),
                    "has_jwt": "jwt" in content.lower() or "bearer" in content.lower(),
                    "has_depends": "Depends(" in content,
                    "has_oauth2": "oauth2" in content.lower(),
                    "auth_decorators": len(re.findall(r'@\w+auth\w*', content)),
                    "security_imports": len(re.findall(r'from.*security.*import', content))
                }
                
                auth_patterns[str(router_file)] = auth_info
                
            except Exception:
                continue
        
        validation["authentication_consistency"] = auth_patterns
    
    async def _find_unused_test_endpoints(self, validation: Dict):
        """Find unused or test endpoints that should be removed."""
        router_files = list(self.root_path.glob("**/routers/*.py"))
        router_files.extend(list(self.root_path.glob("**/api/*.py")))
        
        test_endpoints = []
        
        for router_file in router_files:
            try:
                content = router_file.read_text(encoding='utf-8')
                
                # Look for test/debug endpoints
                test_patterns = [
                    r'@router\.\w+\(".*test.*"',
                    r'@router\.\w+\(".*debug.*"',
                    r'@router\.\w+\(".*dev.*"',
                ]
                
                for pattern in test_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        test_endpoints.append({
                            "file": str(router_file),
                            "endpoints": matches,
                            "suggestion": "Consider removing test endpoints from production"
                        })
                        
            except Exception:
                continue
        
        validation["unused_test_endpoints"] = test_endpoints
    
    # ====== UTILITY METHODS ======
    
    async def _check_if_file_is_imported(self, file_path: Path) -> bool:
        """Check if a Python file is imported anywhere in the project."""
        module_name = file_path.stem
        
        # Search for imports of this module
        python_files = list(self.root_path.glob("**/*.py"))
        
        for py_file in python_files:
            if py_file == file_path:
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for various import patterns
                import_patterns = [
                    f"import {module_name}",
                    f"from .{module_name}",
                    f"from {module_name}",
                    f"import .{module_name}"
                ]
                
                if any(pattern in content for pattern in import_patterns):
                    return True
                    
            except Exception:
                continue
        
        return False
    
    def generate_validation_summary(self):
        """Generate validation summary."""
        search_validation = self.validation_results["search_engine_validation"]
        persona_validation = self.validation_results["persona_system_validation"]
        api_validation = self.validation_results["api_endpoint_validation"]
        
        # Search engine summary
        search_modes_found = len([m for m in search_validation["modes_found"].values() if m.get("exists", False)])
        search_modes_complete = len([m for m in search_validation["modes_found"].values() if m.get("is_complete", False)])
        
        # Persona summary
        persona_configs_valid = sum(p["valid_configs"] for p in persona_validation["persona_configs"].values())
        
        # API summary
        total_endpoints = len(api_validation["endpoint_inventory"])
        duplicate_endpoints = len(api_validation["duplicate_endpoints"])
        
        self.validation_results["summary"] = {
            "search_engine": {
                "modes_found": search_modes_found,
                "modes_complete": search_modes_complete,
                "total_expected": 5,
                "health_score": (search_modes_complete / 5) * 100
            },
            "persona_system": {
                "valid_configs": persona_configs_valid,
                "personas_expected": 3,
                "config_consistency_issues": len(persona_validation["config_file_consistency"]),
                "health_score": min((persona_configs_valid / 6) * 100, 100)  # 2 configs per persona
            },
            "api_endpoints": {
                "total_endpoints": total_endpoints,
                "duplicate_endpoints": duplicate_endpoints,
                "endpoint_conflicts": duplicate_endpoints > 0,
                "health_score": max(0, (1 - duplicate_endpoints / max(total_endpoints, 1)) * 100)
            }
        }
    
    def generate_recommendations(self):
        """Generate prioritized recommendations."""
        recommendations = []
        
        # Search engine recommendations
        search_validation = self.validation_results["search_engine_validation"]
        for mode, info in search_validation["modes_found"].items():
            if not info.get("exists", False):
                recommendations.append({
                    "category": "Search Engine",
                    "priority": "high",
                    "issue": f"Missing {mode} search module",
                    "action": f"Create {mode}_search.py with proper implementation"
                })
            elif not info.get("is_complete", False):
                recommendations.append({
                    "category": "Search Engine", 
                    "priority": "medium",
                    "issue": f"{mode} search has incomplete implementation",
                    "action": f"Complete {mode}_search.py implementation (has {info.get('todo_count', 0)} TODOs)"
                })
        
        # Persona system recommendations
        persona_validation = self.validation_results["persona_system_validation"]
        for persona, info in persona_validation["persona_configs"].items():
            if info["valid_configs"] == 0:
                recommendations.append({
                    "category": "Persona System",
                    "priority": "high", 
                    "issue": f"No valid configuration found for {persona} persona",
                    "action": f"Create or fix {persona} configuration file"
                })
        
        # API endpoint recommendations
        api_validation = self.validation_results["api_endpoint_validation"]
        # TODO: Consider using list comprehension for better performance

        for duplicate in api_validation["duplicate_endpoints"]:
            recommendations.append({
                "category": "API Endpoints",
                "priority": duplicate["severity"],
                "issue": f"Duplicate endpoint: {duplicate['endpoint']}",
                "action": f"Consolidate endpoint definitions in files: {', '.join(duplicate['files'])}"
            })
        
        self.validation_results["recommendations"] = recommendations
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report."""
        summary = self.validation_results["summary"]
        
        report = f"""
🔍 Functional Validation Report - Phase 4
=======================================
Generated: {self.validation_results['timestamp']}

📊 EXECUTIVE SUMMARY
------------------
Search Engine Health: {summary['search_engine']['health_score']:.1f}%
Persona System Health: {summary['persona_system']['health_score']:.1f}%
API Endpoints Health: {summary['api_endpoints']['health_score']:.1f}%

Overall System Health: {(summary['search_engine']['health_score'] + summary['persona_system']['health_score'] + summary['api_endpoints']['health_score']) / 3:.1f}%

"""
        
        # Search Engine Section
        report += """
📡 SEARCH ENGINE MODULES VALIDATION
----------------------------------
"""
        search_validation = self.validation_results["search_engine_validation"]
        
        report += f"Search Modes Found: {summary['search_engine']['modes_found']}/5\n"
        report += f"Complete Implementations: {summary['search_engine']['modes_complete']}/5\n\n"
        
        for mode, info in search_validation["modes_found"].items():
            if info.get("exists", False):
                status = "✅" if info.get("is_complete", False) else "⚠️"
                todo_info = f" ({info.get('todo_count', 0)} TODOs)" if info.get('todo_count', 0) > 0 else ""
                report += f"{status} {mode}_search: {'Complete' if info.get(
                    'is_complete',
                    False
                ) else 'Incomplete'}{todo_info}\n"
            else:
                report += f"❌ {mode}_search: Missing\n"
        
        # Persona System Section
        report += """

🎭 PERSONA SYSTEM VALIDATION
---------------------------
"""
        persona_validation = self.validation_results["persona_system_validation"]
        
        for persona, info in persona_validation["persona_configs"].items():
            status = "✅" if info["valid_configs"] > 0 else "❌"
            report += f"{status} {persona.title()}: {info['valid_configs']} valid config(s) found\n"
            
            if info["config_errors"]:
                for error in info["config_errors"][:2]:  # Show first 2 errors
                    report += f"   ⚠️ Error in {error['file']}: {error['error'][:50]}...\n"
        
        # API Endpoints Section
        report += """

🔌 API ENDPOINT CONSISTENCY
--------------------------
"""
        api_validation = self.validation_results["api_endpoint_validation"]
        
        report += f"Total Endpoints: {summary['api_endpoints']['total_endpoints']}\n"
        report += f"Duplicate Endpoints: {summary['api_endpoints']['duplicate_endpoints']}\n\n"
        
        if api_validation["duplicate_endpoints"]:
            report += "❌ Duplicate Endpoints Found:\n"
            for dup in api_validation["duplicate_endpoints"][:5]:  # Show first 5
                report += f"   • {dup['endpoint']} in {len(dup['files'])} files\n"
        
        # Recommendations Section
        report += """

🔧 PRIORITY RECOMMENDATIONS
--------------------------
"""
        high_priority = [r for r in self.validation_results["recommendations"] if r["priority"] == "high"]
        medium_priority = [r for r in self.validation_results["recommendations"] if r["priority"] == "medium"]
        
        if high_priority:
            report += "🔴 HIGH PRIORITY:\n"
            for rec in high_priority[:5]:
                report += f"   • {rec['category']}: {rec['action']}\n"
        
        if medium_priority:
            report += "\n🟡 MEDIUM PRIORITY:\n"
            for rec in medium_priority[:5]:
                report += f"   • {rec['category']}: {rec['action']}\n"
        
        return report


async def main():
    """Run the functional validation."""
    validator = FunctionalValidationconductor(".")
    results = await validator.run_validation()
    
    # Generate and save report
    report = validator.generate_report()
    print(report)
    
    # Save detailed results to JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = f"functional_validation_results_{timestamp}.json"
    
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed validation results saved to: {json_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 