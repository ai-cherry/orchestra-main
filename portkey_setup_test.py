import requests
import json
import os

# Portkey API Configuration
PORTKEY_API_KEY = "hPxFZGd8AN269n4bznDf2/Onbi8I"
PORTKEY_CONFIG = "pc-portke-b43e56"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

def test_portkey_connection():
    """Test Portkey API connection and retrieve account info"""
    headers = {
        "Authorization": f"Bearer {PORTKEY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test basic connection
        response = requests.get(f"{PORTKEY_BASE_URL}/configs", headers=headers)
        print(f"Connection Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Portkey API connection successful!")
            configs = response.json()
            print(f"Available configs: {len(configs.get('data', []))}")
            return True
        else:
            print(f"❌ Connection failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def create_persona_configs():
    """Create optimized configurations for each persona"""
    
    # Sophia - Business & Apartment Technology Focus
    sophia_config = {
        "name": "sophia-business-analyst",
        "description": "Sophia persona optimized for business analysis, apartment technology, fintech, and debt recovery",
        "models": [
            {
                "model": "claude-3-5-sonnet-20241022",
                "provider": "anthropic",
                "weight": 70,
                "fallbacks": ["gpt-4-turbo", "claude-3-opus-20240229"]
            }
        ],
        "routing": {
            "strategy": "performance-optimized",
            "fallback_strategy": "smart-routing"
        },
        "guardrails": {
            "input_filters": ["business-context-enhancer"],
            "output_filters": ["business-relevance-scorer"]
        },
        "metadata": {
            "persona": "sophia",
            "domain_focus": ["apartment-technology", "fintech", "debt-recovery", "residential-rent"],
            "search_bias": "business-focused"
        }
    }
    
    # Karen - Clinical Research & Healthcare Focus  
    karen_config = {
        "name": "karen-clinical-researcher",
        "description": "Karen persona optimized for clinical research, pharma, and healthcare analysis",
        "models": [
            {
                "model": "claude-3-opus-20240229", 
                "provider": "anthropic",
                "weight": 80,
                "fallbacks": ["gpt-4-turbo", "claude-3-5-sonnet-20241022"]
            }
        ],
        "routing": {
            "strategy": "accuracy-optimized",
            "fallback_strategy": "smart-routing"
        },
        "guardrails": {
            "input_filters": ["clinical-context-enhancer"],
            "output_filters": ["medical-accuracy-validator"]
        },
        "metadata": {
            "persona": "karen",
            "domain_focus": ["clinical-research", "clinical-studies", "pharma", "healthcare"],
            "search_bias": "clinical-focused"
        }
    }
    
    # Cherry - Balanced General Assistant
    cherry_config = {
        "name": "cherry-general-assistant",
        "description": "Cherry persona with balanced capabilities and adaptive learning",
        "models": [
            {
                "model": "gpt-4-turbo",
                "provider": "openai", 
                "weight": 60,
                "fallbacks": ["claude-3-5-sonnet-20241022", "gpt-4o"]
            }
        ],
        "routing": {
            "strategy": "balanced",
            "fallback_strategy": "cost-optimized"
        },
        "guardrails": {
            "input_filters": ["adaptive-context-enhancer"],
            "output_filters": ["balanced-relevance-scorer"]
        },
        "metadata": {
            "persona": "cherry",
            "domain_focus": ["general", "adaptive", "cross-domain"],
            "search_bias": "balanced-adaptive"
        }
    }
    
    return [sophia_config, karen_config, cherry_config]

def create_search_mode_configs():
    """Create configurations for different search modes"""
    
    search_modes = {
        "normal": {
            "name": "normal-search",
            "description": "Standard web search with basic AI enhancement",
            "tools": ["brave-search", "duckduckgo", "exa-ai"],
            "depth": "surface",
            "sources": 5,
            "timeout": 10
        },
        
        "deep": {
            "name": "deep-search", 
            "description": "Enhanced search with multiple sources and AI analysis",
            "tools": ["brave-search", "serpa", "google", "exa-ai", "perplexity"],
            "depth": "deep",
            "sources": 15,
            "timeout": 30
        },
        
        "super_deep": {
            "name": "super-deep-search",
            "description": "Comprehensive search with scraping and specialized sources",
            "tools": ["all-search-apis", "zenrows", "apify", "phantom-buster", "browser-use"],
            "depth": "comprehensive",
            "sources": 50,
            "timeout": 120,
            "scraping": True
        },
        
        "creative": {
            "name": "creative-search",
            "description": "Creative and lateral thinking search approach",
            "tools": ["exa-ai", "perplexity", "venice-ai"],
            "depth": "creative",
            "sources": 10,
            "timeout": 20,
            "creativity_boost": True
        },
        
        "private": {
            "name": "private-search",
            "description": "Privacy-focused search with anonymization",
            "tools": ["duckduckgo", "brave-search", "tor-enabled"],
            "depth": "private",
            "sources": 8,
            "timeout": 25,
            "privacy_mode": True
        },
        
        "uncensored": {
            "name": "uncensored-search",
            "description": "Unrestricted search with minimal filtering",
            "tools": ["venice-ai", "uncensored-sources", "dark-web-search"],
            "depth": "unrestricted", 
            "sources": 20,
            "timeout": 45,
            "content_filtering": "minimal"
        }
    }
    
    return search_modes

if __name__ == "__main__":
    print("🔧 Testing Portkey API Connection...")
    if test_portkey_connection():
        print("\n📋 Creating persona configurations...")
        personas = create_persona_configs()
        
        print("\n🔍 Creating search mode configurations...")
        search_modes = create_search_mode_configs()
        
        print("\n✅ Configuration templates created successfully!")
        print(f"Personas: {len(personas)}")
        print(f"Search modes: {len(search_modes)}")
    else:
        print("❌ Failed to connect to Portkey API")

