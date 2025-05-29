"""
Base persona abstractions for Orchestra AI.

This module provides interfaces for managing AI agent personas
with configurable traits and behaviors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml


class PersonaTrait(Enum):
    """Common persona traits."""

    HELPFUL = "helpful"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"
    CONCISE = "concise"
    DETAILED = "detailed"
    HUMOROUS = "humorous"


class ResponseStyle(Enum):
    """Response formatting styles."""

    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    EDUCATIONAL = "educational"
    CONVERSATIONAL = "conversational"


@dataclass
class PersonaConfig:
    """Configuration for an AI persona."""

    id: str
    name: str
    description: str
    traits: List[PersonaTrait] = field(default_factory=list)
    style: ResponseStyle = ResponseStyle.CONVERSATIONAL
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "PersonaConfig":
        """Create PersonaConfig from YAML content."""
        data = yaml.safe_load(yaml_content)

        # Convert string traits to enum
        traits = []
        for trait_str in data.get("traits", []):
            try:
                traits.append(PersonaTrait(trait_str))
            except ValueError:
                # Skip unknown traits
                pass

        # Convert string style to enum
        style = ResponseStyle.CONVERSATIONAL
        if "style" in data:
            try:
                style = ResponseStyle(data["style"])
            except ValueError:
                pass

        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            traits=traits,
            style=style,
            system_prompt=data.get("system_prompt"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 2000),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "traits": [trait.value for trait in self.traits],
            "style": self.style.value,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "metadata": self.metadata,
        }


class PersonaProcessor(ABC):
    """Abstract base class for persona processors."""

    @abstractmethod
    def process_input(self, input_text: str, persona: PersonaConfig) -> str:
        """Process input text according to persona configuration."""
        pass

    @abstractmethod
    def format_response(self, response: str, persona: PersonaConfig) -> str:
        """Format response according to persona style."""
        pass

    @abstractmethod
    def generate_system_prompt(self, persona: PersonaConfig) -> str:
        """Generate system prompt for the persona."""
        pass


class PersonaManager:
    """Manages persona configurations and processing."""

    def __init__(self):
        self._personas: Dict[str, PersonaConfig] = {}
        self._default_persona_id: Optional[str] = None
        self._processor: Optional[PersonaProcessor] = None

    def register_persona(self, persona: PersonaConfig) -> None:
        """Register a new persona."""
        self._personas[persona.id] = persona

        # Set as default if it's the first persona
        if self._default_persona_id is None:
            self._default_persona_id = persona.id

    def get_persona(self, persona_id: str) -> Optional[PersonaConfig]:
        """Get a persona by ID."""
        return self._personas.get(persona_id)

    def get_default_persona(self) -> Optional[PersonaConfig]:
        """Get the default persona."""
        if self._default_persona_id:
            return self._personas.get(self._default_persona_id)
        return None

    def set_default_persona(self, persona_id: str) -> bool:
        """Set the default persona."""
        if persona_id in self._personas:
            self._default_persona_id = persona_id
            return True
        return False

    def list_personas(self) -> List[PersonaConfig]:
        """List all registered personas."""
        return list(self._personas.values())

    def set_processor(self, processor: PersonaProcessor) -> None:
        """Set the persona processor."""
        self._processor = processor

    def process_with_persona(self, input_text: str, persona_id: Optional[str] = None) -> Optional[str]:
        """Process input with a specific persona."""
        if not self._processor:
            return None

        # Get persona
        if persona_id:
            persona = self.get_persona(persona_id)
        else:
            persona = self.get_default_persona()

        if not persona:
            return None

        # Process input
        return self._processor.process_input(input_text, persona)

    def format_response_with_persona(self, response: str, persona_id: Optional[str] = None) -> Optional[str]:
        """Format response with a specific persona."""
        if not self._processor:
            return response

        # Get persona
        if persona_id:
            persona = self.get_persona(persona_id)
        else:
            persona = self.get_default_persona()

        if not persona:
            return response

        # Format response
        return self._processor.format_response(response, persona)

    def load_from_directory(self, directory: str) -> int:
        """Load personas from YAML files in a directory."""
        import os

        loaded_count = 0

        for filename in os.listdir(directory):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(directory, filename)

                try:
                    with open(filepath, "r") as f:
                        yaml_content = f.read()

                    persona = PersonaConfig.from_yaml(yaml_content)
                    self.register_persona(persona)
                    loaded_count += 1

                except Exception as e:
                    # Log error but continue loading other files
                    print(f"Error loading persona from {filepath}: {e}")

        return loaded_count


# Global persona manager instance
_persona_manager: Optional[PersonaManager] = None


def get_persona_manager() -> PersonaManager:
    """Get the global persona manager instance."""
    global _persona_manager

    if _persona_manager is None:
        _persona_manager = PersonaManager()

    return _persona_manager
