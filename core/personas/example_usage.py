#!/usr/bin/env python3
"""
"""
    """Configure logging for the example."""
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def demonstrate_persona_loading(config_dir: Path) -> None:
    """
    """
    print(f"\n=== Loading Personas from {config_dir} ===")

    try:


        pass
        # Initialize the manager
        manager = PersonaConfigManager(config_dir)

        # Load all personas
        personas = manager.load_all_personas()
        print(f"Successfully loaded {len(personas)} personas")

        # List all personas
        print("\nAvailable Personas:")
        for persona in manager.list_personas():
            print(f"  - {persona.name} ({persona.slug}): {persona.description[:60]}...")

    except Exception:


        pass
        print(f"Error loading personas: {e}")

def demonstrate_persona_access(config_dir: Path) -> None:
    """
    """
    print("\n=== Accessing Specific Personas ===")

    manager = PersonaConfigManager(config_dir)
    manager.load_all_personas()

    # Access each persona
    for slug in ["cherry", "sophia", "karen"]:
        try:

            pass
            persona = manager.get_persona(slug)
            print(f"\n{persona.name}:")
            print(f"  Status: {persona.status}")
            print(f"  Interaction Mode: {persona.interaction_mode}")
            print(f"  Temperature: {persona.temperature}")
            print(f"  Traits: {len(persona.traits)}")
            print(f"  Knowledge Domains: {len(persona.knowledge_domains)}")

            # Show first trait
            if persona.traits:
                trait = persona.traits[0]
                print(f"  Primary Trait: {trait.name} (value: {trait.value})")

        except Exception:


            pass
            print(f"  Error: {e}")

def demonstrate_filtering(config_dir: Path) -> None:
    """
    """
    print("\n=== Filtering Personas ===")

    manager = PersonaConfigManager(config_dir)
    manager.load_all_personas()

    # Filter by status
    active_personas = manager.list_personas(status=PersonaStatus.ACTIVE)
    print(f"\nActive Personas: {len(active_personas)}")
    for persona in active_personas:
        print(f"  - {persona.name}")

    # Filter by tags
    strategic_personas = manager.list_personas(tags=["strategic"])
    print(f"\nStrategic Personas: {len(strategic_personas)}")
    for persona in strategic_personas:
        print(f"  - {persona.name}")

def demonstrate_persona_details(config_dir: Path, slug: str = "cherry") -> None:
    """
    """
    print(f"\n=== Detailed View: {slug} ===")

    manager = PersonaConfigManager(config_dir)
    manager.load_all_personas()

    try:


        pass
        persona = manager.get_persona(slug)

        # Basic info
        print(f"\nName: {persona.name}")
        print(f"Description: {persona.description}")
        print(f"Status: {persona.status}")
        print(f"Created by: {persona.created_by}")

        # Response style
        style = persona.response_style
        print(f"\nResponse Style:")
        print(f"  Type: {style.type}")
        print(f"  Tone: {style.tone}")
        print(f"  Formality: {style.formality_level}/10")
        print(f"  Verbosity: {style.verbosity}/10")

        # Traits
        print(f"\nTraits ({len(persona.traits)}):")
        for trait in persona.traits[:3]:  # Show first 3
            print(f"  - {trait.name}: {trait.value} (weight: {trait.weight})")

        # Knowledge domains
        print(f"\nKnowledge Domains ({len(persona.knowledge_domains)}):")
        for domain in persona.knowledge_domains:
            print(f"  - {domain.name} (expertise: {domain.expertise_level}/10)")
            print(f"    Topics: {', '.join(domain.topics[:3])}...")

        # Behavior rules
        if persona.behavior_rules:
            print(f"\nBehavior Rules ({len(persona.behavior_rules)}):")
            for rule in persona.behavior_rules[:2]:  # Show first 2
                print(f"  - {rule.name}")
                print(f"    Condition: {rule.condition}")
                print(f"    Action: {rule.action}")

        # Memory configuration
        if persona.memory_config:
            mem = persona.memory_config
            print(f"\nMemory Configuration:")
            print(f"  Retention: {mem.retention_period_hours} hours")
            print(f"  Max tokens: {mem.max_context_tokens}")
            print(f"  Priority topics: {', '.join(mem.priority_topics[:3])}...")

    except Exception:


        pass
        print(f"Error: {e}")

def demonstrate_validation(config_dir: Path) -> None:
    """
    """
    print("\n=== Validating Personas ===")

    manager = PersonaConfigManager(config_dir)
    manager.load_all_personas()

    issues = manager.validate_all()

    if not issues:
        print("All personas passed validation!")
    else:
        print("Validation issues found:")
        for slug, persona_issues in issues.items():
            print(f"\n{slug}:")
            for issue in persona_issues:
                print(f"  - {issue}")

def demonstrate_export(config_dir: Path, output_dir: Optional[Path] = None) -> None:
    """
    """
    print("\n=== Exporting Persona ===")

    if output_dir is None:
        import tempfile

        output_dir = Path(tempfile.gettempdir())

    manager = PersonaConfigManager(config_dir)
    manager.load_all_personas()

    # Export Cherry persona
    export_path = output_dir / "cherry_exported.yaml"
    try:

        pass
        manager.export_persona("cherry", export_path)
        print(f"Successfully exported Cherry persona to: {export_path}")

        # Show file size
        size = export_path.stat().st_size
        print(f"Exported file size: {size} bytes")

    except Exception:


        pass
        print(f"Error exporting: {e}")

def main() -> None:
    """Run all demonstrations."""
    print("PersonaConfigManager Example Usage")
    print("=" * 50)

    # Check if personas_detailed.yaml exists
    yaml_file = config_dir / "personas_detailed.yaml"
    if not yaml_file.exists():
        print(f"\nError: {yaml_file} not found!")
        print("Please ensure personas_detailed.yaml is in the same directory.")
        return

    # Run demonstrations
    demonstrate_persona_loading(config_dir)
    demonstrate_persona_access(config_dir)
    demonstrate_filtering(config_dir)
    demonstrate_persona_details(config_dir, "cherry")
    demonstrate_persona_details(config_dir, "sophia")
    demonstrate_validation(config_dir)
    demonstrate_export(config_dir)

    print("\n" + "=" * 50)
    print("Example completed!")

if __name__ == "__main__":
    main()
