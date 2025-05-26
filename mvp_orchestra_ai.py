#!/usr/bin/env python3
"""
Orchestra AI MVP - Complete Integration
Combines enhanced vector memory, data source integrations, and natural language interface.
"""

import argparse
import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from data_source_integrations import DataAggregationOrchestrator, DataSourceConfig
from enhanced_natural_language_interface import (
    ConversationMode,
    EnhancedNaturalLanguageInterface,
)
from enhanced_vector_memory_system import EnhancedVectorMemorySystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("orchestra_ai_mvp.log")],
)
logger = logging.getLogger("orchestra_ai_mvp")


class OrchestraAIMVP:
    """
    Complete Orchestra AI MVP integration.

    Provides:
    - Enhanced vector memory with semantic search
    - Multi-source data aggregation (Gong, Salesforce, HubSpot, Slack, Looker)
    - Advanced natural language interface with context awareness
    - Real-time conversation capabilities
    """

    def __init__(
        self, project_id: str = "cherry-ai-project", user_id: str = "default_user"
    ):
        self.project_id = project_id
        self.user_id = user_id

        # Core components
        self.memory_system: Optional[EnhancedVectorMemorySystem] = None
        self.data_orchestrator: Optional[DataAggregationOrchestrator] = None
        self.nl_interface: Optional[EnhancedNaturalLanguageInterface] = None

        # Configuration
        self.configs: Dict[str, DataSourceConfig] = {}

        logger.info(
            f"Orchestra AI MVP initialized for project {project_id}, user {user_id}"
        )

    async def initialize(self) -> None:
        """Initialize all MVP components."""
        logger.info("Initializing Orchestra AI MVP components...")

        # Initialize memory system
        self.memory_system = EnhancedVectorMemorySystem(
            project_id=self.project_id,
            embedding_model="all-MiniLM-L6-v2",
            redis_url="redis://localhost:6379",
        )
        await self.memory_system.initialize()
        logger.info("✓ Enhanced Vector Memory System initialized")

        # Initialize data orchestrator
        self.data_orchestrator = DataAggregationOrchestrator(
            memory_system=self.memory_system, user_id=self.user_id
        )

        # Setup data source configurations
        await self._setup_data_source_configs()
        await self.data_orchestrator.setup_default_integrations(self.configs)
        logger.info("✓ Data Aggregation Orchestrator initialized")

        # Initialize natural language interface
        portkey_api_key = os.getenv("PORTKEY_API_KEY", "")
        self.nl_interface = EnhancedNaturalLanguageInterface(
            memory_system=self.memory_system,
            data_orchestrator=self.data_orchestrator,
            project_id=self.project_id,
            portkey_api_key=portkey_api_key,
        )
        logger.info("✓ Enhanced Natural Language Interface initialized")

        logger.info("🚀 Orchestra AI MVP fully initialized and ready!")

    async def _setup_data_source_configs(self) -> None:
        """
        Setup configurations for all data sources.

        Each integration requires specific environment variables to be set.
        If any required variable is missing, the integration will be skipped and a warning will be logged.
        See .env.template for required variable names.
        """

        # --- Gong.io ---
        # Requires: GONG_API_KEY
        if os.getenv("GONG_API_KEY"):
            self.configs["gong"] = DataSourceConfig(
                name="gong",
                api_key=os.getenv("GONG_API_KEY"),
                base_url="https://api.gong.io",
                rate_limit=0.5,  # 0.5 requests per second
            )
            logger.info("✓ Gong.io configuration loaded")
        else:
            logger.warning("Gong.io integration skipped: GONG_API_KEY not set.")

        # --- Salesforce ---
        # Requires: SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET
        if os.getenv("SALESFORCE_CLIENT_ID") and os.getenv("SALESFORCE_CLIENT_SECRET"):
            self.configs["salesforce"] = DataSourceConfig(
                name="salesforce",
                api_key=os.getenv("SALESFORCE_CLIENT_ID"),
                base_url="https://login.salesforce.com",
                additional_headers={
                    "client_secret": os.getenv("SALESFORCE_CLIENT_SECRET")
                },
                rate_limit=2.0,  # 2 requests per second
            )
            logger.info("✓ Salesforce configuration loaded")
        else:
            logger.warning(
                "Salesforce integration skipped: SALESFORCE_CLIENT_ID or SALESFORCE_CLIENT_SECRET not set."
            )

        # --- HubSpot ---
        # Requires: HUBSPOT_API_KEY
        if os.getenv("HUBSPOT_API_KEY"):
            self.configs["hubspot"] = DataSourceConfig(
                name="hubspot",
                api_key=os.getenv("HUBSPOT_API_KEY"),
                base_url="https://api.hubapi.com",
                rate_limit=10.0,  # 10 requests per second
            )
            logger.info("✓ HubSpot configuration loaded")
        else:
            logger.warning("HubSpot integration skipped: HUBSPOT_API_KEY not set.")

        # --- Slack ---
        # Requires: SLACK_API_KEY
        if os.getenv("SLACK_API_KEY"):
            self.configs["slack"] = DataSourceConfig(
                name="slack",
                api_key=os.getenv("SLACK_API_KEY"),
                base_url="https://slack.com/api",
                rate_limit=1.0,  # 1 request per second
            )
            logger.info("✓ Slack configuration loaded")
        else:
            logger.warning("Slack integration skipped: SLACK_API_KEY not set.")

        # --- Looker ---
        # Requires: LOOKER_CLIENT_ID, LOOKER_CLIENT_SECRET
        if os.getenv("LOOKER_CLIENT_ID") and os.getenv("LOOKER_CLIENT_SECRET"):
            self.configs["looker"] = DataSourceConfig(
                name="looker",
                api_key=os.getenv("LOOKER_CLIENT_ID"),
                base_url=os.getenv(
                    "LOOKER_BASE_URL", "https://your-company.looker.com"
                ),
                additional_headers={"client_secret": os.getenv("LOOKER_CLIENT_SECRET")},
                rate_limit=5.0,  # 5 requests per second
            )
            logger.info("✓ Looker configuration loaded")
        else:
            logger.warning(
                "Looker integration skipped: LOOKER_CLIENT_ID or LOOKER_CLIENT_SECRET not set."
            )

        total_sources = len(self.configs)
        logger.info(f"✓ Configured {total_sources} data sources")

    async def sync_all_data(self, since_hours: int = 24) -> Dict[str, int]:
        """Sync data from all configured sources."""
        if not self.data_orchestrator:
            raise RuntimeError("MVP not initialized. Call initialize() first.")

        since = datetime.utcnow().replace(hour=datetime.utcnow().hour - since_hours)

        logger.info(f"Starting data synchronization for last {since_hours} hours...")
        results = await self.data_orchestrator.sync_all_sources(since)

        total_items = sum(count for count in results.values() if count > 0)
        logger.info(f"✓ Synchronization complete: {total_items} total items synced")

        return results

    async def start_conversation(
        self, initial_query: Optional[str] = None, mode: str = "casual"
    ) -> str:
        """Start a new conversation session."""
        if not self.nl_interface:
            raise RuntimeError("MVP not initialized. Call initialize() first.")

        conversation_mode = ConversationMode(mode)
        session = await self.nl_interface.start_conversation(
            user_id=self.user_id, initial_query=initial_query, mode=conversation_mode
        )

        logger.info(f"✓ Started conversation {session.id} in {mode} mode")
        return session.id

    async def chat(self, conversation_id: str, message: str) -> str:
        """Send a message in an existing conversation."""
        if not self.nl_interface:
            raise RuntimeError("MVP not initialized. Call initialize() first.")

        response_msg = await self.nl_interface.process_message(conversation_id, message)

        logger.info(f"Processed message in conversation {conversation_id}")
        return response_msg.content

    async def search_memory(
        self, query: str, sources: Optional[list] = None, top_k: int = 5
    ) -> list:
        """Search across all aggregated data with semantic search."""
        if not self.memory_system:
            raise RuntimeError("MVP not initialized. Call initialize() first.")

        memories = await self.memory_system.semantic_search(
            user_id=self.user_id, query=query, sources=sources, top_k=top_k
        )

        results = []
        for memory in memories:
            results.append(
                {
                    "content": memory.content[:300] + "...",
                    "source": memory.source,
                    "relevance": memory.relevance_score,
                    "timestamp": memory.timestamp.isoformat(),
                    "metadata": memory.source_metadata,
                }
            )

        logger.info(
            f"Memory search returned {len(results)} results for query: {query[:50]}..."
        )
        return results

    async def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get full context for a conversation."""
        if not self.nl_interface:
            raise RuntimeError("MVP not initialized. Call initialize() first.")

        history = await self.nl_interface.get_conversation_history(conversation_id)

        context = {
            "conversation_id": conversation_id,
            "message_count": len(history),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "intent": msg.intent,
                    "metadata": msg.metadata,
                }
                for msg in history
            ],
        }

        return context

    async def close(self) -> None:
        """Clean up and close all connections."""
        if self.memory_system:
            await self.memory_system.close()

        if self.data_orchestrator:
            for integration in self.data_orchestrator.integrations.values():
                await integration.close()

        logger.info("✓ Orchestra AI MVP connections closed")


# CLI Interface
async def main():
    """Command-line interface for Orchestra AI MVP."""
    parser = argparse.ArgumentParser(
        description="Orchestra AI MVP - Enhanced AI Assistant"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize the MVP system")
    init_parser.add_argument(
        "--project-id", default="cherry-ai-project", help="GCP Project ID"
    )
    init_parser.add_argument("--user-id", default="default_user", help="User ID")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync data from all sources")
    sync_parser.add_argument(
        "--hours", type=int, default=24, help="Hours of data to sync"
    )
    sync_parser.add_argument(
        "--project-id", default="cherry-ai-project", help="GCP Project ID"
    )
    sync_parser.add_argument("--user-id", default="default_user", help="User ID")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat session")
    chat_parser.add_argument(
        "--mode",
        default="casual",
        choices=["casual", "analytical", "technical", "strategic", "creative"],
        help="Conversation mode",
    )
    chat_parser.add_argument(
        "--project-id", default="cherry-ai-project", help="GCP Project ID"
    )
    chat_parser.add_argument("--user-id", default="default_user", help="User ID")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search memory")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--sources", nargs="+", help="Specific sources to search"
    )
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    search_parser.add_argument(
        "--project-id", default="cherry-ai-project", help="GCP Project ID"
    )
    search_parser.add_argument("--user-id", default="default_user", help="User ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize MVP
    mvp = OrchestraAIMVP(project_id=args.project_id, user_id=args.user_id)

    try:
        if args.command == "init":
            await mvp.initialize()
            print("✅ Orchestra AI MVP initialized successfully!")

        elif args.command == "sync":
            await mvp.initialize()
            results = await mvp.sync_all_data(since_hours=args.hours)

            print("\n📊 Data Synchronization Results:")
            for source, count in results.items():
                status = "✅" if count >= 0 else "❌"
                print(f"{status} {source.upper()}: {count} items")

        elif args.command == "search":
            await mvp.initialize()
            results = await mvp.search_memory(
                query=args.query, sources=args.sources, top_k=args.top_k
            )

            print(f"\n🔍 Search Results for: '{args.query}'")
            for i, result in enumerate(results, 1):
                print(
                    f"\n{i}. [{result['source'].upper()}] (Relevance: {result['relevance']:.3f})"
                )
                print(f"   {result['content']}")
                print(f"   Time: {result['timestamp']}")

        elif args.command == "chat":
            await mvp.initialize()
            conversation_id = await mvp.start_conversation(mode=args.mode)

            print(f"\n💬 Orchestra AI Chat Session ({args.mode} mode)")
            print("Type 'quit', 'exit', or 'bye' to end the conversation.")
            print("Type 'sync' to synchronize data from all sources.")
            print("Type 'search <query>' to search memory.")
            print("-" * 50)

            while True:
                try:
                    user_input = input("\nYou: ").strip()

                    if user_input.lower() in ["quit", "exit", "bye"]:
                        await mvp.nl_interface.end_conversation(conversation_id)
                        print("👋 Goodbye!")
                        break

                    if user_input.lower() == "sync":
                        print("🔄 Syncing data...")
                        results = await mvp.sync_all_data()
                        total = sum(count for count in results.values() if count > 0)
                        print(f"✅ Synced {total} items total")
                        continue

                    if user_input.lower().startswith("search "):
                        query = user_input[7:]  # Remove 'search '
                        results = await mvp.search_memory(query, top_k=3)
                        print(f"\n🔍 Found {len(results)} results:")
                        for i, result in enumerate(results, 1):
                            print(
                                f"  {i}. [{result['source'].upper()}] {result['content'][:100]}..."
                            )
                        continue

                    if not user_input:
                        continue

                    # Process the message
                    response = await mvp.chat(conversation_id, user_input)
                    print(f"\nAssistant: {response}")

                except KeyboardInterrupt:
                    await mvp.nl_interface.end_conversation(conversation_id)
                    print("\n\n👋 Session ended. Goodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    logger.error(f"Chat error: {e}")

    except Exception as e:
        logger.error(f"MVP error: {e}")
        print(f"❌ Error: {e}")

    finally:
        await mvp.close()


if __name__ == "__main__":
    asyncio.run(main())
