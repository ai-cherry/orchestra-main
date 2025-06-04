#!/usr/bin/env python3
"""
Infrastructure Validation and Testing Suite
Comprehensive testing of the Tier 2 enterprise infrastructure
"""

import requests
import subprocess
import json
import time
import socket
from typing import Dict, List, Tuple

class InfrastructureValidator:
    def __init__(self):
        self.infrastructure = {
            "production": "45.32.69.157",
            "database": "45.77.87.106",
            "staging": "207.246.108.201",
            "load_balancer": "45.63.58.63",
            "kubernetes_workers": [
                "207.246.104.92",
                "66.42.107.3",
                "45.32.68.4"
            ]
        }
        
        self.test_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
    
    def test_network_connectivity(self) -> Dict:
        """Test network connectivity to all servers"""
        print("🌐 TESTING NETWORK CONNECTIVITY")
        print("=" * 35)
        
        connectivity_results = {}
        
        for name, ip in self.infrastructure.items():
            if isinstance(ip, list):
                # Handle Kubernetes workers
                connectivity_results[name] = {}
                for i, worker_ip in enumerate(ip):
                    result = self.ping_host(worker_ip)
                    connectivity_results[name][f"worker_{i+1}"] = result
                    print(f"   {name} worker {i+1} ({worker_ip}): {'✅' if result['success'] else '❌'}")
            else:
                result = self.ping_host(ip)
                connectivity_results[name] = result
                print(f"   {name} ({ip}): {'✅' if result['success'] else '❌'}")
        
        return connectivity_results
    
    def ping_host(self, host: str) -> Dict:
        """Ping a host to test connectivity"""
        try:
            result = subprocess.run(
                ['ping', '-c', '3', '-W', '3', host],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                # Extract ping statistics
                lines = result.stdout.split('\n')
                stats_line = [line for line in lines if 'packet loss' in line]
                if stats_line:
                    loss_percent = stats_line[0].split('%')[0].split()[-1]
                    return {
                        "success": True,
                        "packet_loss": f"{loss_percent}%",
                        "details": "Host reachable"
                    }
            
            return {
                "success": False,
                "error": "Host unreachable",
                "details": result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "Ping command failed"
            }
    
    def test_ssh_connectivity(self) -> Dict:
        """Test SSH connectivity to servers"""
        print("\n🔐 TESTING SSH CONNECTIVITY")
        print("=" * 30)
        
        ssh_results = {}
        
        for name, ip in self.infrastructure.items():
            if isinstance(ip, list):
                continue  # Skip Kubernetes workers for SSH test
            
            if name == "load_balancer":
                continue  # Skip load balancer for SSH test
            
            result = self.test_ssh_connection(ip)
            ssh_results[name] = result
            print(f"   {name} ({ip}): {'✅' if result['success'] else '❌'}")
            
            if not result['success']:
                print(f"      Error: {result['error']}")
        
        return ssh_results
    
    def test_ssh_connection(self, host: str) -> Dict:
        """Test SSH connection to a host"""
        try:
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=no',
                '-o', 'PasswordAuthentication=no', '-o', 'PubkeyAuthentication=yes',
                f'root@{host}', 'echo "SSH test successful"'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "details": "SSH key authentication working"
                }
            else:
                return {
                    "success": False,
                    "error": "SSH authentication failed",
                    "details": result.stderr.strip()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": "SSH command failed"
            }
    
    def test_database_services(self) -> Dict:
        """Test database services"""
        print("\n🗄️  TESTING DATABASE SERVICES")
        print("=" * 32)
        
        db_host = self.infrastructure["database"]
        db_results = {}
        
        # Test PostgreSQL
        postgres_result = self.test_port_connectivity(db_host, 5432, "PostgreSQL")
        db_results["postgresql"] = postgres_result
        print(f"   PostgreSQL (5432): {'✅' if postgres_result['success'] else '❌'}")
        
        # Test Redis
        redis_result = self.test_port_connectivity(db_host, 6379, "Redis")
        db_results["redis"] = redis_result
        print(f"   Redis (6379): {'✅' if redis_result['success'] else '❌'}")
        
        # Test Weaviate
        weaviate_result = self.test_http_endpoint(f"http://{db_host}:8080/v1/meta", "Weaviate")
        db_results["weaviate"] = weaviate_result
        print(f"   Weaviate (8080): {'✅' if weaviate_result['success'] else '❌'}")
        
        return db_results
    
    def test_port_connectivity(self, host: str, port: int, service_name: str) -> Dict:
        """Test if a port is open on a host"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return {
                    "success": True,
                    "details": f"{service_name} port {port} is open"
                }
            else:
                return {
                    "success": False,
                    "error": f"Port {port} is closed or filtered",
                    "details": f"{service_name} not accessible"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": f"Failed to test {service_name} connectivity"
            }
    
    def test_http_endpoint(self, url: str, service_name: str) -> Dict:
        """Test HTTP endpoint"""
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "details": f"{service_name} HTTP endpoint responding"
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}",
                    "details": f"{service_name} returned error status"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": f"Failed to connect to {service_name}"
            }
    
    def test_monitoring_services(self) -> Dict:
        """Test monitoring services"""
        print("\n📊 TESTING MONITORING SERVICES")
        print("=" * 35)
        
        staging_host = self.infrastructure["staging"]
        monitoring_results = {}
        
        # Test Prometheus
        prometheus_result = self.test_http_endpoint(f"http://{staging_host}:9090/-/healthy", "Prometheus")
        monitoring_results["prometheus"] = prometheus_result
        print(f"   Prometheus (9090): {'✅' if prometheus_result['success'] else '❌'}")
        
        # Test Grafana
        grafana_result = self.test_http_endpoint(f"http://{staging_host}:3000/api/health", "Grafana")
        monitoring_results["grafana"] = grafana_result
        print(f"   Grafana (3000): {'✅' if grafana_result['success'] else '❌'}")
        
        # Test AlertManager
        alertmanager_result = self.test_http_endpoint(f"http://{staging_host}:9093/-/healthy", "AlertManager")
        monitoring_results["alertmanager"] = alertmanager_result
        print(f"   AlertManager (9093): {'✅' if alertmanager_result['success'] else '❌'}")
        
        # Test Elasticsearch
        elasticsearch_result = self.test_http_endpoint(f"http://{staging_host}:9200/_cluster/health", "Elasticsearch")
        monitoring_results["elasticsearch"] = elasticsearch_result
        print(f"   Elasticsearch (9200): {'✅' if elasticsearch_result['success'] else '❌'}")
        
        # Test Kibana
        kibana_result = self.test_http_endpoint(f"http://{staging_host}:5601/api/status", "Kibana")
        monitoring_results["kibana"] = kibana_result
        print(f"   Kibana (5601): {'✅' if kibana_result['success'] else '❌'}")
        
        return monitoring_results
    
    def test_kubernetes_cluster(self) -> Dict:
        """Test Kubernetes cluster"""
        print("\n☸️  TESTING KUBERNETES CLUSTER")
        print("=" * 32)
        
        k8s_results = {}
        
        # Test worker nodes connectivity
        worker_results = {}
        for i, worker_ip in enumerate(self.infrastructure["kubernetes_workers"]):
            node_result = self.ping_host(worker_ip)
            worker_results[f"worker_{i+1}"] = node_result
            print(f"   Worker {i+1} ({worker_ip}): {'✅' if node_result['success'] else '❌'}")
        
        k8s_results["worker_nodes"] = worker_results
        
        # Test if kubectl is configured (if available)
        try:
            result = subprocess.run(['kubectl', 'cluster-info'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                k8s_results["kubectl"] = {
                    "success": True,
                    "details": "kubectl configured and cluster accessible"
                }
                print("   kubectl: ✅")
            else:
                k8s_results["kubectl"] = {
                    "success": False,
                    "error": "kubectl not configured or cluster not accessible",
                    "details": result.stderr
                }
                print("   kubectl: ❌")
        except FileNotFoundError:
            k8s_results["kubectl"] = {
                "success": False,
                "error": "kubectl not installed",
                "details": "kubectl command not found"
            }
            print("   kubectl: ⚠️  (not installed)")
        
        return k8s_results
    
    def test_load_balancer(self) -> Dict:
        """Test load balancer"""
        print("\n⚖️  TESTING LOAD BALANCER")
        print("=" * 27)
        
        lb_ip = self.infrastructure["load_balancer"]
        lb_results = {}
        
        # Test HTTP connectivity
        http_result = self.test_port_connectivity(lb_ip, 80, "Load Balancer HTTP")
        lb_results["http"] = http_result
        print(f"   HTTP (80): {'✅' if http_result['success'] else '❌'}")
        
        # Test HTTPS connectivity
        https_result = self.test_port_connectivity(lb_ip, 443, "Load Balancer HTTPS")
        lb_results["https"] = https_result
        print(f"   HTTPS (443): {'✅' if https_result['success'] else '❌'}")
        
        return lb_results
    
    def test_backup_system(self) -> Dict:
        """Test backup system"""
        print("\n💾 TESTING BACKUP SYSTEM")
        print("=" * 27)
        
        staging_host = self.infrastructure["staging"]
        backup_results = {}
        
        try:
            # Check if backup directory exists
            result = subprocess.run([
                'ssh', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=no',
                f'root@{staging_host}', 'ls -la /opt/backups/'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                backup_results["backup_directory"] = {
                    "success": True,
                    "details": "Backup directory exists"
                }
                print("   Backup directory: ✅")
                
                # Check for recent backups
                backup_check = subprocess.run([
                    'ssh', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=no',
                    f'root@{staging_host}', 'find /opt/backups -name "*.sql.gz" -mtime -7 | wc -l'
                ], capture_output=True, text=True, timeout=15)
                
                if backup_check.returncode == 0:
                    recent_backups = int(backup_check.stdout.strip())
                    backup_results["recent_backups"] = {
                        "success": recent_backups > 0,
                        "count": recent_backups,
                        "details": f"Found {recent_backups} recent backups"
                    }
                    print(f"   Recent backups: {'✅' if recent_backups > 0 else '⚠️'} ({recent_backups})")
                
            else:
                backup_results["backup_directory"] = {
                    "success": False,
                    "error": "Backup directory not found",
                    "details": result.stderr
                }
                print("   Backup directory: ❌")
                
        except Exception as e:
            backup_results["error"] = {
                "success": False,
                "error": str(e),
                "details": "Failed to test backup system"
            }
            print("   Backup system: ❌")
        
        return backup_results
    
    def generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        print("\n🧪 RUNNING COMPREHENSIVE VALIDATION")
        print("=" * 40)
        
        # Run all tests
        self.test_results["tests"]["network_connectivity"] = self.test_network_connectivity()
        self.test_results["tests"]["ssh_connectivity"] = self.test_ssh_connectivity()
        self.test_results["tests"]["database_services"] = self.test_database_services()
        self.test_results["tests"]["monitoring_services"] = self.test_monitoring_services()
        self.test_results["tests"]["kubernetes_cluster"] = self.test_kubernetes_cluster()
        self.test_results["tests"]["load_balancer"] = self.test_load_balancer()
        self.test_results["tests"]["backup_system"] = self.test_backup_system()
        
        # Calculate summary statistics
        self.calculate_test_summary()
        
        return self.test_results
    
    def calculate_test_summary(self):
        """Calculate test summary statistics"""
        total_tests = 0
        passed = 0
        failed = 0
        warnings = 0
        
        def count_results(obj):
            nonlocal total_tests, passed, failed, warnings
            
            if isinstance(obj, dict):
                if "success" in obj:
                    total_tests += 1
                    if obj["success"]:
                        passed += 1
                    else:
                        failed += 1
                else:
                    for value in obj.values():
                        count_results(value)
            elif isinstance(obj, list):
                for item in obj:
                    count_results(item)
        
        count_results(self.test_results["tests"])
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "success_rate": f"{(passed/total_tests*100):.1f}%" if total_tests > 0 else "0%"
        }
    
    def print_validation_summary(self):
        """Print validation summary"""
        print("\n🎯 VALIDATION SUMMARY")
        print("=" * 22)
        
        summary = self.test_results["summary"]
        print(f"   Total tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']} ✅")
        print(f"   Failed: {summary['failed']} ❌")
        print(f"   Success rate: {summary['success_rate']}")
        
        if summary['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! Infrastructure is fully operational.")
        elif summary['failed'] < summary['total_tests'] * 0.2:  # Less than 20% failure
            print("\n⚠️  Minor issues detected. Infrastructure is mostly operational.")
        else:
            print("\n❌ Significant issues detected. Infrastructure needs attention.")
    
    def create_infrastructure_health_dashboard(self) -> str:
        """Create a simple health dashboard"""
        dashboard = f"""
