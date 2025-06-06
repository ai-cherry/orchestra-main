"""
Service Interfaces
Defines contracts for services following Interface Segregation Principle
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class IAuthenticationService(ABC):
    """Interface for authentication services"""
    
    @abstractmethod
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        pass
    
    @abstractmethod
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create access token"""
        pass
    
    @abstractmethod
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get user from token"""
        pass

class IConversationService(ABC):
    """Interface for conversation services"""
    
    @abstractmethod
    async def generate_response(
        self, 
        user_id: int, 
        persona_type: str, 
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI response"""
        pass
    
    @abstractmethod
    async def get_conversation_history(
        self, 
        user_id: int, 
        persona_type: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        pass

class IPersonaService(ABC):
    """Interface for persona management services"""
    
    @abstractmethod
    async def get_all_personas(self) -> List[Dict[str, Any]]:
        """Get all personas"""
        pass
    
    @abstractmethod
    async def get_persona_by_id(self, persona_id: int) -> Optional[Dict[str, Any]]:
        """Get persona by ID"""
        pass
    
    @abstractmethod
    async def update_persona(self, persona_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update persona configuration"""
        pass
