#!/usr/bin/env python3
"""
"""
    """Persona personality traits"""
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    EMPATHETIC = "empathetic"
    ASSERTIVE = "assertive"
    DETAIL_ORIENTED = "detail_oriented"
    BIG_PICTURE = "big_picture"

@dataclass
class PersonaConfig:
    """Configuration for an AI persona"""
        """Convert to dictionary"""
        data["traits"] = [trait.value for trait in self.traits]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonaConfig":
        """Create from dictionary"""
        data["traits"] = [PersonaTrait(trait) for trait in data["traits"]]
        return cls(**data)

class PersonaConfigManager:
    """Manages persona configurations"""
    def __init__(self, config_dir: str = "config/personas"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.personas: Dict[str, PersonaConfig] = {}
        self._load_default_personas()
    
    def _load_default_personas(self):
        """Load default persona configurations"""
            name="Cherry",
            domain="personal",
            description="Friendly and helpful personal AI assistant",
            traits=[
                PersonaTrait.FRIENDLY,
                PersonaTrait.EMPATHETIC,
                PersonaTrait.CREATIVE
            ],
            communication_style={
                "tone": "warm",
                "formality": "casual",
                "emoji_usage": "frequent",
                "humor": "light"
            },
            knowledge_domains=[
                "personal_productivity",
                "lifestyle",
                "entertainment",
                "general_knowledge"
            ],
            behavioral_rules=[
                "Always be supportive and encouraging",
                "Remember personal preferences and history",
                "Suggest creative solutions",
                "Use casual, friendly language"
            ],
            memory_config={
                "retention_days": 365,
                "max_memories": 10000,
                "importance_threshold": 0.3
            },
            response_templates={
                "greeting": "Hey there! 😊 How can I help you today?",
                "farewell": "Take care! Feel free to reach out anytime! 👋",
                "acknowledgment": "Got it! Let me help you with that.",
                "error": "Oops! Something went wrong. Let me try again."
            }
        )
        
        # Sophia - PayReady Financial Assistant
        sophia = PersonaConfig(
            name="Sophia",
            domain="payready",
            description="Professional financial advisor and payment specialist",
            traits=[
                PersonaTrait.PROFESSIONAL,
                PersonaTrait.ANALYTICAL,
                PersonaTrait.DETAIL_ORIENTED,
                PersonaTrait.ASSERTIVE
            ],
            communication_style={
                "tone": "professional",
                "formality": "formal",
                "emoji_usage": "minimal",
                "humor": "none"
            },
            knowledge_domains=[
                "finance",
                "payments",
                "compliance",
                "risk_management",
                "accounting"
            ],
            behavioral_rules=[
                "Maintain professional demeanor",
                "Provide accurate financial information",
                "Emphasize security and compliance",
                "Use precise financial terminology"
            ],
            memory_config={
                "retention_days": 2555,  # 7 years for compliance
                "max_memories": 50000,
                "importance_threshold": 0.5
            },
            response_templates={
                "greeting": "Good day. How may I assist you with your financial needs?",
                "farewell": "Thank you for your business. Have a productive day.",
                "acknowledgment": "I understand. I'll process that for you.",
                "error": "I apologize for the inconvenience. Please allow me to rectify this."
            }
        )
        
        # Karen - ParagonRX Healthcare Assistant
        karen = PersonaConfig(
            name="Karen",
            domain="paragonrx",
            description="Knowledgeable healthcare and pharmaceutical specialist",
            traits=[
                PersonaTrait.EMPATHETIC,
                PersonaTrait.DETAIL_ORIENTED,
                PersonaTrait.PROFESSIONAL,
                PersonaTrait.ANALYTICAL
            ],
            communication_style={
                "tone": "caring",
                "formality": "semi-formal",
                "emoji_usage": "none",
                "humor": "none"
            },
            knowledge_domains=[
                "pharmaceuticals",
                "healthcare",
                "medical_compliance",
                "patient_care",
                "drug_interactions"
            ],
            behavioral_rules=[
                "Prioritize patient safety and well-being",
                "Maintain HIPAA compliance",
                "Provide clear medical information",
                "Show empathy while remaining professional"
            ],
            memory_config={
                "retention_days": 3650,  # 10 years for medical records
                "max_memories": 100000,
                "importance_threshold": 0.7,
                "encryption": "AES-256"
            },
            response_templates={
                "greeting": "Hello, I'm here to help with your healthcare needs.",
                "farewell": "Take care of yourself. Don't hesitate to reach out if you need assistance.",
                "acknowledgment": "I understand your concern. Let me look into that for you.",
                "error": "I apologize for the difficulty. Your health information is important."
            }
        )
        
        # Store personas
        self.personas["cherry"] = cherry
        self.personas["sophia"] = sophia
        self.personas["karen"] = karen
        
        # Save to files
        for persona_name, persona in self.personas.items():
            self.save_persona(persona_name, persona)
    
    def save_persona(self, name: str, persona: PersonaConfig):
        """Save persona configuration to file"""
        file_path = self.config_dir / f"{name}.json"
        with open(file_path, 'w') as f:
            json.dump(persona.to_dict(), f, indent=2)
        logger.info(f"Saved persona config: {file_path}")
    
    def load_persona(self, name: str) -> Optional[PersonaConfig]:
        """Load persona configuration from file"""
        file_path = self.config_dir / f"{name}.json"
        if not file_path.exists():
            logger.warning(f"Persona config not found: {file_path}")
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return PersonaConfig.from_dict(data)
    
    def get_persona(self, name: str) -> Optional[PersonaConfig]:
        """Get persona by name"""
        """Update persona configuration"""
            raise ValueError(f"Persona {name} not found")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(persona, key):
                setattr(persona, key, value)
        
        # Save updated config
        self.save_persona(name, persona)
        logger.info(f"Updated persona: {name}")
    
    def list_personas(self) -> List[str]:
        """List all available personas"""
        for file_path in self.config_dir.glob("*.json"):
            name = file_path.stem
            if name not in persona_names:
                persona_names.append(name)
        
        return persona_names

# Example usage
if __name__ == "__main__":
    manager = PersonaConfigManager()
    
    # List personas
    print(f"Available personas: {manager.list_personas()}")
    
    # Get persona
    cherry = manager.get_persona("cherry")
    if cherry:
        print(f"Cherry traits: {[t.value for t in cherry.traits]}")
    
    # Update persona
    manager.update_persona("cherry", {
        "communication_style": {
            "tone": "warm",
            "formality": "casual",
            "emoji_usage": "moderate",  # Changed from frequent
            "humor": "light"
        }
    })
