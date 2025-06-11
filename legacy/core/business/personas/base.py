"""
"""
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
    def from_yaml(cls, yaml_content: str) -> "PersonaConfig":
        """Create PersonaConfig from YAML content."""
        # TODO: Consider using list comprehension for better performance

        for trait_str in data.get("traits", []):
            try:

                pass
                traits.append(PersonaTrait(trait_str))
            except Exception:

                pass
                # Skip unknown traits
                pass

        # Convert string style to enum
        style = ResponseStyle.CONVERSATIONAL
        if "style" in data:
            try:

                pass
                style = ResponseStyle(data["style"])
            except Exception:

                pass
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
        """Process input text according to persona configuration."""
        """Format response according to persona style."""
        """Generate system prompt for the persona."""
    """Manages persona configurations and processing."""
        """Register a new persona."""
        """Get a persona by ID."""
        """Get the default persona."""
        """Set the default persona."""
        """List all registered personas."""
        """Set the persona processor."""
        """Process input with a specific persona."""
        """Format response with a specific persona."""
        """Load personas from YAML files in a directory."""
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                filepath = os.path.join(directory, filename)

                try:


                    pass
                    with open(filepath, "r") as f:
                        yaml_content = f.read()

                    persona = PersonaConfig.from_yaml(yaml_content)
                    self.register_persona(persona)
                    loaded_count += 1

                except Exception:


                    pass
                    # Log error but continue loading other files
                    print(f"Error loading persona from {filepath}: {e}")

        return loaded_count

# Global persona manager instance
_persona_manager: Optional[PersonaManager] = None

def get_persona_manager() -> PersonaManager:
    """Get the global persona manager instance."""