"""
"""
    """Raised when there's an error in persona configuration."""
    """Raised when a requested persona is not found."""
    """
        manager = PersonaConfigManager("./config/personas")

        # Load all personas from directory
        manager.load_all_personas()

        # Get a specific persona
        cherry = manager.get_persona("cherry")

        # List all available personas
        personas = manager.list_personas()
        ```
    """
        """
        """
            raise PersonaConfigError(f"Config directory does not exist: {config_dir}")

        self.personas: Dict[str, PersonaConfiguration] = {}
        self.logger = logging.getLogger(__name__)
        self._file_cache: Dict[Path, float] = {}  # For tracking file modifications

    def load_persona_from_file(self, file_path: Union[str, Path]) -> PersonaConfiguration:
        """
        """
            raise PersonaConfigError(f"Persona file not found: {file_path}")

        try:


            pass
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:

            pass
            raise PersonaConfigError(f"Invalid YAML in {file_path}: {e}")

        if not data:
            raise PersonaConfigError(f"Empty configuration file: {file_path}")

        try:


            pass
            # Convert nested dictionaries to proper model instances
            persona_data = self._prepare_persona_data(data)
            persona = PersonaConfiguration(**persona_data)

            self.logger.info(f"Loaded persona '{persona.name}' from {file_path}")
            return persona

        except Exception:


            pass
            raise PersonaConfigError(f"Invalid persona configuration in {file_path}: {e}")

    def _prepare_persona_data(self, data: Dict) -> Dict:
        """
        """
        if "traits" in prepared and isinstance(prepared["traits"], list):
            prepared["traits"] = [
                PersonaTrait(**trait) if isinstance(trait, dict) else trait for trait in prepared["traits"]
            ]

        # Convert response_style
        if "response_style" in prepared and isinstance(prepared["response_style"], dict):
            prepared["response_style"] = ResponseStyle(**prepared["response_style"])

        # Convert knowledge_domains
        if "knowledge_domains" in prepared and isinstance(prepared["knowledge_domains"], list):
            prepared["knowledge_domains"] = [
                KnowledgeDomain(**domain) if isinstance(domain, dict) else domain
                for domain in prepared["knowledge_domains"]
            ]

        # Convert behavior_rules
        if "behavior_rules" in prepared and isinstance(prepared["behavior_rules"], list):
            prepared["behavior_rules"] = [
                BehaviorRule(**rule) if isinstance(rule, dict) else rule # TODO: Consider using list comprehension for better performance
 for rule in prepared["behavior_rules"]
            ]

        # Convert memory_config
        if "memory_config" in prepared and isinstance(prepared["memory_config"], dict):
            prepared["memory_config"] = MemoryConfiguration(**prepared["memory_config"])

        # Convert voice_config
        if "voice_config" in prepared and isinstance(prepared["voice_config"], dict):
            prepared["voice_config"] = VoiceConfiguration(**prepared["voice_config"])

        return prepared

    def load_all_personas(self) -> Dict[str, PersonaConfiguration]:
        """
        """
        yaml_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))

        if not yaml_files:
            self.logger.warning(f"No YAML files found in {self.config_dir}")
            return {}

        errors = []
        loaded_count = 0

        for file_path in yaml_files:
            try:

                pass
                persona = self.load_persona_from_file(file_path)
                self.personas[persona.slug] = persona
                self._file_cache[file_path] = file_path.stat().st_mtime
                loaded_count += 1
            except Exception:

                pass
                errors.append(f"{file_path.name}: {str(e)}")
                self.logger.error(f"Failed to load {file_path}: {e}")

        if errors and not loaded_count:
            raise PersonaConfigError(f"Failed to load any personas. Errors:\n" + "\n".join(errors))

        self.logger.info(f"Loaded {loaded_count} personas from {self.config_dir} " f"({len(errors)} errors)")

        return self.personas

    def get_persona(self, slug: str) -> PersonaConfiguration:
        """
        """
            raise PersonaNotFoundError(f"Persona not found: {slug}")

        return self.personas[slug]

    def list_personas(
        self, status: Optional[PersonaStatus] = None, tags: Optional[List[str]] = None
    ) -> List[PersonaConfiguration]:
        """
        """
        """
        """
            for yaml_file in self.config_dir.glob("*.y*ml"):
                try:

                    pass
                    with open(yaml_file, "r") as f:
                        data = yaml.safe_load(f)
                        if data and data.get("slug") == slug:
                            file_path = yaml_file
                            break
                except Exception:

                    pass
                    continue

            if not file_path:
                raise PersonaNotFoundError(f"Cannot find configuration file for persona: {slug}")

        persona = self.load_persona_from_file(file_path)
        self.personas[persona.slug] = persona
        self._file_cache[file_path] = file_path.stat().st_mtime

        self.logger.info(f"Reloaded persona: {slug}")
        return persona

    def check_for_updates(self) -> Set[str]:
        """
        """
                    self.logger.info(f"Auto-reloaded updated persona: {persona.slug}")
                except Exception:

                    pass
                    self.logger.error(f"Failed to reload {file_path}: {e}")

        return updated_personas

    def validate_all(self) -> Dict[str, List[str]]:
        """
        """
                persona_issues.append(f"Duplicate slug: {slug}")

            # Check for empty required lists
            if not persona.traits:
                persona_issues.append("No traits defined")

            # Check for conflicting behavior rules
            mandatory_rules = [r for r in persona.behavior_rules if r.is_mandatory]
            if len(mandatory_rules) > 1:
                conditions = [r.condition for r in mandatory_rules]
                if len(conditions) != len(set(conditions)):
                    persona_issues.append("Conflicting mandatory behavior rules")

            # Check model preferences
            if persona.model_preferences and len(persona.model_preferences) == 0:
                persona_issues.append("Empty model preferences list")

            if persona_issues:
                issues[slug] = persona_issues

        return issues

    def export_persona(self, slug: str, output_path: Union[str, Path]) -> None:
        """
        """
        for key in ["created_at", "updated_at"]:
            if key in persona_dict:
                persona_dict[key] = persona_dict[key].isoformat()

        try:


            pass
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(persona_dict, f, default_flow_style=False, sort_keys=False)

            self.logger.info(f"Exported persona '{slug}' to {output_path}")
        except Exception:

            pass
            raise IOError(f"Failed to export persona: {e}")
