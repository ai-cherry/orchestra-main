"""
PersonaConfigManager for loading and managing persona configurations from YAML files.

This module provides functionality to load, validate, and manage persona configurations
from YAML files, with support for caching, hot-reloading, and configuration merging.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import yaml
from pydantic import ValidationError

from .models import (
    BehaviorRule,
    InteractionMode,
    KnowledgeDomain,
    MemoryConfiguration,
    PersonaConfiguration,
    PersonaStatus,
    PersonaTrait,
    ResponseStyle,
    ResponseStyleType,
    TraitCategory,
    VoiceConfiguration,
)


class PersonaConfigError(Exception):
    """Raised when there's an error in persona configuration."""

    pass


class PersonaNotFoundError(PersonaConfigError):
    """Raised when a requested persona is not found."""

    pass


class PersonaConfigManager:
    """
    Manages persona configurations loaded from YAML files.

    This manager handles loading, caching, and validation of persona configurations
    from YAML files. It supports hot-reloading and provides methods for accessing
    and managing personas.

    Attributes:
        config_dir: Directory containing persona YAML files
        personas: Dictionary of loaded persona configurations
        logger: Logger instance for this manager

    Example:
        ```python
        manager = PersonaConfigManager("./config/personas")

        # Load all personas from directory
        manager.load_all_personas()

        # Get a specific persona
        cherry = manager.get_persona("cherry")

        # List all available personas
        personas = manager.list_personas()
        ```
    """

    def __init__(self, config_dir: Union[str, Path]) -> None:
        """
        Initialize the PersonaConfigManager.

        Args:
            config_dir: Directory path containing persona YAML configuration files

        Raises:
            PersonaConfigError: If the config directory doesn't exist
        """
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            raise PersonaConfigError(f"Config directory does not exist: {config_dir}")

        self.personas: Dict[str, PersonaConfiguration] = {}
        self.logger = logging.getLogger(__name__)
        self._file_cache: Dict[Path, float] = {}  # For tracking file modifications

    def load_persona_from_file(self, file_path: Union[str, Path]) -> PersonaConfiguration:
        """
        Load a single persona configuration from a YAML file.

        Args:
            file_path: Path to the YAML file containing persona configuration

        Returns:
            PersonaConfiguration: Loaded and validated persona configuration

        Raises:
            PersonaConfigError: If file doesn't exist or contains invalid configuration
            ValidationError: If the configuration doesn't match the schema
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise PersonaConfigError(f"Persona file not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PersonaConfigError(f"Invalid YAML in {file_path}: {e}")

        if not data:
            raise PersonaConfigError(f"Empty configuration file: {file_path}")

        try:
            # Convert nested dictionaries to proper model instances
            persona_data = self._prepare_persona_data(data)
            persona = PersonaConfiguration(**persona_data)

            self.logger.info(f"Loaded persona '{persona.name}' from {file_path}")
            return persona

        except ValidationError as e:
            raise PersonaConfigError(f"Invalid persona configuration in {file_path}: {e}")

    def _prepare_persona_data(self, data: Dict) -> Dict:
        """
        Prepare raw YAML data for PersonaConfiguration model.

        Converts nested dictionaries to appropriate model instances.

        Args:
            data: Raw persona data from YAML

        Returns:
            Dict: Prepared data ready for PersonaConfiguration
        """
        prepared = data.copy()

        # Convert traits
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
                BehaviorRule(**rule) if isinstance(rule, dict) else rule for rule in prepared["behavior_rules"]
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
        Load all persona configurations from the config directory.

        Scans the config directory for YAML files and loads all valid
        persona configurations.

        Returns:
            Dict[str, PersonaConfiguration]: Dictionary mapping persona slugs to configurations

        Raises:
            PersonaConfigError: If there are errors loading personas
        """
        yaml_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))

        if not yaml_files:
            self.logger.warning(f"No YAML files found in {self.config_dir}")
            return {}

        errors = []
        loaded_count = 0

        for file_path in yaml_files:
            try:
                persona = self.load_persona_from_file(file_path)
                self.personas[persona.slug] = persona
                self._file_cache[file_path] = file_path.stat().st_mtime
                loaded_count += 1
            except Exception as e:
                errors.append(f"{file_path.name}: {str(e)}")
                self.logger.error(f"Failed to load {file_path}: {e}")

        if errors and not loaded_count:
            raise PersonaConfigError(f"Failed to load any personas. Errors:\n" + "\n".join(errors))

        self.logger.info(f"Loaded {loaded_count} personas from {self.config_dir} " f"({len(errors)} errors)")

        return self.personas

    def get_persona(self, slug: str) -> PersonaConfiguration:
        """
        Get a specific persona by slug.

        Args:
            slug: The slug identifier of the persona

        Returns:
            PersonaConfiguration: The requested persona configuration

        Raises:
            PersonaNotFoundError: If the persona doesn't exist
        """
        if slug not in self.personas:
            raise PersonaNotFoundError(f"Persona not found: {slug}")

        return self.personas[slug]

    def list_personas(
        self, status: Optional[PersonaStatus] = None, tags: Optional[List[str]] = None
    ) -> List[PersonaConfiguration]:
        """
        List all available personas with optional filtering.

        Args:
            status: Filter by persona status (active, inactive, etc.)
            tags: Filter by tags (personas must have all specified tags)

        Returns:
            List[PersonaConfiguration]: List of personas matching the criteria
        """
        personas = list(self.personas.values())

        # Filter by status
        if status:
            personas = [p for p in personas if p.status == status]

        # Filter by tags
        if tags:
            tag_set = set(tags)
            personas = [p for p in personas if tag_set.issubset(set(p.tags))]

        return sorted(personas, key=lambda p: p.name)

    def reload_persona(self, slug: str, file_path: Optional[Path] = None) -> PersonaConfiguration:
        """
        Reload a specific persona from its configuration file.

        Args:
            slug: The slug of the persona to reload
            file_path: Optional specific file path to load from

        Returns:
            PersonaConfiguration: The reloaded persona configuration

        Raises:
            PersonaNotFoundError: If the persona doesn't exist
            PersonaConfigError: If there's an error reloading
        """
        if not file_path:
            # Try to find the file containing this persona
            for yaml_file in self.config_dir.glob("*.y*ml"):
                try:
                    with open(yaml_file, "r") as f:
                        data = yaml.safe_load(f)
                        if data and data.get("slug") == slug:
                            file_path = yaml_file
                            break
                except:
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
        Check for updated persona files and reload them.

        Returns:
            Set[str]: Set of persona slugs that were updated
        """
        updated_personas = set()

        for file_path, last_mtime in self._file_cache.items():
            if not file_path.exists():
                continue

            current_mtime = file_path.stat().st_mtime
            if current_mtime > last_mtime:
                try:
                    persona = self.load_persona_from_file(file_path)
                    self.personas[persona.slug] = persona
                    self._file_cache[file_path] = current_mtime
                    updated_personas.add(persona.slug)
                    self.logger.info(f"Auto-reloaded updated persona: {persona.slug}")
                except Exception as e:
                    self.logger.error(f"Failed to reload {file_path}: {e}")

        return updated_personas

    def validate_all(self) -> Dict[str, List[str]]:
        """
        Validate all loaded personas and return any issues found.

        Returns:
            Dict[str, List[str]]: Dictionary mapping persona slugs to lists of validation issues
        """
        issues = {}

        for slug, persona in self.personas.items():
            persona_issues = []

            # Check for duplicate slugs
            slug_count = sum(1 for p in self.personas.values() if p.slug == slug)
            if slug_count > 1:
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
        Export a persona configuration to a YAML file.

        Args:
            slug: The slug of the persona to export
            output_path: Path where the YAML file should be saved

        Raises:
            PersonaNotFoundError: If the persona doesn't exist
            IOError: If there's an error writing the file
        """
        persona = self.get_persona(slug)
        output_path = Path(output_path)

        # Convert to dictionary for YAML export
        persona_dict = persona.model_dump(exclude_none=True)

        # Convert datetime objects to strings
        for key in ["created_at", "updated_at"]:
            if key in persona_dict:
                persona_dict[key] = persona_dict[key].isoformat()

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(persona_dict, f, default_flow_style=False, sort_keys=False)

            self.logger.info(f"Exported persona '{slug}' to {output_path}")
        except IOError as e:
            raise IOError(f"Failed to export persona: {e}")
