import requests
import json
from datetime import datetime

# Working Portkey Configuration
PORTKEY_API_KEY = "hPxFZGd8AN269n4bznDf2/Onbi8I"
PORTKEY_CONFIG = "pc-portke-b43e56"
BASE_URL = "https://api.portkey.ai/v1"

HEADERS = {
    "x-portkey-api-key": PORTKEY_API_KEY,
    "Content-Type": "application/json"
}

def get_current_configs():
    """Retrieve current Portkey configurations"""
    try:
        response = requests.get(f"{BASE_URL}/configs", headers=HEADERS)
        if response.status_code == 200:
            configs = response.json()
            print(f"✅ Found {len(configs.get('data', []))} existing configs")
            return configs.get('data', [])
        else:
            print(f"❌ Failed to get configs: {response.text}")
            return []
    except Exception as e:
        print(f"💥 Error getting configs: {str(e)}")
        return []

def create_persona_config(persona_name, config_data):
    """Create a configuration for a specific persona"""
    try:
        response = requests.post(f"{BASE_URL}/configs", headers=HEADERS, json=config_data)
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✅ Created config for {persona_name}")
            return result
        else:
            print(f"❌ Failed to create {persona_name} config: {response.text}")
            return None
    except Exception as e:
        print(f"💥 Error creating {persona_name} config: {str(e)}")
        return None

def setup_sophia_config():
    """Setup Sophia's business-focused configuration"""
    config = {
        "name": "sophia-business-analyst",
        "description": "Sophia persona optimized for business analysis, apartment technology, fintech, and debt recovery",
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022",
        "config": {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 4000,
            "temperature": 0.3,
            "system": "You are Sophia, a business analyst specializing in apartment technology, residential rent management, fintech solutions, and debt recovery. You have deep expertise in property management software, tenant screening, payment processing, and financial technology for real estate. When conducting searches or analysis, prioritize business-focused sources and maintain a strategic perspective on market opportunities, competitive analysis, and operational efficiency.",
            "metadata": {
                "persona": "sophia",
                "domain_focus": ["apartment-technology", "fintech", "debt-recovery", "residential-rent", "proptech"],
                "search_bias": "business-focused",
                "expertise_areas": ["property_management", "tenant_screening", "payment_processing", "real_estate_fintech"]
            }
        },
        "fallbacks": [
            {
                "provider": "openai",
                "model": "gpt-4-turbo"
            },
            {
                "provider": "anthropic", 
                "model": "claude-3-opus-20240229"
            }
        ]
    }
    return create_persona_config("Sophia", config)

def setup_karen_config():
    """Setup Karen's clinical research configuration"""
    config = {
        "name": "karen-clinical-researcher",
        "description": "Karen persona optimized for clinical research, pharma, and healthcare analysis",
        "provider": "anthropic",
        "model": "claude-3-opus-20240229",
        "config": {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": "You are Karen, a clinical research specialist with expertise in pharmaceutical development, clinical studies, medical research, and healthcare analytics. You have deep knowledge of clinical trial design, regulatory compliance, drug development processes, and medical literature analysis. When conducting searches or analysis, prioritize peer-reviewed medical sources, clinical databases, and regulatory information. Maintain scientific rigor and evidence-based reasoning in all responses.",
            "metadata": {
                "persona": "karen",
                "domain_focus": ["clinical-research", "clinical-studies", "pharma", "healthcare", "medical-research"],
                "search_bias": "clinical-focused",
                "expertise_areas": ["clinical_trials", "drug_development", "medical_literature", "regulatory_compliance"]
            }
        },
        "fallbacks": [
            {
                "provider": "openai",
                "model": "gpt-4-turbo"
            },
            {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022"
            }
        ]
    }
    return create_persona_config("Karen", config)

def setup_cherry_config():
    """Setup Cherry's balanced general assistant configuration"""
    config = {
        "name": "cherry-general-assistant",
        "description": "Cherry persona with balanced capabilities and adaptive learning",
        "provider": "openai",
        "model": "gpt-4-turbo",
        "config": {
            "model": "gpt-4-turbo",
            "max_tokens": 4000,
            "temperature": 0.4,
            "system": "You are Cherry, a versatile AI assistant with balanced capabilities across multiple domains. You excel at adapting to different contexts and learning from interactions to provide increasingly personalized assistance. You maintain a helpful, friendly demeanor while being thorough and accurate. When conducting searches or analysis, you take a balanced approach that considers multiple perspectives and sources. You learn from user interactions to improve future responses and adapt your communication style to user preferences.",
            "metadata": {
                "persona": "cherry",
                "domain_focus": ["general", "adaptive", "cross-domain", "personalized"],
                "search_bias": "balanced-adaptive",
                "expertise_areas": ["general_assistance", "adaptive_learning", "cross_domain_knowledge", "personalization"]
            }
        },
        "fallbacks": [
            {
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022"
            },
            {
                "provider": "openai",
                "model": "gpt-4o"
            }
        ]
    }
    return create_persona_config("Cherry", config)

