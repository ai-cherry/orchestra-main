"""
"""
    id="default",
    name="Default",
    description="A standard default persona for when no specific persona is selected or available.",
    traits=PersonaTraits(creativity=50, analytical_thinking=50),
    system_prompt="You are a helpful AI assistant. Please provide accurate and informative responses to user queries.",
)

# Dictionary of fallback personas
FALLBACK_PERSONAS = {
    "default": DEFAULT_PERSONA,
    "cherry": PersonaConfig(
        id="cherry",
        name="Cherry",
        description="A cheerful and optimistic persona with a focus on positive thinking.",
        traits=PersonaTraits(creativity=80, social_awareness=70, adaptability=60),
        system_prompt="You are Cherry, a cheerful and optimistic AI assistant. Always approach problems with positivity and encourage users while providing helpful solutions.",
    ),
    "sage": PersonaConfig(
        id="sage",
        name="Sage",
        description="A wise and thoughtful persona with a focus on careful analysis.",
        traits=PersonaTraits(analytical_thinking=90, technical_depth=80, detail_orientation=85),
        system_prompt="You are Sage, a wise and thoughtful AI assistant. Take time to carefully consider problems and provide well-reasoned, strategic advice.",
    ),
    "wit": PersonaConfig(
        id="wit",
        name="Wit",
        description="A clever and quick-witted persona with a sharp sense of humor.",
        traits=PersonaTraits(creativity=85, social_awareness=75, adaptability=70),
        system_prompt="You are Wit, a clever and quick-witted AI assistant. Use humor and wordplay appropriately while providing insightful and creative solutions.",
    ),
}

class PersonaManager:
    """
    """
        """
        """
        self._default_id = "default"
        self._last_loaded = 0
        self._auto_reload = auto_reload
        self._cache_ttl_seconds = cache_ttl_seconds

        # Load personas immediately
        self._load_personas()

        logger.info(
            f"PersonaManager initialized with {len(self._personas)} personas, "
            f"default: {self._default_id}, auto_reload: {auto_reload}"
        )

    def get_persona(self, persona_id: Optional[str] = None) -> PersonaConfig:
        """
        """
            logger.warning(f"Persona '{persona_id}' not found, using default: {self._default_id}")
            return self._personas[self._default_id]

        # If still not found, use fallback
        if "default" in FALLBACK_PERSONAS:
            logger.warning("No personas available, using fallback: default")
            return FALLBACK_PERSONAS["default"]

        # If all else fails, raise an error
        raise KeyError(f"Persona '{persona_id}' not found and no default available")

    def get_all_personas(self) -> Dict[str, PersonaConfig]:
        """
        """
        """
        """
        """
        """
        """
        """
                    logger.warning(f"Persona config file not found: {config_path}")
                    self._last_loaded = time.time()
                    return False

                # Load and parse YAML
                with open(config_path, "r") as f:
                    yaml_data = yaml.safe_load(f) or {}

                # Extract personas section
                yaml_personas = yaml_data.get("personas", {})

                if not yaml_personas:
                    logger.warning(f"No personas found in config file: {config_path}")
                else:
                    # Parse each persona
                    for persona_id, persona_data in yaml_personas.items():
                        try:

                            pass
                            # Create and validate the persona
                            persona = PersonaConfig(**persona_data)

                            # Add to personas dictionary
                            personas_dict[persona_id] = persona
                        except Exception:

                            pass
                            logger.error(f"Failed to load persona {persona_id}: {e}")

                    # Get default persona ID
                    default_id = yaml_data.get("default_persona_id", "default")
                    if default_id in personas_dict:
                        self._default_id = default_id

                    logger.info(f"Loaded {len(yaml_personas)} personas from {config_path}")
            except Exception:

                pass
                logger.error(f"Failed to load personas from {self._config_path}: {e}")
                self._last_loaded = time.time()
                return False

        # Update personas dictionary
        self._personas = personas_dict
        self._last_loaded = time.time()

        # Ensure default persona exists
        if self._default_id not in self._personas and self._personas:
            # Pick first persona as default
            self._default_id = next(iter(self._personas))
            logger.warning(f"Default persona ID not found, using {self._default_id} as default")

        return True
