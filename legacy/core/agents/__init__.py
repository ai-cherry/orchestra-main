"""Core agents module for AI orchestration"""

from .multi_agent_swarm import MultiAgentSwarmSystem
from .unified_orchestrator import UnifiedOrchestrator
from .web_scraping_agents import (
    EnhancedWebScrapingAgent,
    FinanceWebScrapingTeam,
    ClinicalTrialsWebScrapingTeam,
    EnterpriseWebScrapingTeam
)
from .integration_specialists import (
    GongIntegrationAgent,
    HubSpotIntegrationAgent,
    SlackIntegrationAgent,
    LookerIntegrationAgent,
    GitHubIntegrationAgent,
    LinkedInIntegrationAgent,
    NetSuiteIntegrationAgent,
    AsanaIntegrationAgent,
    LinearIntegrationAgent,
    ApolloIntegrationAgent,
    SharePointIntegrationAgent,
    LatticeIntegrationAgent,
    IntegrationCoordinator
)
from .ai_operators import (
    AIOperator,
    OperatorManager
)

__all__ = [
    'MultiAgentSwarmSystem',
    'UnifiedOrchestrator',
    'EnhancedWebScrapingAgent',
    'FinanceWebScrapingTeam',
    'ClinicalTrialsWebScrapingTeam',
    'EnterpriseWebScrapingTeam',
    'GongIntegrationAgent',
    'HubSpotIntegrationAgent',
    'SlackIntegrationAgent',
    'LookerIntegrationAgent',
    'GitHubIntegrationAgent',
    'LinkedInIntegrationAgent',
    'NetSuiteIntegrationAgent',
    'AsanaIntegrationAgent',
    'LinearIntegrationAgent',
    'ApolloIntegrationAgent',
    'SharePointIntegrationAgent',
    'LatticeIntegrationAgent',
    'IntegrationCoordinator',
    'AIOperator',
    'OperatorManager'
]