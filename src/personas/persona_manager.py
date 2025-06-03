#!/usr/bin/env python3
"""
Persona Manager
Manages persona instances and routing.
"""

import logging
from typing import Dict, Optional, Any
from .cherry_persona import CherryPersona
from .sophia_persona import SophiaPersona
from .karen_persona import KarenPersona

logger = logging.getLogger(__name__)


class PersonaManager:
    """Manages persona instances and routing."""
    
    def __init__(self):
        """Initialize persona manager."""
        self.personas = {
            "cherry": CherryPersona(),
            "sophia": SophiaPersona(),
            "karen": KarenPersona()
        }
        self.default_persona = "cherry"
    
    def get_persona(self, persona_id: str) -> Optional[Any]:
        """Get persona instance by ID."""
        return self.personas.get(persona_id.lower())
    
    def get_available_personas(self) -> Dict[str, str]:
        """Get list of available personas."""
        return {
            persona_id: persona.description 
            for persona_id, persona in self.personas.items()
        }
    
    async def process_message(self, message: str, persona_id: str, user_id: str, session_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process message with specified persona."""
        persona = self.get_persona(persona_id)
        
        if not persona:
            logger.warning(f"Persona '{persona_id}' not found, using default")
            persona = self.personas[self.default_persona]
            persona_id = self.default_persona
        
        result = await persona.process_message(message, user_id, session_id, context)
        result["requested_persona"] = persona_id
        
        return result
    
    def get_persona_info(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed persona information."""
        persona = self.get_persona(persona_id)
        
        if not persona:
            return None
        
        return {
            "id": persona.id,
            "name": persona.name,
            "description": persona.description,
            "domain": persona.domain,
            "traits": persona.traits,
            "communication_style": persona.communication_style,
            "knowledge_domains": persona.knowledge_domains
        }
