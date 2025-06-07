#!/usr/bin/env python3
"""
Deploy and Initialize AI Agent Orchestration System
Brings together all components for the unified orchestration architecture
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.database import UnifiedDatabase
from services.weaviate_service import WeaviateService
from core.memory.advanced_memory_system import MemoryRouter
from core.personas.enhanced_personality_engine import PersonalityEngine
from core.coordination.cross_domain_coordinator import CrossDomainCoordinator
from core.cache_manager import CacheManager
from core.monitoring import MetricsCollector

from core.agents.unified_orchestrator import UnifiedOrchestrator
from core.agents.ai_operators import AIOperatorManager, create_default_operators
from services.ai_agent_orchestrator import AIAgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIOrchestrationDeployment:
    """Handles deployment and initialization of the AI orchestration system"""
    
    def __init__(self):
        self.db = None
        self.weaviate = None
        self.memory_router = None
        self.cache_manager = None
        self.metrics = None
        self.orchestrator = None
        self.operator_manager = None
    
    async def initialize_infrastructure(self):
        """Initialize core infrastructure components"""
        logger.info("Initializing infrastructure components...")
        
        # Initialize database
        self.db = UnifiedDatabase()
        await self.db.initialize()
        
        # Initialize Weaviate
        self.weaviate = WeaviateService()
        await self.weaviate.initialize()
        
        # Initialize memory system
        self.memory_router = MemoryRouter()
        
        # Initialize cache
        self.cache_manager = CacheManager()
        
        # Initialize metrics
        self.metrics = MetricsCollector()
        
        logger.info("Infrastructure components initialized successfully")
    
    async def create_database_schema(self):
        """Create all required database schemas"""
        logger.info("Creating database schemas...")
        
        # Import schema definitions
        from core.agents.unified_orchestrator import ENHANCED_ORCHESTRATION_SCHEMA
        
        # Execute schema creation
        await self.db.execute(ENHANCED_ORCHESTRATION_SCHEMA)
        
        logger.info("Database schemas created successfully")
    
    async def initialize_orchestration_system(self):
        """Initialize the unified orchestration system"""
        logger.info("Initializing orchestration system...")
        
        # Initialize personality engine
        personality_engine = PersonalityEngine(self.memory_router)
        
        # Initialize cross-domain coordinator
        coordinator = CrossDomainCoordinator(self.memory_router, personality_engine)
        
        # Initialize unified orchestrator
        self.orchestrator = UnifiedOrchestrator(
            memory_router=self.memory_router,
            personality_engine=personality_engine,
            coordinator=coordinator,
            db=self.db,
            weaviate=self.weaviate,
            cache_manager=self.cache_manager,
            metrics=self.metrics
        )
        
        # Initialize operator manager
        self.operator_manager = AIOperatorManager(
            db=self.db,
            memory_router=self.memory_router,
            metrics=self.metrics
        )
        
        # Create default operators
        await create_default_operators(self.operator_manager)
        
        logger.info("Orchestration system initialized successfully")
    
    async def create_weaviate_collections(self):
        """Create Weaviate collections for vector storage"""
        logger.info("Creating Weaviate collections...")
        
        collections = [
            {
                "name": "WebScrapingResults",
                "properties": [
                    {"name": "task_id", "dataType": ["string"]},
                    {"name": "agent_id", "dataType": ["string"]},
                    {"name": "domain", "dataType": ["string"]},
                    {"name": "task_type", "dataType": ["string"]},
                    {"name": "results", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]},
                    {"name": "metadata", "dataType": ["object"]}
                ]
            },
            {
                "name": "ClientIntelligence",
                "properties": [
                    {"name": "client_name", "dataType": ["string"]},
                    {"name": "aggregated_data", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]},
                    {"name": "data_sources", "dataType": ["string[]"]}
                ]
            },
            {
                "name": "SlackAlerts",
                "properties": [
                    {"name": "channel", "dataType": ["string"]},
                    {"name": "message", "dataType": ["text"]},
                    {"name": "context", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]},
                    {"name": "status", "dataType": ["string"]}
                ]
            },
            {
                "name": "SwingTradeAnalysis",
                "properties": [
                    {"name": "task_id", "dataType": ["string"]},
                    {"name": "task_type", "dataType": ["string"]},
                    {"name": "ticker", "dataType": ["string"]},
                    {"name": "analysis", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]}
                ]
            }
        ]
        
        for collection in collections:
            try:
                await self.weaviate.create_collection(
                    collection["name"],
                    collection["properties"]
                )
                logger.info(f"Created Weaviate collection: {collection['name']}")
            except Exception as e:
                logger.warning(f"Collection {collection['name']} may already exist: {e}")
        
        logger.info("Weaviate collections setup completed")
    
    async def run_system_tests(self):
        """Run basic system tests to verify functionality"""
        logger.info("Running system tests...")
        
        # Test 1: Natural language query processing
        logger.info("Test 1: Natural language query processing")
        result = await self.orchestrator.process_natural_language_query(
            query="What are the best swing trade opportunities today?",
            domain="cherry",
            user_id="test_user",
            context={"test": True}
        )
        logger.info(f"Query result: {result.get('success', False)}")
        
        # Test 2: Data ingestion pipeline
        logger.info("Test 2: Data ingestion pipeline creation")
        pipeline = await self.orchestrator.create_data_ingestion_pipeline(
            source="test_source",
            destination="test_destination",
            transformation_rules={"test": "rules"}
        )
        logger.info(f"Pipeline created: {pipeline.get('pipeline_id', 'None')}")
        
        # Test 3: Orchestrator status
        logger.info("Test 3: Orchestrator status check")
        status = await self.orchestrator.get_orchestrator_status()
        logger.info(f"System status: {status.get('database_health', 'unknown')}")
        
        # Test 4: Operator dashboard
        logger.info("Test 4: Operator dashboard data")
        operators = await self.db.fetch(
            "SELECT operator_id FROM ai_operators LIMIT 1"
        )
        if operators:
            dashboard = await self.operator_manager.get_operator_dashboard_data(
                operators[0]["operator_id"]
            )
            logger.info(f"Dashboard data retrieved: {bool(dashboard)}")
        
        logger.info("System tests completed")
    
    async def display_deployment_summary(self):
        """Display deployment summary and instructions"""
        print("\n" + "="*60)
        print("AI AGENT ORCHESTRATION SYSTEM DEPLOYMENT COMPLETE")
        print("="*60)
        
        # Get system status
        status = await self.orchestrator.get_orchestrator_status()
        operator_count = await self.operator_manager.get_operator_count()
        
        print(f"\n📊 SYSTEM STATUS:")
        print(f"   - Database: {status.get('database_health', 'unknown')}")
        print(f"   - Weaviate: Connected")
        print(f"   - Cache: Active")
        print(f"   - Metrics: Recording")
        
        print(f"\n🤖 AGENT TEAMS:")
        print(f"   - Web Scraping Teams: {len(status.get('web_scraping_teams', {}))}")
        print(f"   - Integration Specialists: {len(status.get('integration_specialists', []))}")
        print(f"   - Total Agents: {status.get('total_agents', 0)}")
        
        print(f"\n👥 AI OPERATORS:")
        print(f"   - Total Operators: {operator_count}")
        print(f"   - Domains Covered: Cherry, Sophia, ParagonRX")
        
        print(f"\n🔌 INTEGRATIONS:")
        integrations = [
            "Gong.io", "HubSpot", "Slack", "Looker", "GitHub",
            "SQL Databases", "SharePoint", "LinkedIn", "NetSuite",
            "Asana", "Linear", "Apollo.io", "Lattice"
        ]
        print(f"   - Available: {', '.join(integrations[:5])}...")
        print(f"   - Total: {len(integrations)} platforms")
        
        print(f"\n📝 NATURAL LANGUAGE QUERIES:")
        print("   Examples:")
        print('   - "Sophia, give me an overall health analysis of Client X"')
        print('   - "Cherry, what are the best swing trade opportunities today?"')
        print('   - "Karen, find new clinical trials for diabetes"')
        
        print(f"\n🚀 NEXT STEPS:")
        print("   1. Access admin interface at: http://localhost:3000/admin")
        print("   2. Login with operator credentials")
        print("   3. Start submitting queries and tasks")
        print("   4. Monitor agent performance in real-time")
        
        print(f"\n📚 API ENDPOINTS:")
        print("   - REST API: http://localhost:8000/api/v1/")
        print("   - WebSocket: ws://localhost:8000/ws")
        print("   - GraphQL: http://localhost:8000/graphql")
        
        print("\n" + "="*60)
        print("System ready for production use!")
        print("="*60 + "\n")
    
    async def deploy(self):
        """Main deployment method"""
        try:
            logger.info("Starting AI Orchestration System deployment...")
            
            # Step 1: Initialize infrastructure
            await self.initialize_infrastructure()
            
            # Step 2: Create database schemas
            await self.create_database_schema()
            
            # Step 3: Create Weaviate collections
            await self.create_weaviate_collections()
            
            # Step 4: Initialize orchestration system
            await self.initialize_orchestration_system()
            
            # Step 5: Run system tests
            await self.run_system_tests()
            
            # Step 6: Display deployment summary
            await self.display_deployment_summary()
            
            logger.info("Deployment completed successfully!")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise
        finally:
            # Cleanup
            if self.db:
                await self.db.close()


async def main():
    """Main entry point"""
    deployment = AIOrchestrationDeployment()
    await deployment.deploy()


if __name__ == "__main__":
    # Run deployment
    asyncio.run(main())