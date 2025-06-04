# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Analyze codebase for domain separation readiness"""
        self.base_dir = Path("/root/cherry_ai-main")
        self.domains = {
            "Personal": {
                "keywords": ["personal", "user", "profile", "preference", "individual"],
                "patterns": ["user_", "personal_", "profile_", "individual_"],
                "files": [],
                "dependencies": set(),
                "issues": []
            },
            "PayReady": {
                "keywords": ["pay", "payment", "transaction", "billing", "invoice", "payready"],
                "patterns": ["pay_", "payment_", "billing_", "invoice_", "transaction_"],
                "files": [],
                "dependencies": set(),
                "issues": []
            },
            "ParagonRX": {
                "keywords": ["paragon", "rx", "prescription", "medical", "health", "pharma"],
                "patterns": ["paragon_", "rx_", "medical_", "health_", "prescription_"],
                "files": [],
                "dependencies": set(),
                "issues": []
            }
        }
        self.shared_components = []
        self.cross_domain_dependencies = []
        self.refactoring_checklist = []
        
    def analyze_file_content(self, file_path):
        """Analyze file content for domain-specific code"""
                for keyword in info["keywords"]:
                    score += len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))
                # Check patterns
                for pattern in info["patterns"]:
                    score += len(re.findall(pattern, content, re.IGNORECASE))
                domain_scores[domain] = score
            
            # Assign to domain with highest score
            if max(domain_scores.values()) > 0:
                primary_domain = max(domain_scores, key=domain_scores.get)
                return primary_domain, domain_scores
            
            return None, domain_scores
            
        except Exception:

            
            pass
            return None, {}
    
    def analyze_imports(self, file_path):
        """Analyze Python imports to identify dependencies"""
                r'__import__\(["\'](\S+)["\']\)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.update(matches)
                
        except Exception:

                
            pass
            pass
        
        return dependencies
    
    def check_cross_domain_references(self, file_path, content, file_domain):
        """Check for cross-domain references that need refactoring"""
                for keyword in info["keywords"]:
                    if re.search(rf'\b{keyword}\b', content, re.IGNORECASE):
                        issues.append({
                            "file": str(file_path),
                            "from_domain": file_domain,
                            "references": domain,
                            "keyword": keyword,
                            "severity": "high" if keyword in content.lower() else "medium"
                        })
        
        return issues
    
    def scan_codebase(self):
        """Scan entire codebase for domain-specific files"""
        print("🔍 Scanning codebase for domain-specific files...")
        
        # Define directories to scan
        scan_dirs = [
            "agent", "ai_components", "services", "core", 
            "apps", "factory_integration", "workflows"
        ]
        
        total_files = 0
        domain_files = 0
        
        for scan_dir in scan_dirs:
            dir_path = self.base_dir / scan_dir
            if not dir_path.exists():
                continue
                
            for root, dirs, files in os.walk(dir_path):
                # Skip test and cache directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.pytest_cache', 'node_modules']]
                
                for file in files:
                    if file.endswith(('.py', '.ts', '.js', '.yaml', '.json')):
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(self.base_dir)
                        total_files += 1
                        
                        # Analyze file
                        domain, scores = self.analyze_file_content(file_path)
                        
                        if domain:
                            domain_files += 1
                            self.domains[domain]["files"].append({
                                "path": str(rel_path),
                                "score": scores[domain],
                                "type": file_path.suffix
                            })
                            
                            # Analyze dependencies
                            if file_path.suffix == '.py':
                                deps = self.analyze_imports(file_path)
                                self.domains[domain]["dependencies"].update(deps)
                            
                            # Check for cross-domain issues
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            issues = self.check_cross_domain_references(file_path, content, domain)
                            if issues:
                                self.cross_domain_dependencies.extend(issues)
                        else:
                            # Likely a shared component
                            if any(scores.values()):  # Has some domain keywords but not dominant
                                self.shared_components.append({
                                    "path": str(rel_path),
                                    "scores": scores
                                })
        
        print(f"✅ Scanned {total_files} files, found {domain_files} domain-specific files")
    
    def analyze_database_schemas(self):
        """Analyze database schemas for domain separation"""
        print("\n📊 Analyzing database schemas...")
        
        schema_files = list(self.base_dir.glob("**/*.sql"))
        domain_tables = defaultdict(list)
        
        for schema_file in schema_files:
            try:

                pass
                with open(schema_file, 'r') as f:
                    content = f.read()
                
                # Extract table names
                table_pattern = r'CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)'
                tables = re.findall(table_pattern, content, re.IGNORECASE)
                
                for table in tables:
                    # Determine domain
                    for domain, info in self.domains.items():
                        if any(pattern in table.lower() for pattern in info["patterns"]):
                            domain_tables[domain].append({
                                "table": table,
                                "file": str(schema_file.relative_to(self.base_dir))
                            })
                            break
            except Exception:

                pass
                pass
        
        # Add to refactoring checklist
        for domain, tables in domain_tables.items():
            if tables:
                self.refactoring_checklist.append({
                    "category": "Database",
                    "domain": domain,
                    "action": f"Migrate {len(tables)} tables to domain-specific schema",
                    "items": [t["table"] for t in tables]
                })
    
    def analyze_api_endpoints(self):
        """Analyze API endpoints for domain separation"""
        print("\n🌐 Analyzing API endpoints...")
        
        router_files = list(self.base_dir.glob("**/routers/*.py"))
        domain_endpoints = defaultdict(list)
        
        for router_file in router_files:
            try:

                pass
                with open(router_file, 'r') as f:
                    content = f.read()
                
                # Extract route definitions
                route_pattern = r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
                routes = re.findall(route_pattern, content)
                
                for method, path in routes:
                    # Determine domain
                    for domain, info in self.domains.items():
                        if any(keyword in path.lower() for keyword in info["keywords"]):
                            domain_endpoints[domain].append({
                                "method": method.upper(),
                                "path": path,
                                "file": str(router_file.relative_to(self.base_dir))
                            })
                            break
            except Exception:

                pass
                pass
        
        # Add to refactoring checklist
        for domain, endpoints in domain_endpoints.items():
            if endpoints:
                self.refactoring_checklist.append({
                    "category": "API",
                    "domain": domain,
                    "action": f"Move {len(endpoints)} endpoints to domain API",
                    "items": [f"{e['method']} {e['path']}" for e in endpoints]
                })
    
    def generate_dependency_graph(self):
        """Generate dependency graph for domains"""
        print("\n🔗 Analyzing dependencies...")
        
        # Analyze internal dependencies
        for domain, info in self.domains.items():
            internal_deps = set()
            external_deps = set()
            
            for dep in info["dependencies"]:
                # Check if dependency is internal to project
                if dep.startswith(('agent', 'ai_components', 'services', 'core')):
                    internal_deps.add(dep)
                else:
                    external_deps.add(dep)
            
            info["internal_dependencies"] = list(internal_deps)
            info["external_dependencies"] = list(external_deps)
    
    def generate_refactoring_checklist(self):
        """Generate comprehensive refactoring checklist"""
        print("\n📋 Generating refactoring checklist...")
        
        for domain, info in self.domains.items():
            if info["files"]:
                # Group files by directory
                files_by_dir = defaultdict(list)
                for file_info in info["files"]:
                    dir_path = str(Path(file_info["path"]).parent)
                    files_by_dir[dir_path].append(file_info["path"])
                
                # Add file relocation tasks
                for dir_path, files in files_by_dir.items():
                    self.refactoring_checklist.append({
                        "category": "Files",
                        "domain": domain,
                        "action": f"Move {len(files)} files from {dir_path}",
                        "target": f"domains/{domain}/services/",
                        "items": files[:5]  # Show first 5 files
                    })
        
        # Add cross-domain dependency resolution
        if self.cross_domain_dependencies:
            grouped_issues = defaultdict(list)
            # TODO: Consider using list comprehension for better performance

            # TODO: Consider using list comprehension for better performance
 for issue in self.cross_domain_dependencies:
                key = f"{issue['from_domain']}->{issue['references']}"
                grouped_issues[key].append(issue)
            
            for key, issues in grouped_issues.items():
                from_domain, to_domain = key.split('->')
                self.refactoring_checklist.append({
                    "category": "Dependencies",
                    "domain": from_domain,
                    "action": f"Resolve {len(issues)} cross-domain references to {to_domain}",
                    "severity": "high",
                    "items": [issue["file"] for issue in issues[:3]]
                })
        
        # Add shared component recommendations
        if self.shared_components:
            self.refactoring_checklist.append({
                "category": "Shared",
                "domain": "Common",
                "action": f"Review {len(self.shared_components)} potential shared components",
                "target": "shared/",
                "items": [c["path"] for c in self.shared_components[:5]]
            })
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_domain_files": sum(len(d["files"]) for d in self.domains.values()),
                "cross_domain_issues": len(self.cross_domain_dependencies),
                "shared_components": len(self.shared_components),
                "refactoring_tasks": len(self.refactoring_checklist)
            },
            "domains": {},
            "refactoring_checklist": self.refactoring_checklist,
            "cross_domain_dependencies": self.cross_domain_dependencies[:10],  # Top 10
            "recommendations": []
        }
        
        # Domain-specific summaries
        for domain, info in self.domains.items():
            report["domains"][domain] = {
                "file_count": len(info["files"]),
                "top_files": sorted(info["files"], key=lambda x: x["score"], reverse=True)[:5],
                "dependency_count": len(info["dependencies"]),
                "issues": len([i for i in self.cross_domain_dependencies if i["from_domain"] == domain])
            }
        
        # Generate recommendations
        if report["summary"]["cross_domain_issues"] > 10:
            report["recommendations"].append({
                "priority": "HIGH",
                "issue": "High cross-domain coupling",
                "action": "Create domain interfaces to reduce direct dependencies"
            })
        
        for domain, info in self.domains.items():
            if len(info["files"]) == 0:
                report["recommendations"].append({
                    "priority": "MEDIUM",
                    "issue": f"No files identified for {domain} domain",
                    "action": f"Review codebase for {domain}-specific functionality"
                })
        
        return report
    
    def save_report(self):
        """Save analysis report"""
        report_path = self.base_dir / "DOMAIN_SEPARATION_ANALYSIS.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Analysis report saved to: {report_path}")
        
        # Create migration script
        migration_script = self.base_dir / "scripts" / "migrate_to_domains.sh"
        with open(migration_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Domain Migration Script\n")
            f.write("# Generated by Domain Separation Analyzer\n\n")
            
            f.write("# Create domain directories\n")
            f.write("mkdir -p domains/{Personal,PayReady,ParagonRX}/{services,models,api,config}\n\n")
            
            # Add file migration commands
            for task in self.refactoring_checklist:
                if task["category"] == "Files":
                    f.write(f"# Migrate {task['domain']} files\n")
                    for file in task.get("items", []):
                        f.write(f"# mv {file} {task['target']}\n")
                    f.write("\n")
        
        os.chmod(migration_script, 0o755)
        print(f"✅ Migration script created: {migration_script}")
    
    def print_summary(self):
        """Print analysis summary"""
        print("\n" + "="*60)
        print("📊 DOMAIN SEPARATION ANALYSIS SUMMARY")
        print("="*60)
        
        for domain, info in self.domains.items():
            print(f"\n{domain} Domain:")
            print(f"  Files: {len(info['files'])}")
            print(f"  Dependencies: {len(info['dependencies'])}")
            print(f"  Issues: {len([i for i in self.cross_domain_dependencies if i['from_domain'] == domain])}")
        
        print(f"\n🔗 Cross-Domain Dependencies: {len(self.cross_domain_dependencies)}")
        print(f"📦 Shared Components: {len(self.shared_components)}")
        print(f"✅ Refactoring Tasks: {len(self.refactoring_checklist)}")
        
        print("\n📋 Top Refactoring Tasks:")
        for task in self.refactoring_checklist[:5]:
            print(f"  [{task['category']}] {task['action']}")
            if task.get('severity') == 'high':
                print(f"    ⚠️  HIGH PRIORITY")
    
    def run_analysis(self):
        """Run complete domain separation analysis"""
        print("🚀 Starting Domain Separation Analysis")
        print("="*60)
        
        self.scan_codebase()
        self.analyze_database_schemas()
        self.analyze_api_endpoints()
        self.generate_dependency_graph()
        self.generate_refactoring_checklist()
        self.save_report()
        self.print_summary()
        
        print("\n✅ Analysis complete! Review DOMAIN_SEPARATION_ANALYSIS.json for details.")
        print("📝 Migration script available at: scripts/migrate_to_domains.sh")

if __name__ == "__main__":
    analyzer = DomainSeparationAnalyzer()
    analyzer.run_analysis()