def create_search_mode_configs():
    """Create configurations for different search modes"""
    
    search_configs = {
        "normal_search": {
            "name": "normal-search-mode",
            "description": "Standard web search with basic AI enhancement",
            "config": {
                "search_depth": "surface",
                "max_sources": 5,
                "timeout": 10,
                "tools": ["brave-search", "duckduckgo", "exa-ai"],
                "content_filtering": "standard"
            }
        },
        
        "deep_search": {
            "name": "deep-search-mode",
            "description": "Enhanced search with multiple sources and AI analysis", 
            "config": {
                "search_depth": "deep",
                "max_sources": 15,
                "timeout": 30,
                "tools": ["brave-search", "serpa", "google", "exa-ai", "perplexity"],
                "content_filtering": "enhanced",
                "cross_reference": True
            }
        },
        
        "super_deep_search": {
            "name": "super-deep-search-mode",
            "description": "Comprehensive search with scraping and specialized sources",
            "config": {
                "search_depth": "comprehensive",
                "max_sources": 50,
                "timeout": 120,
                "tools": ["all-search-apis", "zenrows", "apify", "phantom-buster", "browser-use"],
                "content_filtering": "minimal",
                "scraping_enabled": True,
                "specialized_sources": ["crunchbase", "academic-databases", "industry-reports"]
            }
        },
        
        "creative_search": {
            "name": "creative-search-mode",
            "description": "Creative and lateral thinking search approach",
            "config": {
                "search_depth": "creative",
                "max_sources": 10,
                "timeout": 20,
                "tools": ["exa-ai", "perplexity", "venice-ai"],
                "content_filtering": "creative",
                "creativity_boost": True,
                "lateral_thinking": True
            }
        },
        
        "private_search": {
            "name": "private-search-mode",
            "description": "Privacy-focused search with anonymization",
            "config": {
                "search_depth": "private",
                "max_sources": 8,
                "timeout": 25,
                "tools": ["duckduckgo", "brave-search", "tor-enabled"],
                "content_filtering": "privacy-focused",
                "privacy_mode": True,
                "anonymization": True
            }
        },
        
        "uncensored_search": {
            "name": "uncensored-search-mode",
            "description": "Unrestricted search with minimal filtering",
            "config": {
                "search_depth": "unrestricted",
                "max_sources": 20,
                "timeout": 45,
                "tools": ["venice-ai", "uncensored-sources", "alternative-search"],
                "content_filtering": "minimal",
                "restrictions": "none"
            }
        }
    }
    
    created_search_configs = []
    for mode_name, config_data in search_configs.items():
        result = create_persona_config(f"Search Mode: {mode_name}", config_data)
        if result:
            created_search_configs.append(result)
    
    return created_search_configs

def setup_media_generation_configs():
    """Setup configurations for media generation capabilities"""
    
    media_configs = {
        "image_creation": {
            "name": "image-creation-mode",
            "description": "AI image generation and creation",
            "config": {
                "primary_tool": "midjourney",
                "fallbacks": ["recraft-ai", "dall-e-3"],
                "quality": "high",
                "style_adaptation": True
            }
        },
        
        "image_editing": {
            "name": "image-editing-mode", 
            "description": "AI image editing and enhancement",
            "config": {
                "primary_tool": "recraft-ai",
                "fallbacks": ["dall-e-3-edit", "photoshop-ai"],
                "precision": "high",
                "batch_processing": True
            }
        },
        
        "video_creation": {
            "name": "video-creation-mode",
            "description": "AI video generation and creation",
            "config": {
                "primary_tool": "mureka-ai",
                "fallbacks": ["runway-ml", "pika-labs"],
                "quality": "high",
                "duration_limit": 60
            }
        },
        
        "presentation_creation": {
            "name": "presentation-creation-mode",
            "description": "AI presentation generation",
            "config": {
                "primary_tool": "gamma",
                "fallbacks": ["beautiful-ai", "tome"],
                "template_variety": "extensive",
                "auto_design": True
            }
        },
        
        "audio_generation": {
            "name": "audio-generation-mode",
            "description": "AI audio and voice generation",
            "config": {
                "primary_tool": "eleven-labs",
                "fallbacks": ["murf", "speechify"],
                "voice_cloning": True,
                "quality": "studio"
            }
        }
    }
    
    created_media_configs = []
    for mode_name, config_data in media_configs.items():
        result = create_persona_config(f"Media: {mode_name}", config_data)
        if result:
            created_media_configs.append(result)
    
    return created_media_configs

def main():
    """Main setup function"""
    print("🚀 Setting up comprehensive Portkey configuration for Orchestra AI...")
    
    # Get current state
    print("\n📋 Checking current configurations...")
    current_configs = get_current_configs()
    
    # Setup persona configurations
    print("\n👥 Setting up persona configurations...")
    sophia_config = setup_sophia_config()
    karen_config = setup_karen_config() 
    cherry_config = setup_cherry_config()
    
    # Setup search mode configurations
    print("\n🔍 Setting up search mode configurations...")
    search_configs = create_search_mode_configs()
    
    # Setup media generation configurations
    print("\n🎨 Setting up media generation configurations...")
    media_configs = setup_media_generation_configs()
    
    # Summary
    print("\n📊 Setup Summary:")
    print(f"✅ Persona configs: {sum([1 for c in [sophia_config, karen_config, cherry_config] if c])}/3")
    print(f"✅ Search mode configs: {len(search_configs)}/6")
    print(f"✅ Media generation configs: {len(media_configs)}/5")
    
    total_configs = len([c for c in [sophia_config, karen_config, cherry_config] if c]) + len(search_configs) + len(media_configs)
    print(f"\n🎉 Total configurations created: {total_configs}")
    
    if total_configs > 0:
        print("\n✅ Portkey setup completed successfully!")
        print("🎯 Ready for Orchestra AI integration!")
    else:
        print("\n❌ Setup encountered issues - please check configuration")

if __name__ == "__main__":
    main()

