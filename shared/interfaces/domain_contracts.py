#!/usr/bin/env python3
"""
Domain Interface Contracts
Defines clean interfaces for cross-domain communication
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class DomainRequest(BaseModel):
    """Base request model for cross-domain communication"""
    source_domain: str
    target_domain: str
    request_id: str
    timestamp: str
    data: Dict[str, Any]

class DomainResponse(BaseModel):
    """Base response model for cross-domain communication"""
    request_id: str
    status: str
    data: Optional[Dict[str, Any]]
    error: Optional[str]

class IDomainService(ABC):
    """Interface for domain services"""
    
    @abstractmethod
    async def process_request(self, request: DomainRequest) -> DomainResponse:
        """Process a cross-domain request"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[str]:
        """Return list of capabilities this domain provides"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Return health status of the domain"""
        pass

class PersonalDomainInterface(IDomainService):
    """Interface for Personal (Cherry) domain"""
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        pass
    
    async def update_user_context(self, user_id: str, context: Dict[str, Any]) -> bool:
        """Update user context"""
        pass

class PayReadyDomainInterface(IDomainService):
    """Interface for PayReady (Sophia) domain"""
    
    async def analyze_payment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze payment data"""
        pass
    
    async def get_market_insights(self, query: str) -> List[Dict[str, Any]]:
        """Get market insights"""
        pass

class ParagonRXDomainInterface(IDomainService):
    """Interface for ParagonRX (Karen) domain"""
    
    async def search_medical_info(self, query: str) -> List[Dict[str, Any]]:
        """Search medical information"""
        pass
    
    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get system health metrics"""
        pass

class DomainRegistry:
    """Registry for domain services"""
    
    def __init__(self):
        self._domains = {}
    
    def register(self, domain: str, service: IDomainService):
        """Register a domain service"""
        self._domains[domain] = service
    
    def get(self, domain: str) -> Optional[IDomainService]:
        """Get a domain service"""
        return self._domains.get(domain)
    
    def list_domains(self) -> List[str]:
        """List all registered domains"""
        return list(self._domains.keys())

# Global registry instance
domain_registry = DomainRegistry()
