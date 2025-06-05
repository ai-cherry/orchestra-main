import os
#!/usr/bin/env python3
"""
Vultr API Management Script for Orchestra-Main Project
Manages server infrastructure via Vultr API
"""

import requests
import json
import time
from typing import Dict, List, Optional

class VultrManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.vultr.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def list_instances(self, main_ip: Optional[str] = None) -> Dict:
        """List all instances, optionally filter by main IP"""
        url = f"{self.base_url}/instances"
        params = {}
        if main_ip:
            params["main_ip"] = main_ip
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_instance(self, instance_id: str) -> Dict:
        """Get detailed information about a specific instance"""
        url = f"{self.base_url}/instances/{instance_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def reboot_instance(self, instance_id: str) -> bool:
        """Reboot a specific instance"""
        url = f"{self.base_url}/instances/reboot"
        data = {"instance_ids": [instance_id]}
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.status_code == 204
    
    def find_instance_by_ip(self, target_ip: str) -> Optional[Dict]:
        """Find instance by IP address"""
        instances = self.list_instances()
        
        for instance in instances.get("instances", []):
            if instance.get("main_ip") == target_ip:
                return instance
        return None
    
    def get_server_plans(self) -> Dict:
        """Get available server plans"""
        url = f"{self.base_url}/plans"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_regions(self) -> Dict:
        """Get available regions"""
        url = f"{self.base_url}/regions"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

def main():
    # Initialize Vultr manager with API key
api_key = os.getenv('ORCHESTRA_INFRA_API_KEY')
    vultr = VultrManager(api_key)
    
    target_ip = "45.32.69.157"
    
    print("🔍 Orchestra-Main Server Management")
    print("=" * 50)
    
    try:
        # Find the current server
        print(f"🔎 Looking for server with IP: {target_ip}")
        instance = vultr.find_instance_by_ip(target_ip)
        
        if not instance:
            print(f"❌ No instance found with IP {target_ip}")
            return
        
        instance_id = instance["id"]
        print(f"✅ Found instance: {instance_id}")
        print(f"📊 Current status: {instance.get('status', 'unknown')}")
        print(f"💰 Plan: {instance.get('plan', 'unknown')}")
        print(f"🌍 Region: {instance.get('region', 'unknown')}")
        print(f"💾 RAM: {instance.get('ram', 'unknown')} MB")
        print(f"💽 Disk: {instance.get('disk', 'unknown')} GB")
        print(f"⚡ vCPUs: {instance.get('vcpu_count', 'unknown')}")
        
        # Check if server is rate limited or having issues
        if instance.get("server_status") == "installingbooting" or instance.get("power_status") != "running":
            print("⚠️  Server appears to have issues")
        
        # Reboot the server to fix rate limiting
        print(f"\n🔄 Rebooting server to fix rate limiting...")
        reboot_success = vultr.reboot_instance(instance_id)
        
        if reboot_success:
            print("✅ Reboot command sent successfully!")
            print("⏳ Waiting for server to restart...")
            
            # Wait and check status
            for i in range(12):  # Wait up to 2 minutes
                # TODO: Replace with asyncio.sleep() for async code
                time.sleep(10)
                updated_instance = vultr.get_instance(instance_id)["instance"]
                status = updated_instance.get("status", "unknown")
                power_status = updated_instance.get("power_status", "unknown")
                
                print(f"   Status: {status}, Power: {power_status}")
                
                if status == "active" and power_status == "running":
                    print("🎉 Server is back online!")
                    break
            else:
                print("⚠️  Server is still restarting, but reboot was initiated")
        else:
            print("❌ Failed to reboot server")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

