"""
"""
    """
    """
        """
        """
        """
        """
            raise ValueError("Template cannot be empty")

        if "{input}" not in self.template:
            raise ValueError("Template must contain {input} placeholder")

    def format(self, input_text: str, **kwargs: Any) -> str:
        """
        """
        format_vars = {"input": input_text, **kwargs}

        try:


            pass
            # Use string.format to apply the template
            return self.template.format(**format_vars)
        except Exception:

            pass
            logger.warning(f"Missing format variable in template: {e}")
            # Fallback: just substitute input if other vars are missing
            return self.template.replace("{input}", input_text)
        except Exception:

            pass
            logger.error(f"Error formatting template: {e}")
            # Last resort fallback
            return input_text

class EnhancedPersonaConfig:
    """
    """
        description: str = "",
        prompt_template: Optional[str] = None,
        background: str = "",
        interaction_style: str = "helpful",
        traits: Union[List[str], Dict[str, int]] = None,
        preferred_agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        """
        self.prompt_template = prompt_template or "Response: {input}"
        self._template = PersonaTemplate(self.prompt_template)

        # Agent type preference
        self.preferred_agent_type = preferred_agent_type

        # Additional metadata
        self.metadata = metadata or {}

    def format_response(self, response_text: str, **kwargs: Any) -> str:
        """
        """
    """
    """
        """
        """
        logger.info("EnhancedPersonaManager initialized - personas will be loaded on first access")

    def get_enhanced_persona(self, persona_id: Optional[str] = None) -> EnhancedPersonaConfig:
        """
        """
        persona_id_lower = persona_id.lower() if persona_id else ""
        for pid, persona in self._enhanced_personas.items():
            if persona.name.lower() == persona_id_lower:
                return persona

        # If not found in enhanced personas, try to adapt from base persona
        try:

            pass
            base_persona = self.get_persona(persona_id)

            # Convert base persona to enhanced
            enhanced = EnhancedPersonaConfig(
                name=base_persona.name,
                description=base_persona.background[:100],
                background=base_persona.background,
                interaction_style=base_persona.interaction_style,
                traits=base_persona.traits,
                # Default template
                prompt_template="Response: {input}",
            )

            # Cache for future use
            self._enhanced_personas[persona_id] = enhanced

            return enhanced
        except Exception:

            pass
            # Create a simple default if nothing else works
            logger.warning(f"Creating basic default persona for '{persona_id}'")

            return EnhancedPersonaConfig(
                name=persona_id or "Default",
                description="Automatically generated persona",
                prompt_template="Response: {input}",
            )

    def format_response(self, persona_id: Optional[str], response_text: str, **kwargs: Any) -> str:
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
        """
        """
                    logger.warning(f"Persona config file not found: {config_path}")
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
                            # Check if persona has a prompt template
                            if "prompt_template" in persona_data:
                                # Create enhanced persona
                                persona = EnhancedPersonaConfig(**persona_data)

                                # Add to enhanced personas dictionary
                                enhanced_personas[persona_id] = persona

                                # Check for agent type mapping
                                if persona.preferred_agent_type:
                                    self._agent_type_mappings[persona_id] = persona.preferred_agent_type

                        except Exception:

                            pass
                            logger.error(f"Failed to load enhanced persona {persona_id}: {e}")

                    logger.info(f"Loaded {len(enhanced_personas)} enhanced personas from {config_path}")
            except Exception:

                pass
                logger.error(f"Failed to load enhanced personas from {self._config_path}: {e}")
                return False

        # Update enhanced personas dictionary
        self._enhanced_personas = enhanced_personas

        # Create enhanced versions of base personas if they don't exist
        for persona_id, base_persona in self._personas.items():
            if persona_id not in self._enhanced_personas:
                try:

                    pass
                    # Convert base persona to enhanced
                    enhanced = EnhancedPersonaConfig(
                        name=base_persona.name,
                        description=(base_persona.background[:100] if base_persona.background else ""),
                        background=base_persona.background or "",
                        interaction_style=base_persona.interaction_style or "helpful",
                        traits=base_persona.traits or [],
                        # Default template
                        prompt_template="Response: {input}",
                    )

                    # Add to enhanced personas dictionary
                    self._enhanced_personas[persona_id] = enhanced
                except Exception:

                    pass
                    logger.error(f"Failed to convert base persona {persona_id} to enhanced: {e}")

        return True

# Global enhanced persona manager instance
_enhanced_persona_manager = None

def get_enhanced_persona_manager() -> EnhancedPersonaManager:
    """
    """
        auto_reload = settings.ENVIRONMENT == "development"
        config_path = settings.PERSONA_CONFIG_PATH
        cache_ttl = settings.CACHE_TTL_SECONDS

        _enhanced_persona_manager = EnhancedPersonaManager(
            config_path=config_path,
            auto_reload=auto_reload,
            cache_ttl_seconds=cache_ttl,
        )

    return _enhanced_persona_manager
