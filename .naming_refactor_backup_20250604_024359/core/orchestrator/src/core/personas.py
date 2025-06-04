"""
"""
    """
    """
    description: str = ""
    prompt_template: str = "{input}"
    background: str = ""
    interaction_style: str = "helpful"
    traits: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PersonaProcessor:
    """
    """
        """
        """
        """
        """
        format_vars = {"input": response_text, **kwargs}

        try:


            pass
            # Use string.format to apply the template
            return self.persona.prompt_template.format(**format_vars)
        except Exception:

            pass
            logger.warning(f"Missing format variable in template: {e}")
            # Fallback to basic substitution
            return self.persona.prompt_template.replace("{input}", response_text)
        except Exception:

            pass
            logger.error(f"Error formatting response: {e}")
            # Last resort fallback
            return response_text

class PersonaLoader:
    """
    """
        """
        """
        self.default_persona_id: str = "default"
        self._load_personas()

    def _load_personas(self) -> None:
        """Load personas from the configuration file."""
                logger.warning(f"Persona config file not found: {self.config_path}")
                self._create_default_persona()
                return

            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)

            if not config or not isinstance(config, dict):
                logger.warning(f"Invalid persona config file: {self.config_path}")
                self._create_default_persona()
                return

            # Get default persona ID
            self.default_persona_id = config.get("default_persona_id", "default")

            # Load personas
            persona_configs = config.get("personas", {})
            if not persona_configs:
                logger.warning(f"No personas found in config file: {self.config_path}")
                self._create_default_persona()
                return

            # Parse each persona
            for persona_id, persona_data in persona_configs.items():
                try:

                    pass
                    # Extract traits list if present
                    traits = persona_data.get("traits", [])
                    if isinstance(traits, list):
                        persona_data["traits"] = traits
                    else:
                        persona_data["traits"] = []

                    # Create persona config
                    persona = PersonaConfig(**persona_data)
                    self.personas[persona_id] = persona
                except Exception:

                    pass
                    logger.error(f"Failed to load persona {persona_id}: {e}")

            logger.info(f"Loaded {len(self.personas)} personas from {self.config_path}")

            # Ensure default persona exists
            if self.default_persona_id not in self.personas:
                logger.warning(f"Default persona '{self.default_persona_id}' not found, creating it")
                self._create_default_persona()
        except Exception:

            pass
            logger.error(f"Failed to load personas from {self.config_path}: {e}")
            self._create_default_persona()

    def _create_default_persona(self) -> None:
        """Create a default persona if none exists."""
        self.default_persona_id = "default"
        self.personas[self.default_persona_id] = PersonaConfig(
            name="Assistant",
            description="A helpful, knowledgeable assistant",
            prompt_template="{input}",
            interaction_style="helpful",
            traits=["helpful", "knowledgeable"],
        )
        logger.info("Created default persona")

    def load_persona(self, persona_id: Optional[str] = None) -> PersonaConfig:
        """
        """
        persona_id_lower = persona_id.lower() if persona_id else ""
        for pid, p in self.personas.items():
            if p.name.lower() == persona_id_lower:
                return p

        # Fall back to default
        logger.warning(f"Persona '{persona_id}' not found, using default")
        return self.personas[self.default_persona_id]

    def get_all_personas(self) -> Dict[str, PersonaConfig]:
        """
        """
    """
    """
        """
        """
        logger.info(f"PersonaManager initialized with config: {config_path}")

    def get_persona(self, persona_id: Optional[str] = None) -> PersonaConfig:
        """
        """
        """
        """
        """
        """
        """
        """
    """
    """