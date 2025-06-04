#!/usr/bin/env python3
"""
"""
    """Validates domain infrastructure configurations"""
        self.base_dir = Path("/root/cherry_ai-main")
        self.domains = ["personal", "payready", "paragonrx"]
        self.validation_results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("🔍 Validating Domain Infrastructure")
        print("=" * 60)
        
        # Check rate limit configurations
        self._validate_rate_limits()
        
        # Check Weaviate configurations
        self._validate_weaviate_configs()
        
        # Check Airbyte configurations
        self._validate_airbyte_configs()
        
        # Check NGINX routing
        self._validate_nginx_routing()
        
        # Check circuit breaker configurations
        self._validate_circuit_breakers()
        
        # Check domain isolation
        self._validate_domain_isolation()
        
        # Print results
        self._print_results()
        
        return len(self.validation_results["failed"]) == 0
    
    def _validate_rate_limits(self):
        """Validate rate limit configurations for all domains"""
        print("\n📋 Validating Rate Limit Configurations...")
        
        for domain in self.domains:
            config_path = self.base_dir / "config" / "domains" / f"{domain}_rate_limits.json"
            
            if not config_path.exists():
                self.validation_results["failed"].append(
                    f"Missing rate limit config for {domain}: {config_path}"
                )
                continue
            
            try:

            
                pass
                with open(config_path) as f:
                    config = json.load(f)
                
                # Validate required fields
                required_fields = ["domain", "rate_limiting", "circuit_breaker", "retry_policy"]
                for field in required_fields:
                    if field not in config:
                        self.validation_results["failed"].append(
                            f"Missing required field '{field}' in {domain} rate limits"
                        )
                
                # Validate rate limiting is enabled
                if not config.get("rate_limiting", {}).get("enabled", False):
                    self.validation_results["failed"].append(
                        f"Rate limiting not enabled for {domain}"
                    )
                
                # Validate circuit breaker is enabled
                if not config.get("circuit_breaker", {}).get("enabled", False):
                    self.validation_results["warnings"].append(
                        f"Circuit breaker not enabled for {domain}"
                    )
                
                # Domain-specific validations
                if domain == "payready" and not config.get("security", {}).get("require_api_key", False):
                    self.validation_results["warnings"].append(
                        "PayReady should require API key for security"
                    )
                
                if domain == "paragonrx" and not config.get("compliance", {}).get("hipaa_enabled", False):
                    self.validation_results["failed"].append(
                        "ParagonRX must have HIPAA compliance enabled"
                    )
                
                self.validation_results["passed"].append(
                    f"Rate limit config valid for {domain}"
                )
                
            except Exception:

                
                pass
                self.validation_results["failed"].append(
                    f"Error reading {domain} rate limits: {str(e)}"
                )
    
    def _validate_weaviate_configs(self):
        """Validate Weaviate configurations"""
        print("\n📋 Validating Weaviate Configurations...")
        
        for domain in self.domains:
            config_path = self.base_dir / "config" / "domains" / f"{domain}_weaviate.json"
            
            if not config_path.exists():
                self.validation_results["warnings"].append(
                    f"Missing Weaviate config for {domain}: {config_path}"
                )
                continue
            
            try:

            
                pass
                with open(config_path) as f:
                    config = json.load(f)
                
                # Validate schema
                if "schema" not in config:
                    self.validation_results["failed"].append(
                        f"Missing schema in {domain} Weaviate config"
                    )
                
                # Validate URL
                if "url" not in config:
                    self.validation_results["failed"].append(
                        f"Missing URL in {domain} Weaviate config"
                    )
                
                self.validation_results["passed"].append(
                    f"Weaviate config valid for {domain}"
                )
                
            except Exception:

                
                pass
                self.validation_results["failed"].append(
                    f"Error reading {domain} Weaviate config: {str(e)}"
                )
    
    def _validate_airbyte_configs(self):
        """Validate Airbyte configurations"""
        print("\n📋 Validating Airbyte Configurations...")
        
        for domain in self.domains:
            config_path = self.base_dir / "config" / "domains" / f"{domain}_airbyte.json"
            
            if not config_path.exists():
                self.validation_results["warnings"].append(
                    f"Missing Airbyte config for {domain}: {config_path}"
                )
                continue
            
            try:

            
                pass
                with open(config_path) as f:
                    config = json.load(f)
                
                # Validate connections
                if "connections" not in config:
                    self.validation_results["failed"].append(
                        f"Missing connections in {domain} Airbyte config"
                    )
                
                self.validation_results["passed"].append(
                    f"Airbyte config valid for {domain}"
                )
                
            except Exception:

                
                pass
                self.validation_results["failed"].append(
                    f"Error reading {domain} Airbyte config: {str(e)}"
                )
    
    def _validate_nginx_routing(self):
        """Validate NGINX routing configuration"""
        print("\n📋 Validating NGINX Routing...")
        
        nginx_config = self.base_dir / "infrastructure" / "nginx" / "domain-routing.conf"
        
        if not nginx_config.exists():
            self.validation_results["warnings"].append(
                "NGINX routing configuration not found"
            )
            return
        
        try:

        
            pass
            with open(nginx_config) as f:
                content = f.read()
            
            # Check for all domain routes
            for domain in self.domains:
                if f"location /{domain}" not in content:
                    self.validation_results["failed"].append(
                        f"Missing route for {domain} in NGINX config"
                    )
                
                if f"{domain}_backend" not in content:
                    self.validation_results["failed"].append(
                        f"Missing backend definition for {domain}"
                    )
                
                if f"{domain}_limit" not in content:
                    self.validation_results["warnings"].append(
                        f"Missing rate limit zone for {domain}"
                    )
            
            # Check for circuit breaker headers
            if "X-Circuit-Breaker" not in content:
                self.validation_results["warnings"].append(
                    "Circuit breaker headers not configured in NGINX"
                )
            
            self.validation_results["passed"].append(
                "NGINX routing configuration valid"
            )
            
        except Exception:

            
            pass
            self.validation_results["failed"].append(
                f"Error reading NGINX config: {str(e)}"
            )
    
    def _validate_circuit_breakers(self):
        """Validate circuit breaker implementation"""
        print("\n📋 Validating Circuit Breakers...")
        
        circuit_breaker_path = self.base_dir / "shared" / "enhanced_circuit_breaker.py"
        
        if not circuit_breaker_path.exists():
            self.validation_results["failed"].append(
                "Enhanced circuit breaker implementation not found"
            )
            return
        
        try:

        
            pass
            # Check if the module can be imported
            import sys
            sys.path.insert(0, str(self.base_dir))
            from shared.enhanced_circuit_breaker import EnhancedCircuitBreaker, circuit_breaker_manager
            
            self.validation_results["passed"].append(
                "Circuit breaker implementation valid"
            )
            
        except Exception:

            
            pass
            self.validation_results["failed"].append(
                f"Cannot import circuit breaker: {str(e)}"
            )
    
    def _validate_domain_isolation(self):
        """Validate domain isolation"""
        print("\n📋 Validating Domain Isolation...")
        
        # Check for cross-domain references
        issues = []
        
        # Check configuration files
        for domain in self.domains:
            for other_domain in self.domains:
                if domain != other_domain:
                    # Check rate limit configs
                    rate_limit_path = self.base_dir / "config" / "domains" / f"{domain}_rate_limits.json"
                    if rate_limit_path.exists():
                        with open(rate_limit_path) as f:
                            content = f.read()
                            if other_domain in content:
                                issues.append(
                                    f"{domain} rate limits reference {other_domain}"
                                )
        
        if issues:
            for issue in issues:
                self.validation_results["warnings"].append(issue)
        else:
            self.validation_results["passed"].append(
                "Domain isolation validated - no cross-references found"
            )
    
    def _print_results(self):
        """Print validation results"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS")
        print("=" * 60)
        
        if self.validation_results["passed"]:
            print("\n✅ PASSED:")
            for result in self.validation_results["passed"]:
                print(f"  • {result}")
        
        if self.validation_results["warnings"]:
            print("\n⚠️  WARNINGS:")
            for warning in self.validation_results["warnings"]:
                print(f"  • {warning}")
        
        if self.validation_results["failed"]:
            print("\n❌ FAILED:")
            for failure in self.validation_results["failed"]:
                print(f"  • {failure}")
        
        print("\n" + "=" * 60)
        print(f"Total Passed: {len(self.validation_results['passed'])}")
        print(f"Total Warnings: {len(self.validation_results['warnings'])}")
        print(f"Total Failed: {len(self.validation_results['failed'])}")
        print("=" * 60)

def main():
    """Main validation entry point"""
        print("\n✅ Domain infrastructure validation PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Domain infrastructure validation FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()
