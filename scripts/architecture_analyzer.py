#!/usr/bin/env python3
"""
"""
    """Comprehensive architecture analysis tool"""
        self.base_dir = Path("/root/orchestra-main")
        self.domains = ["Personal", "PayReady", "ParagonRX"]
        self.analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "modularity_score": 0,
            "domain_separation": {},
            "infrastructure_flexibility": {},
            "improvements_needed": [],
            "recommendations": []
        }
        
    def analyze_directory_structure(self):
        """Analyze the directory structure for modularity"""
        print("\n🔍 Analyzing Directory Structure...")
        
        # Key directories that indicate good modularity
        modular_indicators = {
            "services": 0,
            "components": 0,
            "modules": 0,
            "domains": 0,
            "shared": 0,
            "core": 0,
            "infrastructure": 0,
            "config": 0
        }
        
        # Scan directory structure
        for root, dirs, files in os.walk(self.base_dir):
            rel_path = Path(root).relative_to(self.base_dir)
            
            # Check for modular directory patterns
            for indicator in modular_indicators:
                if indicator in str(rel_path).lower():
                    modular_indicators[indicator] += 1
        
        # Calculate modularity score
        total_indicators = sum(modular_indicators.values())
        max_score = len(modular_indicators) * 5  # Expect at least 5 instances of each
        modularity_score = min(100, (total_indicators / max_score) * 100)
        
        self.analysis_results["modularity_score"] = round(modularity_score, 2)
        self.analysis_results["directory_analysis"] = modular_indicators
        
        print(f"✅ Modularity Score: {modularity_score:.1f}%")
        
        # Identify missing modular structures
        for indicator, count in modular_indicators.items():
            if count == 0:
                self.analysis_results["improvements_needed"].append(
                    f"Missing {indicator} directory structure"
                )
    
    def analyze_domain_separation(self):
        """Analyze separation between domains"""
        print("\n🏢 Analyzing Domain Separation...")
        
        domain_files = defaultdict(list)
        cross_domain_dependencies = []
        
        # Scan # TODO: Consider using list comprehension for better performance
 for domain-specific files
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(('.py', '.ts', '.js')):
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(self.base_dir)
                    
                    # Check which domain this file belongs to
                    file_domain = None
                    for domain in self.domains:
                        if domain.lower() in str(rel_path).lower():
                            file_domain = domain
                            domain_files[domain].append(str(rel_path))
                            break
                    
                    # Check for cross-domain imports
                    if file_domain and file_path.suffix == '.py':
                        try:

                            pass
                            with open(file_path, 'r') as f:
                                content = f.read()
                                for other_domain in self.domains:
                                    if other_domain != file_domain and other_domain.lower() in content.lower():
                                        cross_domain_dependencies.append({
                                            "file": str(rel_path),
                                            "from_domain": file_domain,
                                            "references": other_domain
                                        })
                        except Exception:

                            pass
                            pass
        
        # Analyze results
        for domain in self.domains:
            count = len(domain_files[domain])
            self.analysis_results["domain_separation"][domain] = {
                "file_count": count,
                "isolated": count > 0 and not any(
                    dep["from_domain"] == domain 
                    for dep in cross_domain_dependencies
                )
            }
            
            if count == 0:
                self.analysis_results["improvements_needed"].append(
                    f"No dedicated structure for {domain} domain"
                )
        
        if cross_domain_dependencies:
            self.analysis_results["improvements_needed"].append(
                f"Found {len(cross_domain_dependencies)} cross-domain dependencies"
            )
            self.analysis_results["cross_domain_issues"] = cross_domain_dependencies[:5]  # First 5
        
        print(f"✅ Domain Files Found:")
        for domain, info in self.analysis_results["domain_separation"].items():
            print(f"   {domain}: {info['file_count']} files (Isolated: {info['isolated']})")
    
    def analyze_infrastructure_flexibility(self):
        """Analyze infrastructure configuration and flexibility"""
        print("\n🏗️ Analyzing Infrastructure Flexibility...")
        
        infra_patterns = {
            "docker_compose": list(self.base_dir.glob("**/docker-compose*.yml")),
            "kubernetes": list(self.base_dir.glob("**/*.yaml")) + list(self.base_dir.glob("**/*.yml")),
            "terraform": list(self.base_dir.glob("**/*.tf")),
            "pulumi": list(self.base_dir.glob("**/Pulumi.yaml")),
            "config_files": list(self.base_dir.glob("**/config/*.json")) + 
                           list(self.base_dir.glob("**/config/*.yaml"))
        }
        
        flexibility_score = 0
        max_score = 100
        
        # Check for infrastructure as code
        if infra_patterns["pulumi"]:
            flexibility_score += 25
            self.analysis_results["infrastructure_flexibility"]["iac"] = "Pulumi"
        elif infra_patterns["terraform"]:
            flexibility_score += 25
            self.analysis_results["infrastructure_flexibility"]["iac"] = "Terraform"
        else:
            self.analysis_results["improvements_needed"].append(
                "No Infrastructure as Code (IaC) solution found"
            )
        
        # Check for containerization
        if infra_patterns["docker_compose"]:
            flexibility_score += 25
            self.analysis_results["infrastructure_flexibility"]["containerization"] = True
        else:
            self.analysis_results["improvements_needed"].append(
                "No Docker Compose configuration found"
            )
        
        # Check for configuration management
        config_count = len(infra_patterns["config_files"])
        if config_count > 5:
            flexibility_score += 25
            self.analysis_results["infrastructure_flexibility"]["config_management"] = "Good"
        elif config_count > 0:
            flexibility_score += 15
            self.analysis_results["infrastructure_flexibility"]["config_management"] = "Basic"
        else:
            self.analysis_results["improvements_needed"].append(
                "Limited configuration management"
            )
        
        # Check for environment separation
        env_files = list(self.base_dir.glob("**/.env*"))
        if len(env_files) > 1:
            flexibility_score += 25
            self.analysis_results["infrastructure_flexibility"]["env_separation"] = True
        
        self.analysis_results["infrastructure_flexibility"]["score"] = flexibility_score
        print(f"✅ Infrastructure Flexibility Score: {flexibility_score}%")
    
    def analyze_service_integration(self):
        """Analyze how easily new services can be integrated"""
        print("\n🔌 Analyzing Service Integration Capability...")
        
        integration_patterns = {
            "api_gateway": False,
            "service_registry": False,
            "message_queue": False,
            "event_bus": False,
            "plugin_system": False
        }
        
        # Search for integration patterns
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(('.py', '.ts', '.js', '.yaml', '.json')):
                    file_path = Path(root) / file
                    try:

                        pass
                        with open(file_path, 'r') as f:
                            content = f.read().lower()
                            
                            if 'gateway' in content or 'proxy' in content:
                                integration_patterns["api_gateway"] = True
                            if 'registry' in content or 'discovery' in content:
                                integration_patterns["service_registry"] = True
                            if 'queue' in content or 'rabbitmq' in content or 'kafka' in content:
                                integration_patterns["message_queue"] = True
                            if 'event' in content and ('bus' in content or 'emitter' in content):
                                integration_patterns["event_bus"] = True
                            if 'plugin' in content or 'extension' in content:
                                integration_patterns["plugin_system"] = True
                    except Exception:

                        pass
                        pass
        
        integration_score = sum(integration_patterns.values()) * 20
        self.analysis_results["service_integration"] = {
            "patterns": integration_patterns,
            "score": integration_score
        }
        
        if integration_score < 60:
            self.analysis_results["improvements_needed"].append(
                "Limited service integration patterns found"
            )
        
        print(f"✅ Service Integration Score: {integration_score}%")
    
    def generate_recommendations(self):
        """Generate specific recommendations for improvement"""
        print("\n💡 Generating Recommendations...")
        
        recommendations = []
        
        # Domain separation recommendations
        if not all(self.analysis_results["domain_separation"][d]["file_count"] > 0 for d in self.domains):
            recommendations.append({
                "priority": "HIGH",
                "category": "Domain Separation",
                "action": "Create dedicated directory structure for each domain",
                "implementation": """
                """
        if self.analysis_results["modularity_score"] < 70:
            recommendations.append({
                "priority": "HIGH",
                "category": "Modularity",
                "action": "Implement a modular architecture pattern",
                "implementation": """
                """
        if self.analysis_results["infrastructure_flexibility"]["score"] < 75:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Infrastructure",
                "action": "Enhance infrastructure flexibility",
                "implementation": """
                """
        if self.analysis_results["service_integration"]["score"] < 60:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Integration",
                "action": "Implement service integration patterns",
                "implementation": """
                """
        self.analysis_results["recommendations"] = recommendations
        
        for rec in recommendations:
            print(f"\n[{rec['priority']}] {rec['category']}: {rec['action']}")
    
    def save_analysis_report(self):
        """Save the complete analysis report"""
        report_path = self.base_dir / "ARCHITECTURE_ANALYSIS_REPORT.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_path}")
        
        # Create actionable script
        script_path = self.base_dir / "scripts" / "implement_architecture_improvements.sh"
        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Architecture Improvement Implementation Script\n")
            f.write("# Generated by Architecture Analyzer\n\n")
            
            for rec in self.analysis_results["recommendations"]:
                f.write(f"# {rec['category']}: {rec['action']}\n")
                f.write(rec["implementation"].strip() + "\n\n")
        
        os.chmod(script_path, 0o755)
        print(f"✅ Implementation script created: {script_path}")
    
    def run_analysis(self):
        """Run complete architecture analysis"""
        print("🏗️ Orchestra AI Architecture Analysis")
        print("=" * 50)
        
        self.analyze_directory_structure()
        self.analyze_domain_separation()
        self.analyze_infrastructure_flexibility()
        self.analyze_service_integration()
        self.generate_recommendations()
        self.save_analysis_report()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 50)
        print(f"Modularity Score: {self.analysis_results['modularity_score']}%")
        print(f"Infrastructure Flexibility: {self.analysis_results['infrastructure_flexibility']['score']}%")
        print(f"Service Integration: {self.analysis_results['service_integration']['score']}%")
        print(f"Improvements Needed: {len(self.analysis_results['improvements_needed'])}")
        print(f"Recommendations: {len(self.analysis_results['recommendations'])}")
        
        if self.analysis_results['improvements_needed']:
            print("\n⚠️ Key Issues:")
            for issue in self.analysis_results['improvements_needed'][:5]:
                print(f"  - {issue}")

if __name__ == "__main__":
    analyzer = ArchitectureAnalyzer()
    analyzer.run_analysis()