#!/usr/bin/env python3
"""Infrastructure Tests Suite"""
    """Test API Gateway configuration"""
        """Test NGINX configuration exists"""
        nginx_config = Path("infrastructure/nginx/domain-routing.conf")
        self.assertTrue(nginx_config.exists(), "NGINX config not found")
    
    def test_circuit_breaker_imported(self):
        """Test circuit breaker can be imported"""
            self.fail("Circuit breaker import failed")
    
    def test_rate_limits_configured(self):
        """Test rate limits are properly configured"""
            "personal": Path("config/domains/personal_rate_limits.json"),
            "payready": Path("config/domains/payready_rate_limits.json"),
            "paragonrx": Path("config/domains/paragonrx_rate_limits.json")
        }
        
        for domain, path in rate_limits.items():
            self.assertTrue(path.exists(), f"Rate limit config missing for {domain}")
            
            with open(path) as f:
                config = json.load(f)
                self.assertIn("rate_limiting", config)
                self.assertTrue(config["rate_limiting"]["enabled"])

class TestProvisioning(unittest.TestCase):
    """Test provisioning enhancements"""
        """Test enhanced provisioning script exists"""
        script = Path("scripts/enhanced_provisioning.py")
        self.assertTrue(script.exists(), "Enhanced provisioning script not found")
    
    def test_rollback_script_exists(self):
        """Test rollback script exists"""
        script = Path("scripts/rollback_infrastructure.py")
        self.assertTrue(script.exists(), "Rollback script not found")
    
    @patch('enhanced_provisioning.EnhancedProvisioner')
    def test_provisioning_with_retry(self, mock_provisioner):
        """Test provisioning includes retry logic"""
        mock_func = Mock(side_effect=[Exception("First fail"), "Success"])
        result = provisioner.provision_with_retry(mock_func, max_retries=2)
        self.assertEqual(result, "Success")
        self.assertEqual(mock_func.call_count, 2)

class TestMonitoring(unittest.TestCase):
    """Test AI monitoring tools"""
        """Test AI monitor script exists"""
        script = Path("scripts/ai_infrastructure_monitor.py")
        self.assertTrue(script.exists(), "AI monitor script not found")
    
    async def test_anomaly_detection(self):
        """Test anomaly detection logic"""
        anomaly_metrics["domains"]["personal"]["cpu_usage"] = 99.9
        
        anomalies = monitor.detect_anomalies(anomaly_metrics)
        self.assertGreater(len(anomalies), 0, "Anomaly not detected")
        self.assertEqual(anomalies[0]["domain"], "personal")
        self.assertEqual(anomalies[0]["metric"], "cpu_usage")

class TestIntegration(unittest.TestCase):
    """Integration tests"""
        """Test all domains have complete configuration"""
        domains = ["personal", "payready", "paragonrx"]
        
        for domain in domains:
            # Check Weaviate config
            weaviate_config = Path(f"config/domains/{domain}_weaviate.json")
            self.assertTrue(weaviate_config.exists(), f"Weaviate config missing for {domain}")
            
            # Check Airbyte config
            airbyte_config = Path(f"config/domains/{domain}_airbyte.json")
            self.assertTrue(airbyte_config.exists(), f"Airbyte config missing for {domain}")
            
            # Check rate limit config
            rate_config = Path(f"config/domains/{domain}_rate_limits.json")
            self.assertTrue(rate_config.exists(), f"Rate limit config missing for {domain}")
    
    def test_github_workflow_updated(self):
        """Test GitHub workflow includes domain routing"""
        workflow_path = Path(".github/workflows/domain_infrastructure.yml")
        self.assertTrue(workflow_path.exists(), "GitHub workflow not found")
        
        with open(workflow_path) as f:
            content = f.read()
            self.assertIn("Configure Domain Routing", content)

def run_async_test(coro):
    """Helper to run async tests"""
if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