# Orchestra-Main Infrastructure Health Dashboard
Generated: {self.test_results['timestamp']}

## 🏗️ Infrastructure Overview
- **Production Server**: {self.infrastructure['production']}
- **Database Server**: {self.infrastructure['database']}
- **Staging Server**: {self.infrastructure['staging']}
- **Load Balancer**: {self.infrastructure['load_balancer']}
- **Kubernetes Workers**: {len(self.infrastructure['kubernetes_workers'])} nodes

## 📊 Test Results Summary
- **Total Tests**: {self.test_results['summary']['total_tests']}
- **Passed**: {self.test_results['summary']['passed']} ✅
- **Failed**: {self.test_results['summary']['failed']} ❌
- **Success Rate**: {self.test_results['summary']['success_rate']}

## 🔗 Service Endpoints
- **Prometheus**: http://{self.infrastructure['staging']}:9090
- **Grafana**: http://{self.infrastructure['staging']}:3000
- **Kibana**: http://{self.infrastructure['staging']}:5601
- **Load Balancer**: http://{self.infrastructure['load_balancer']}

## 🗄️ Database Connections
- **PostgreSQL**: {self.infrastructure['database']}:5432
- **Redis**: {self.infrastructure['database']}:6379
- **Weaviate**: http://{self.infrastructure['database']}:8080

