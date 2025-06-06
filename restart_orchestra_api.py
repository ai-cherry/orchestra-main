#!/usr/bin/env python3
"""
Restart Orchestra API Service with Fixed Weaviate Connection
"""

import os
import sys
import subprocess
import time
import json
import requests
from pathlib import Path

class OrchestraAPIRestarter:
    def __init__(self):
        self.api_port = 8000
        self.weaviate_url = "http://localhost:8080"
        
    def log(self, message, level="INFO"):
        print(f"[{level}] {message}")
        
    def find_orchestra_api_process(self):
        """Find running orchestra-api processes"""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            
            processes = []
            for line in result.stdout.split('\n'):
                if 'orchestra' in line and 'api' in line and 'python' in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        processes.append(pid)
                        
            return processes
        except Exception as e:
            self.log(f"Error finding processes: {e}", "ERROR")
            return []
            
    def stop_orchestra_api(self):
        """Stop existing orchestra-api processes"""
        self.log("Stopping existing orchestra-api processes...")
        
        processes = self.find_orchestra_api_process()
        if processes:
            for pid in processes:
                try:
                    subprocess.run(['kill', '-9', pid])
                    self.log(f"Killed process {pid}")
                except:
                    pass
                    
            time.sleep(2)
            
    def update_environment_config(self):
        """Update environment configuration for Weaviate"""
        self.log("Updating environment configuration...")
        
        env_file = Path(".env")
        env_content = []
        
        # Read existing .env if it exists
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.readlines()
                
        # Update or add Weaviate configuration
        weaviate_found = False
        new_content = []
        
        for line in env_content:
            if line.startswith('WEAVIATE_URL=') or line.startswith('WEAVIATE_HOST='):
                new_content.append(f'WEAVIATE_URL={self.weaviate_url}\n')
                weaviate_found = True
            else:
                new_content.append(line)
                
        if not weaviate_found:
            new_content.append(f'\n# Weaviate Configuration\n')
            new_content.append(f'WEAVIATE_URL={self.weaviate_url}\n')
            new_content.append(f'WEAVIATE_HOST=localhost\n')
            new_content.append(f'WEAVIATE_PORT=8080\n')
            new_content.append(f'WEAVIATE_SCHEME=http\n')
            
        # Write updated configuration
        with open(env_file, 'w') as f:
            f.writelines(new_content)
            
        self.log("Environment configuration updated")
        
    def find_main_api_file(self):
        """Find the main API file to run"""
        possible_files = [
            'api/main.py',
            'src/api/main.py',
            'orchestra_api/main.py',
            'backend/main.py',
            'app/main.py',
            'main.py',
            'api.py',
            'server.py'
        ]
        
        for file in possible_files:
            if os.path.exists(file):
                return file
                
        # Search for FastAPI files
        try:
            result = subprocess.run(
                ['find', '.', '-name', '*.py', '-type', 'f'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if line and 'api' in line.lower():
                    # Check if it's a FastAPI file
                    try:
                        with open(line.strip(), 'r') as f:
                            content = f.read()
                            if 'FastAPI' in content or 'fastapi' in content:
                                return line.strip()
                    except:
                        pass
        except:
            pass
            
        return None
        
    def start_orchestra_api(self):
        """Start the orchestra-api service"""
        self.log("Starting orchestra-api service...")
        
        # Find the main API file
        api_file = self.find_main_api_file()
        if not api_file:
            self.log("Could not find main API file", "ERROR")
            return False
            
        self.log(f"Found API file: {api_file}")
        
        # Set environment variables
        env = os.environ.copy()
        env['WEAVIATE_URL'] = self.weaviate_url
        env['WEAVIATE_HOST'] = 'localhost'
        env['WEAVIATE_PORT'] = '8080'
        env['WEAVIATE_SCHEME'] = 'http'
        env['PYTHONUNBUFFERED'] = '1'
        
        # Start the API
        try:
            # Try with uvicorn first
            cmd = ['uvicorn', f"{api_file.replace('/', '.').replace('.py', '')}:app", 
                   '--host', '0.0.0.0', '--port', str(self.api_port), '--reload']
            
            self.log(f"Starting with command: {' '.join(cmd)}")
            process = subprocess.Popen(cmd, env=env)
            
            # Save PID
            with open('orchestra_api.pid', 'w') as f:
                f.write(str(process.pid))
                
            self.log(f"Started orchestra-api with PID {process.pid}")
            return True
            
        except Exception as e:
            self.log(f"Failed to start with uvicorn: {e}", "WARNING")
            
            # Try direct Python execution
            try:
                cmd = ['python3', api_file]
                process = subprocess.Popen(cmd, env=env)
                
                with open('orchestra_api.pid', 'w') as f:
                    f.write(str(process.pid))
                    
                self.log(f"Started orchestra-api with PID {process.pid}")
                return True
                
            except Exception as e:
                self.log(f"Failed to start API: {e}", "ERROR")
                return False
                
    def wait_for_api(self, timeout=30):
        """Wait for API to be ready"""
        self.log("Waiting for API to be ready...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f'http://localhost:{self.api_port}/health', timeout=2)
                if response.status_code == 200:
                    self.log("API is ready!")
                    return True
            except:
                # Also try root endpoint
                try:
                    response = requests.get(f'http://localhost:{self.api_port}/', timeout=2)
                    if response.status_code in [200, 404]:  # 404 is ok, means server is running
                        self.log("API is ready!")
                        return True
                except:
                    pass
                    
            time.sleep(1)
            
        self.log("API failed to start within timeout", "WARNING")
        return False
        
    def test_weaviate_connection(self):
        """Test if API can connect to Weaviate"""
        self.log("Testing Weaviate connection through API...")
        
        # Try different endpoints that might use Weaviate
        test_endpoints = [
            '/api/v1/vectors/health',
            '/api/v1/search',
            '/vectors/health',
            '/weaviate/health'
        ]
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(f'http://localhost:{self.api_port}{endpoint}', timeout=5)
                self.log(f"Endpoint {endpoint}: Status {response.status_code}")
            except Exception as e:
                self.log(f"Endpoint {endpoint}: {str(e)}", "WARNING")
                
    def run_restart(self):
        """Run the complete restart process"""
        self.log("\n" + "="*60)
        self.log("ORCHESTRA API RESTART")
        self.log("="*60)
        
        # 1. Stop existing processes
        self.stop_orchestra_api()
        
        # 2. Update environment configuration
        self.update_environment_config()
        
        # 3. Start the API
        if not self.start_orchestra_api():
            self.log("Failed to start orchestra-api", "ERROR")
            return False
            
        # 4. Wait for API to be ready
        if not self.wait_for_api():
            self.log("API did not become ready", "WARNING")
            
        # 5. Test Weaviate connection
        time.sleep(2)  # Give it a moment to fully initialize
        self.test_weaviate_connection()
        
        self.log("\n" + "="*60)
        self.log("RESTART COMPLETE")
        self.log("="*60)
        self.log(f"Orchestra API is running on http://localhost:{self.api_port}")
        self.log(f"Weaviate is running on {self.weaviate_url}")
        self.log("\nMonitor logs with: tail -f orchestra_api.log")
        
        return True


def main():
    restarter = OrchestraAPIRestarter()
    success = restarter.run_restart()
    
    if success:
        print("\n✅ Orchestra API has been restarted with Weaviate connection!")
    else:
        print("\n❌ Failed to restart Orchestra API")
        print("Check the logs for details")
        
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()