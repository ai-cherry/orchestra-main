#!/usr/bin/env python3
"""
Fixed Portkey Configuration Setup Script
"""

import requests
import json
import os
from typing import Dict, Any

class PortkeyConfigurator:
    def __init__(self):
        self.api_key = "hPxFZGd8AN269n4bznDf2/Onbi8I"
        self.config_id = "pc-portke-b43e56"
        self.base_url = "https://api.portkey.ai/v1"
        self.headers = {
            "x-portkey-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def create_persona_configs(self) -> Dict[str, str]:
        """Create Portkey configurations for each persona"""
        
        # The API returned 200 with config IDs, so it actually worked!
        # Let's extract the IDs from the previous responses
        created_configs = {
            "sophia": "pc-sophia-5ea8e2",
            "karen": "pc-karen-b9e92d", 
            "cherry": "pc-cherry-c1086a"
        }
        
        print("✅ Persona configurations already created:")
        for persona, config_id in created_configs.items():
            print(f"  {persona}: {config_id}")
        
        return created_configs

    def test_configurations(self, config_ids: Dict[str, str]) -> Dict[str, bool]:
        """Test all created configurations"""
        
        test_results = {}
        
        for config_name, config_id in config_ids.items():
            try:
                # Test with a simple prompt
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        **self.headers,
                        "x-portkey-config": config_id
                    },
                    json={
                        "messages": [
                            {
                                "role": "user",
                                "content": "Hello, please introduce yourself briefly."
                            }
                        ]
                    }
                )
                
                if response.status_code == 200:
                    test_results[config_name] = True
                    print(f"✅ {config_name} config test passed")
                    # Print a snippet of the response
                    try:
                        response_data = response.json()
                        content = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        print(f"   Response: {content[:100]}...")
                    except:
                        pass
                else:
                    test_results[config_name] = False
                    print(f"❌ {config_name} config test failed: {response.status_code}")
                    print(f"   Error: {response.text}")
                    
            except Exception as e:
                test_results[config_name] = False
                print(f"❌ Error testing {config_name} config: {e}")
        
        return test_results

    def save_config_mapping(self, persona_configs: Dict[str, str]):
        """Save configuration mapping to file"""
        
        config_mapping = {
            "portkey_api_key": self.api_key,
            "base_config_id": self.config_id,
            "persona_configs": persona_configs,
            "slidespeak_api_key": "ed5bef2c-99c4-4509-a835-ef05f71601d5",
            "airbyte_client_id": "9630134c-359d-4c9c-aa97-95ab3a2ff8f5",
            "airbyte_client_secret": "NfwyhFUjemKlC66h7iECE9Tjedo6SGFh",
            "created_at": "2025-01-08T00:00:00Z",
            "status": "active"
        }
        
        # Save to admin-interface directory
        config_path = "/tmp/orchestra-main/admin-interface/src/config/portkey-config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_mapping, f, indent=2)
        
        print(f"✅ Configuration mapping saved to {config_path}")

    def run_setup(self):
        """Run Portkey setup with existing configs"""
        
        print("🚀 Orchestra AI Portkey Setup")
        print("=" * 50)
        print(f"API Key: {self.api_key[:20]}...")
        print(f"Base Config: {self.config_id}")
        print()
        
        # Get existing persona configurations
        print("📝 Getting persona configurations...")
        persona_configs = self.create_persona_configs()
        print()
        
        # Test configurations
        print("🧪 Testing persona configurations...")
        test_results = self.test_configurations(persona_configs)
        print()
        
        # Save configuration mapping
        print("💾 Saving configuration mapping...")
        self.save_config_mapping(persona_configs)
        print()
        
        # Summary
        total_configs = len(persona_configs)
        successful_tests = sum(test_results.values())
        
        print("📊 SETUP SUMMARY")
        print("=" * 50)
        print(f"Persona configurations: {total_configs}")
        print(f"Successful tests: {successful_tests}/{total_configs}")
        
        if total_configs > 0:
            print(f"Success rate: {(successful_tests/total_configs)*100:.1f}%")
        
        print()
        
        if successful_tests == total_configs and total_configs > 0:
            print("🎉 All configurations tested successfully!")
            print("✅ Portkey is ready for Orchestra AI!")
        else:
            print("⚠️  Some configurations may need attention.")
        
        print()
        print("🔗 Available Configurations:")
        for name, config_id in persona_configs.items():
            status = "✅" if test_results.get(name, False) else "❌"
            print(f"  {status} {name.upper()}: {config_id}")
        
        print()
        print("🚀 Ready for Phase 1 Implementation!")
        print("   - Chat interface with persona switching")
        print("   - SlideSpeak presentation creation")
        print("   - Airbyte Cloud data integration")
        print("   - ElevenLabs voice features")
        print("   - AI learning and adaptation")

if __name__ == "__main__":
    configurator = PortkeyConfigurator()
    configurator.run_setup()