## 🏥 Health Check Commands
```bash
# Quick health check
curl http://{self.infrastructure['staging']}:9090/-/healthy  # Prometheus
curl http://{self.infrastructure['staging']}:3000/api/health  # Grafana
curl http://{self.infrastructure['database']}:8080/v1/meta   # Weaviate

# Database connectivity
nc -zv {self.infrastructure['database']} 5432  # PostgreSQL
nc -zv {self.infrastructure['database']} 6379  # Redis
```

## 🛠️ Management Scripts
- **Health Check**: `/home/ubuntu/scripts/health_check.sh`
- **Deploy to Staging**: `/home/ubuntu/scripts/deploy_to_staging.sh`
- **Deploy to Production**: `/home/ubuntu/scripts/deploy_to_production.sh`
- **Backup Database**: `/opt/backups/scripts/backup_database.sh`
"""
        
        return dashboard

def main():
    validator = InfrastructureValidator()
    
    print("🧪 ORCHESTRA-MAIN INFRASTRUCTURE VALIDATION")
    print("=" * 50)
    
    # Run comprehensive validation
    results = validator.generate_validation_report()
    
    # Print summary
    validator.print_validation_summary()
    
    # Save results
    with open("/home/ubuntu/infrastructure_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Create health dashboard
    dashboard = validator.create_infrastructure_health_dashboard()
    with open("/home/ubuntu/infrastructure_health_dashboard.md", "w") as f:
        f.write(dashboard)
    
    print(f"\n📄 Results saved to:")
    print(f"   📊 Validation results: infrastructure_validation_results.json")
    print(f"   📋 Health dashboard: infrastructure_health_dashboard.md")

if __name__ == "__main__":
    main()

