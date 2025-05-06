"""
Simple validation script for the configuration module.
"""

# Try to import the settings and persona config loader
try:
    from core.orchestrator.src.config.config import settings, load_all_persona_configs
    
    print("✅ Successfully imported settings from config module")
    print(f"✅ APP_NAME: {settings.APP_NAME}")
    print(f"✅ ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"✅ REDIS_HOST: {settings.REDIS_HOST}")
    
    # Load persona configs
    personas = load_all_persona_configs()
    print(f"\n✅ Successfully loaded {len(personas)} personas:")
    
    for name, persona in personas.items():
        print(f"  - {name}: {persona.name}, {persona.age} years old")
        print(f"    Traits: {', '.join([f'{k}: {v}' for k, v in persona.traits.items()])}")
        print(f"    Style: {persona.interaction_style}")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
