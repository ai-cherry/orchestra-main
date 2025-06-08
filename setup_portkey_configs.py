#!/usr/bin/env python3
"""
Portkey Configuration Setup Script
Sets up all Portkey configurations for Orchestra AI admin website
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
        
        configs = {
            "sophia": {
                "name": "Sophia Business Intelligence",
                "description": "Business intelligence and market analysis persona",
                "config": {
                    "strategy": {
                        "mode": "loadbalance"
                    },
                    "targets": [
                        {
                            "provider": "anthropic",
                            "api_key": "{{ANTHROPIC_API_KEY}}",
                            "override_params": {
                                "model": "claude-3-5-sonnet-20241022",
                                "temperature": 0.3,
                                "max_tokens": 4000,
                                "system": "You are Sophia, a business intelligence expert specializing in apartment technology, fintech, debt recovery, and proptech. Provide data-driven insights with professional analysis. Always ask clarifying questions when needed."
                            },
                            "weight": 0.8
                        },
                        {
                            "provider": "openai",
                            "api_key": "{{OPENAI_API_KEY}}",
                            "override_params": {
                                "model": "gpt-4o-2024-11-20",
                                "temperature": 0.2,
                                "max_tokens": 4000
                            },
                            "weight": 0.2
                        }
                    ]
                }
            },
            
            "karen": {
                "name": "Karen Clinical Research",
                "description": "Clinical research and pharmaceutical analysis persona",
                "config": {
                    "strategy": {
                        "mode": "loadbalance"
                    },
                    "targets": [
                        {
                            "provider": "anthropic",
                            "api_key": "{{ANTHROPIC_API_KEY}}",
                            "override_params": {
                                "model": "claude-3-opus-20240229",
                                "temperature": 0.1,
                                "max_tokens": 4000,
                                "system": "You are Karen, a clinical research specialist with expertise in pharmaceutical studies, medical literature, and regulatory compliance. Provide precise, evidence-based analysis. Always ask clarifying questions when needed."
                            },
                            "weight": 0.9
                        },
                        {
                            "provider": "openai",
                            "api_key": "{{OPENAI_API_KEY}}",
                            "override_params": {
                                "model": "gpt-4o-mini",
                                "temperature": 0.1,
                                "max_tokens": 4000
                            },
                            "weight": 0.1
                        }
                    ]
                }
            },
            
            "cherry": {
                "name": "Cherry Creative Assistant",
                "description": "Creative and cross-domain innovation persona",
                "config": {
                    "strategy": {
                        "mode": "loadbalance"
                    },
                    "targets": [
                        {
                            "provider": "openai",
                            "api_key": "{{OPENAI_API_KEY}}",
                            "override_params": {
                                "model": "gpt-4o-2024-11-20",
                                "temperature": 0.8,
                                "max_tokens": 4000,
                                "system": "You are Cherry, a creative assistant specializing in cross-domain innovation, content creation, and artistic projects. Provide imaginative solutions while learning from all interactions. Always ask clarifying questions when needed."
                            },
                            "weight": 0.7
                        },
                        {
                            "provider": "anthropic",
                            "api_key": "{{ANTHROPIC_API_KEY}}",
                            "override_params": {
                                "model": "claude-3-5-sonnet-20241022",
                                "temperature": 0.7,
                                "max_tokens": 4000
                            },
                            "weight": 0.3
                        }
                    ]
                }
            }
        }

        created_configs = {}
        
        for persona, config_data in configs.items():
            try:
                # Create config via Portkey API
                response = requests.post(
                    f"{self.base_url}/configs",
                    headers=self.headers,
                    json={
                        "name": config_data["name"],
                        "description": config_data["description"],
                        "config": config_data["config"]
                    }
                )
                
                if response.status_code == 201:
                    config_id = response.json().get("id")
                    created_configs[persona] = config_id
                    print(f"✅ Created {persona} config: {config_id}")
                else:
                    print(f"❌ Failed to create {persona} config: {response.status_code}")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error creating {persona} config: {e}")
        
        return created_configs

    def setup_search_configs(self) -> Dict[str, str]:
        """Setup search-specific configurations"""
        
        search_configs = {
            "normal_search": {
                "name": "Normal Search Mode",
                "description": "Quick search with basic results",
                "config": {
                    "strategy": {
                        "mode": "single"
                    },
                    "targets": [
                        {
                            "provider": "openai",
                            "api_key": "{{OPENAI_API_KEY}}",
                            "override_params": {
                                "model": "gpt-4o-mini",
                                "temperature": 0.2,
                                "max_tokens": 1000
                            }
                        }
                    ]
                }
            },
            
            "deep_search": {
                "name": "Deep Search Mode",
                "description": "Comprehensive search with detailed analysis",
                "config": {
                    "strategy": {
                        "mode": "single"
                    },
                    "targets": [
                        {
                            "provider": "anthropic",
                            "api_key": "{{ANTHROPIC_API_KEY}}",
                            "override_params": {
                                "model": "claude-3-5-sonnet-20241022",
                                "temperature": 0.1,
                                "max_tokens": 4000
                            }
                        }
                    ]
                }
            },
            
            "super_deep_search": {
                "name": "Super Deep Search Mode",
                "description": "Exhaustive search with multi-source analysis",
                "config": {
                    "strategy": {
                        "mode": "fallback"
                    },
                    "targets": [
                        {
                            "provider": "anthropic",
                            "api_key": "{{ANTHROPIC_API_KEY}}",
                            "override_params": {
                                "model": "claude-3-opus-20240229",
                                "temperature": 0.1,
                                "max_tokens": 8000
                            }
                        },
                        {
                            "provider": "openai",
                            "api_key": "{{OPENAI_API_KEY}}",
                            "override_params": {
                                "model": "gpt-4o-2024-11-20",
                                "temperature": 0.1,
                                "max_tokens": 4000
                            }
                        }
                    ]
                }
            }
        }

        created_search_configs = {}
        
        for search_type, config_data in search_configs.items():
            try:
                response = requests.post(
                    f"{self.base_url}/configs",
                    headers=self.headers,
                    json={
                        "name": config_data["name"],
                        "description": config_data["description"],
                        "config": config_data["config"]
                    }
                )
                
                if response.status_code == 201:
                    config_id = response.json().get("id")
                    created_search_configs[search_type] = config_id
                    print(f"✅ Created {search_type} config: {config_id}")
                else:
                    print(f"❌ Failed to create {search_type} config: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error creating {search_type} config: {e}")
        
        return created_search_configs

    def setup_creative_configs(self) -> Dict[str, str]:
        """Setup creative task configurations"""
        
        creative_configs = {
            "presentation_creation": {
                "name": "Presentation Creation",
                "description": "Optimized for creating presentations",
                "config": {
                    "strategy": {
                        "mode": "single"
                    },
                    "targets": [
                        {
                            "provider": "anthropic",
                            "api_key": "{{ANTHROPIC_API_KEY}}",
                            "override_params": {
                                "model": "claude-3-5-sonnet-20241022",
                                "temperature": 0.4,
                                "max_tokens": 4000,
                                "system": "You are an expert presentation creator. Structure content logically, create compelling narratives, and optimize for visual presentation formats."
                            }
                        }
                    ]
                }
            },
            
            "content_generation": {
                "name": "Content Generation",
                "description": "Optimized for creative content creation",
                "config": {
                    "strategy": {
                        "mode": "single"
                    },
                    "targets": [
                        {
                            "provider": "openai",
                            "api_key": "{{OPENAI_API_KEY}}",
                            "override_params": {
                                "model": "gpt-4o-2024-11-20",
                                "temperature": 0.8,
                                "max_tokens": 4000,
                                "system": "You are a creative content generator. Produce engaging, original content across various formats including stories, songs, scripts, and creative writing."
                            }
                        }
                    ]
                }
            }
        }

        created_creative_configs = {}
        
        for creative_type, config_data in creative_configs.items():
            try:
                response = requests.post(
                    f"{self.base_url}/configs",
                    headers=self.headers,
                    json={
                        "name": config_data["name"],
                        "description": config_data["description"],
                        "config": config_data["config"]
                    }
                )
                
                if response.status_code == 201:
                    config_id = response.json().get("id")
                    created_creative_configs[creative_type] = config_id
                    print(f"✅ Created {creative_type} config: {config_id}")
                else:
                    print(f"❌ Failed to create {creative_type} config: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error creating {creative_type} config: {e}")
        
        return created_creative_configs

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
                else:
                    test_results[config_name] = False
                    print(f"❌ {config_name} config test failed: {response.status_code}")
                    
            except Exception as e:
                test_results[config_name] = False
                print(f"❌ Error testing {config_name} config: {e}")
        
        return test_results

    def save_config_mapping(self, all_configs: Dict[str, Dict[str, str]]):
        """Save configuration mapping to file"""
        
        config_mapping = {
            "portkey_api_key": self.api_key,
            "base_config_id": self.config_id,
            "persona_configs": all_configs.get("personas", {}),
            "search_configs": all_configs.get("search", {}),
            "creative_configs": all_configs.get("creative", {}),
            "created_at": "2025-01-08T00:00:00Z"
        }
        
        # Save to admin-interface directory
        config_path = "/tmp/orchestra-main/admin-interface/src/config/portkey-config.json"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_mapping, f, indent=2)
        
        print(f"✅ Configuration mapping saved to {config_path}")

    def run_full_setup(self):
        """Run complete Portkey setup"""
        
        print("🚀 Starting Portkey configuration setup...")
        print(f"Using API Key: {self.api_key[:20]}...")
        print(f"Base Config ID: {self.config_id}")
        print()
        
        # Create all configurations
        print("📝 Creating persona configurations...")
        persona_configs = self.create_persona_configs()
        print()
        
        print("🔍 Creating search configurations...")
        search_configs = self.setup_search_configs()
        print()
        
        print("🎨 Creating creative configurations...")
        creative_configs = self.setup_creative_configs()
        print()
        
        # Combine all configs
        all_configs = {
            "personas": persona_configs,
            "search": search_configs,
            "creative": creative_configs
        }
        
        # Test configurations
        print("🧪 Testing configurations...")
        all_config_ids = {**persona_configs, **search_configs, **creative_configs}
        test_results = self.test_configurations(all_config_ids)
        print()
        
        # Save configuration mapping
        print("💾 Saving configuration mapping...")
        self.save_config_mapping(all_configs)
        print()
        
        # Summary
        total_configs = len(all_config_ids)
        successful_tests = sum(test_results.values())
        
        print("📊 SETUP SUMMARY")
        print("=" * 50)
        print(f"Total configurations created: {total_configs}")
        print(f"Successful tests: {successful_tests}/{total_configs}")
        print(f"Success rate: {(successful_tests/total_configs)*100:.1f}%")
        print()
        
        if successful_tests == total_configs:
            print("🎉 All configurations created and tested successfully!")
            print("✅ Portkey is ready for Orchestra AI admin website!")
        else:
            print("⚠️  Some configurations failed. Please check the errors above.")
        
        print()
        print("🔗 Configuration IDs:")
        for name, config_id in all_config_ids.items():
            status = "✅" if test_results.get(name, False) else "❌"
            print(f"  {status} {name}: {config_id}")

if __name__ == "__main__":
    configurator = PortkeyConfigurator()
    configurator.run_full_setup()

