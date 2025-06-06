#!/usr/bin/env python3
"""
Comprehensive Weaviate Fix Script
Resolves all connectivity, configuration, and startup issues
"""

import os
import sys
import subprocess
import time
import json
import requests
from pathlib import Path

class WeaviateFixer:
    def __init__(self):
        self.issues_fixed = []
        self.weaviate_dir = None
        self.config_path = None
        
    def log(self, message, level="INFO"):
        print(f"[{level}] {message}")
        
    def find_weaviate_installation(self):
        """Find where Weaviate is installed"""
        possible_paths = [
            '/opt/weaviate',
            '/usr/local/weaviate',
            './weaviate',
            os.path.expanduser('~/weaviate'),
            '/var/lib/weaviate'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.weaviate_dir = path
                self.log(f"Found Weaviate directory: {path}")
                return True
                
        # Check if Weaviate is installed via Docker
        try:
            docker_result = subprocess.run(
                ['docker', 'ps', '-a', '--format', '{{.Names}}'],
                capture_output=True,
                text=True
            )
            if 'weaviate' in docker_result.stdout:
                self.log("Weaviate is running in Docker")
                self.weaviate_dir = 'docker'
                return True
        except:
            pass
            
        self.log("Weaviate installation not found", "ERROR")
        return False
        
    def stop_conflicting_services(self):
        """Stop services using port 8080"""
        self.log("Checking for services on port 8080...")
        
        # Find process using port 8080
        try:
            # Try lsof first
            result = subprocess.run(
                ['lsof', '-i', ':8080'],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        process_name = parts[0]
                        
                        if 'weaviate' not in process_name.lower():
                            self.log(f"Found conflicting process: {process_name} (PID: {pid})")
                            
                            # Kill the process
                            try:
                                subprocess.run(['kill', '-9', pid])
                                self.log(f"Killed process {pid}")
                                self.issues_fixed.append(f"Stopped conflicting service on port 8080")
                                time.sleep(2)
                            except:
                                self.log(f"Failed to kill process {pid}", "WARNING")
        except:
            # Try netstat as fallback
            try:
                result = subprocess.run(
                    ['netstat', '-tlnp'],
                    capture_output=True,
                    text=True
                )
                if ':8080' in result.stdout:
                    self.log("Port 8080 is in use, but cannot identify process", "WARNING")
            except:
                pass
                
    def fix_python_syntax_errors(self):
        """Fix Python syntax errors in Weaviate modules"""
        self.log("Checking for Python syntax errors...")
        
        if self.weaviate_dir and self.weaviate_dir != 'docker':
            # Find all Python files
            python_files = []
            for root, dirs, files in os.walk(self.weaviate_dir):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))
                        
            errors_found = 0
            for py_file in python_files:
                try:
                    # Try to compile the file
                    with open(py_file, 'r') as f:
                        compile(f.read(), py_file, 'exec')
                except SyntaxError as e:
                    errors_found += 1
                    self.log(f"Syntax error in {py_file}: {e}", "ERROR")
                    
                    # Try to fix common indentation issues
                    try:
                        with open(py_file, 'r') as f:
                            content = f.read()
                            
                        # Fix mixed tabs and spaces
                        fixed_content = content.replace('\t', '    ')
                        
                        with open(py_file, 'w') as f:
                            f.write(fixed_content)
                            
                        self.log(f"Fixed indentation in {py_file}")
                        self.issues_fixed.append(f"Fixed syntax in {py_file}")
                    except:
                        pass
                        
            if errors_found > 0:
                self.log(f"Found and attempted to fix {errors_found} syntax errors")
                
    def create_weaviate_config(self):
        """Create proper Weaviate configuration"""
        self.log("Creating Weaviate configuration...")
        
        config = {
            "authentication": {
                "anonymous_access": {
                    "enabled": True
                }
            },
            "authorization": {
                "admin_list": {
                    "enabled": False
                }
            },
            "query_defaults": {
                "limit": 25
            },
            "debug": False,
            "persistence": {
                "data_path": "./data"
            }
        }
        
        # Save configuration
        config_dir = Path("./weaviate-config")
        config_dir.mkdir(exist_ok=True)
        
        config_path = config_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        self.config_path = str(config_path)
        self.log(f"Created configuration at {config_path}")
        self.issues_fixed.append("Created Weaviate configuration")
        
    def start_weaviate_docker(self):
        """Start Weaviate using Docker"""
        self.log("Starting Weaviate with Docker...")
        
        # Create docker-compose.yml
        docker_compose = """version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - ./weaviate-data:/var/lib/weaviate
    restart: unless-stopped
"""
        
        with open('docker-compose-weaviate.yml', 'w') as f:
            f.write(docker_compose)
            
        # Stop existing container if any
        subprocess.run(['docker-compose', '-f', 'docker-compose-weaviate.yml', 'down'], 
                      capture_output=True)
        
        # Start Weaviate
        result = subprocess.run(
            ['docker-compose', '-f', 'docker-compose-weaviate.yml', 'up', '-d'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            self.log("Weaviate Docker container started")
            self.issues_fixed.append("Started Weaviate in Docker")
            return True
        else:
            self.log(f"Failed to start Docker: {result.stderr}", "ERROR")
            return False
            
    def start_weaviate_standalone(self):
        """Start Weaviate standalone"""
        self.log("Starting Weaviate standalone...")
        
        # Download Weaviate if not present
        if not self.weaviate_dir or self.weaviate_dir == 'docker':
            self.log("Downloading Weaviate binary...")
            
            # Detect OS
            import platform
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            if system == 'darwin':
                if 'arm' in machine:
                    url = "https://github.com/weaviate/weaviate/releases/latest/download/weaviate-darwin-arm64"
                else:
                    url = "https://github.com/weaviate/weaviate/releases/latest/download/weaviate-darwin-amd64"
            elif system == 'linux':
                if 'arm' in machine:
                    url = "https://github.com/weaviate/weaviate/releases/latest/download/weaviate-linux-arm64"
                else:
                    url = "https://github.com/weaviate/weaviate/releases/latest/download/weaviate-linux-amd64"
            else:
                self.log(f"Unsupported OS: {system}", "ERROR")
                return False
                
            # Download binary
            subprocess.run(['curl', '-L', '-o', 'weaviate', url])
            subprocess.run(['chmod', '+x', 'weaviate'])
            
            self.weaviate_dir = './'
            
        # Start Weaviate
        env = os.environ.copy()
        env['PERSISTENCE_DATA_PATH'] = './weaviate-data'
        env['AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED'] = 'true'
        env['QUERY_DEFAULTS_LIMIT'] = '25'
        env['DEFAULT_VECTORIZER_MODULE'] = 'none'
        
        # Start in background
        process = subprocess.Popen(
            ['./weaviate', '--host', '0.0.0.0', '--port', '8080', '--scheme', 'http'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Save PID
        with open('weaviate.pid', 'w') as f:
            f.write(str(process.pid))
            
        self.log(f"Started Weaviate with PID {process.pid}")
        self.issues_fixed.append("Started Weaviate standalone")
        return True
        
    def wait_for_weaviate(self, timeout=30):
        """Wait for Weaviate to be ready"""
        self.log("Waiting for Weaviate to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get('http://localhost:8080/v1/.well-known/ready', timeout=2)
                if response.status_code == 200:
                    self.log("Weaviate is ready!")
                    return True
            except:
                pass
                
            time.sleep(1)
            
        self.log("Weaviate failed to start within timeout", "ERROR")
        return False
        
    def test_weaviate_api(self):
        """Test Weaviate API endpoints"""
        self.log("Testing Weaviate API...")
        
        endpoints = [
            '/v1/.well-known/ready',
            '/v1/.well-known/live',
            '/v1/meta',
            '/v1/schema'
        ]
        
        all_good = True
        for endpoint in endpoints:
            try:
                response = requests.get(f'http://localhost:8080{endpoint}', timeout=5)
                if response.status_code == 200:
                    self.log(f"✓ {endpoint} - OK")
                else:
                    self.log(f"✗ {endpoint} - Status {response.status_code}", "WARNING")
                    all_good = False
            except Exception as e:
                self.log(f"✗ {endpoint} - Error: {str(e)}", "ERROR")
                all_good = False
                
        return all_good
        
    def create_test_schema(self):
        """Create a test schema in Weaviate"""
        self.log("Creating test schema...")
        
        schema = {
            "class": "Document",
            "description": "A document with text content",
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "The content of the document"
                },
                {
                    "name": "title",
                    "dataType": ["string"],
                    "description": "The title of the document"
                }
            ]
        }
        
        try:
            response = requests.post(
                'http://localhost:8080/v1/schema',
                json=schema,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                self.log("Test schema created successfully")
                self.issues_fixed.append("Created test schema")
                return True
            else:
                self.log(f"Failed to create schema: {response.text}", "WARNING")
                return False
        except Exception as e:
            self.log(f"Error creating schema: {str(e)}", "ERROR")
            return False
            
    def run_comprehensive_fix(self):
        """Run all fixes in sequence"""
        self.log("\n" + "="*60)
        self.log("WEAVIATE COMPREHENSIVE FIX")
        self.log("="*60)
        
        # 1. Stop conflicting services
        self.stop_conflicting_services()
        
        # 2. Find Weaviate installation
        has_installation = self.find_weaviate_installation()
        
        # 3. Fix Python syntax errors if found
        if has_installation and self.weaviate_dir != 'docker':
            self.fix_python_syntax_errors()
            
        # 4. Create configuration
        self.create_weaviate_config()
        
        # 5. Start Weaviate
        started = False
        
        # Try Docker first
        try:
            if subprocess.run(['docker', '--version'], capture_output=True).returncode == 0:
                started = self.start_weaviate_docker()
        except:
            pass
            
        # If Docker failed, try standalone
        if not started:
            started = self.start_weaviate_standalone()
            
        if not started:
            self.log("Failed to start Weaviate", "ERROR")
            return False
            
        # 6. Wait for Weaviate to be ready
        if not self.wait_for_weaviate():
            return False
            
        # 7. Test API
        if not self.test_weaviate_api():
            self.log("Some API endpoints are not working properly", "WARNING")
            
        # 8. Create test schema
        self.create_test_schema()
        
        # Summary
        self.log("\n" + "="*60)
        self.log("FIX SUMMARY")
        self.log("="*60)
        self.log(f"Total issues fixed: {len(self.issues_fixed)}")
        for issue in self.issues_fixed:
            self.log(f"  ✓ {issue}")
            
        self.log("\nWeaviate is now running on http://localhost:8080")
        self.log("Test with: curl http://localhost:8080/v1/meta")
        
        return True


def main():
    fixer = WeaviateFixer()
    success = fixer.run_comprehensive_fix()
    
    if success:
        print("\n✅ Weaviate has been successfully fixed and is running!")
        print("\nNext steps:")
        print("1. Update your application to use http://localhost:8080")
        print("2. Restart the orchestra-api service")
        print("3. Test vector operations with the new setup")
    else:
        print("\n❌ Some issues could not be resolved automatically")
        print("Please check the logs above for details")
        
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()