#!/usr/bin/env python3
"""
🧠 Enhanced Memory Server v2 - 5-Tier Architecture with Updated Personas
Integrated with Cherry (8K), Sophia (12K), Karen (6K) for Cursor AI supercharging
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import uuid

# MCP imports
from mcp.server import Server
from mcp import types
from mcp.server.stdio import stdio_server

# Memory architecture imports
from memory_architecture import PersonaDomain, PERSONA_CONFIGS, PersonaEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """Enhanced memory entry with persona context"""
    id: str
    persona: str
    content: str
    context_type: str  # 'coding', 'conversation', 'project', 'preference'
    importance: float
    timestamp: datetime
    tags: List[str]
    tier: int  # 0-4 (L0-L4)
    cross_domain_access: List[str]
    metadata: Dict[str, Any]

class FiveTierMemorySystem:
    """5-Tier Memory Architecture for Orchestra AI"""
    
    def __init__(self):
        self.tiers = {
            0: {},  # L0: CPU Cache (~1ns) - Hot data
            1: {},  # L1: Process Memory (~10ns) - Session context  
            2: {},  # L2: Shared Memory (~100ns) - Cross-persona sharing
            3: {},  # L3: PostgreSQL (~1ms) - Structured history
            4: {}   # L4: Weaviate (~10ms) - Vector embeddings & semantic search
        }
        self.personas = {
            'cherry': PERSONA_CONFIGS[PersonaDomain.CHERRY],
            'sophia': PERSONA_CONFIGS[PersonaDomain.SOPHIA], 
            'karen': PERSONA_CONFIGS[PersonaDomain.KAREN]
        }
        
    async def store_memory(self, entry: MemoryEntry) -> bool:
        """Store memory entry in appropriate tier based on importance and type"""
        try:
            # Determine optimal tier based on importance and type
            tier = self._determine_tier(entry)
            entry.tier = tier
            
            # Store in selected tier
            self.tiers[tier][entry.id] = entry
            
            # Apply persona-specific retention and cross-domain rules
            await self._apply_persona_rules(entry)
            
            logger.info(f"Stored memory {entry.id} in tier L{tier} for persona {entry.persona}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return False
    
    def _determine_tier(self, entry: MemoryEntry) -> int:
        """Determine optimal memory tier for entry"""
        if entry.context_type == 'coding' and entry.importance > 0.8:
            return 0  # L0: Hot coding context
        elif entry.context_type == 'conversation' and entry.importance > 0.6:
            return 1  # L1: Active conversation
        elif entry.persona == 'cherry' and 'cross-domain' in entry.tags:
            return 2  # L2: Cross-domain coordination
        elif entry.context_type in ['project', 'workflow']:
            return 3  # L3: Structured project data
        else:
            return 4  # L4: Long-term semantic storage
    
    async def _apply_persona_rules(self, entry: MemoryEntry):
        """Apply persona-specific memory rules"""
        persona_config = self.personas.get(entry.persona)
        if not persona_config:
            return
        
        # Cherry gets broader access
        if entry.persona == 'cherry':
            entry.cross_domain_access = ['sophia', 'karen']
        
        # Sophia (Pay Ready Guru) gets comprehensive retention
        elif entry.persona == 'sophia':
            if entry.importance > 0.3:  # Lower threshold for comprehensive storage
                entry.cross_domain_access = ['cherry']
        
        # Karen (ParagonRX) gets focused retention
        elif entry.persona == 'karen':
            if 'paragonrx' in entry.tags or 'medical' in entry.tags:
                entry.cross_domain_access = ['cherry']
    
    async def retrieve_memory(self, persona: str, query: str, context_type: str = None) -> List[MemoryEntry]:
        """Retrieve relevant memories across all tiers for persona"""
        results = []
        
        # Search through tiers in order of access speed
        for tier in range(5):
            tier_results = await self._search_tier(tier, persona, query, context_type)
            results.extend(tier_results)
        
        # Apply persona-specific filtering and ranking
        filtered_results = self._apply_persona_filtering(persona, results)
        
        return sorted(filtered_results, key=lambda x: x.importance, reverse=True)[:10]
    
    async def _search_tier(self, tier: int, persona: str, query: str, context_type: str) -> List[MemoryEntry]:
        """Search specific memory tier"""
        results = []
        
        for entry in self.tiers[tier].values():
            # Check persona access rights
            if entry.persona == persona or persona in entry.cross_domain_access:
                # Check context type match
                if context_type is None or entry.context_type == context_type:
                    # Simple text matching (would be enhanced with vector search for L4)
                    if query.lower() in entry.content.lower() or any(tag in query.lower() for tag in entry.tags):
                        results.append(entry)
        
        return results
    
    def _apply_persona_filtering(self, persona: str, results: List[MemoryEntry]) -> List[MemoryEntry]:
        """Apply persona-specific filtering and access rules"""
        persona_config = self.personas.get(persona)
        if not persona_config:
            return results
        
        # Cherry gets access to everything
        if persona == 'cherry':
            return results
        
        # Sophia gets access to business intelligence and pay ready context
        elif persona == 'sophia':
            return [r for r in results if 
                   r.persona == 'sophia' or 
                   'business' in r.tags or 
                   'payready' in r.tags or
                   persona in r.cross_domain_access]
        
        # Karen gets access to ParagonRX and medical context
        elif persona == 'karen':
            return [r for r in results if 
                   r.persona == 'karen' or 
                   'paragonrx' in r.tags or 
                   'medical' in r.tags or
                   persona in r.cross_domain_access]
        
        return results

class EnhancedMemoryMCPServer:
    """Enhanced MCP server for 5-tier memory management"""
    
    def __init__(self):
        self.server = Server("enhanced-memory")
        self.memory_system = FiveTierMemorySystem()
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup enhanced MCP tools for memory operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List available memory tools"""
            return [
                types.Tool(
                    name="store_memory",
                    description="Store memory in 5-tier architecture with persona context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
                            "content": {"type": "string"},
                            "context_type": {"type": "string", "enum": ["coding", "conversation", "project", "preference", "workflow"]},
                            "importance": {"type": "number", "minimum": 0, "maximum": 1},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "metadata": {"type": "object"}
                        },
                        "required": ["persona", "content", "context_type", "importance"]
                    }
                ),
                types.Tool(
                    name="retrieve_memory",
                    description="Retrieve memories for persona with 5-tier search",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "persona": {"type": "string", "enum": ["cherry", "sophia", "karen"]},
                            "query": {"type": "string"},
                            "context_type": {"type": "string", "enum": ["coding", "conversation", "project", "preference", "workflow"]},
                            "max_results": {"type": "integer", "minimum": 1, "maximum": 20}
                        },
                        "required": ["persona", "query"]
                    }
                ),
                types.Tool(
                    name="get_memory_status",
                    description="Get 5-tier memory system status and persona statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_details": {"type": "boolean"}
                        }
                    }
                ),
                types.Tool(
                    name="cross_domain_query",
                    description="Cherry's cross-domain memory access across all personas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "domains": {"type": "array", "items": {"type": "string", "enum": ["cherry", "sophia", "karen"]}},
                            "synthesis_required": {"type": "boolean"}
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls for memory operations"""
            
            if name == "store_memory":
                return await self._handle_store_memory(arguments)
            elif name == "retrieve_memory":
                return await self._handle_retrieve_memory(arguments)
            elif name == "get_memory_status":
                return await self._handle_memory_status(arguments)
            elif name == "cross_domain_query":
                return await self._handle_cross_domain_query(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_store_memory(self, args: dict) -> List[types.TextContent]:
        """Handle memory storage requests"""
        try:
            entry = MemoryEntry(
                id=str(uuid.uuid4()),
                persona=args['persona'],
                content=args['content'],
                context_type=args['context_type'],
                importance=args['importance'],
                timestamp=datetime.now(),
                tags=args.get('tags', []),
                tier=0,  # Will be determined by system
                cross_domain_access=[],  # Will be set by persona rules
                metadata=args.get('metadata', {})
            )
            
            success = await self.memory_system.store_memory(entry)
            
            if success:
                return [types.TextContent(
                    type="text",
                    text=f"✅ Memory stored successfully in tier L{entry.tier} for {entry.persona}"
                )]
            else:
                return [types.TextContent(
                    type="text", 
                    text="❌ Failed to store memory"
                )]
                
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error storing memory: {str(e)}"
            )]
    
    async def _handle_retrieve_memory(self, args: dict) -> List[types.TextContent]:
        """Handle memory retrieval requests"""
        try:
            results = await self.memory_system.retrieve_memory(
                persona=args['persona'],
                query=args['query'],
                context_type=args.get('context_type')
            )
            
            if results:
                response = f"🧠 Found {len(results)} memories for {args['persona']}:\n\n"
                for i, entry in enumerate(results[:args.get('max_results', 5)], 1):
                    response += f"{i}. [L{entry.tier}] {entry.content[:100]}...\n"
                    response += f"   Tags: {', '.join(entry.tags)}\n"
                    response += f"   Importance: {entry.importance:.2f}\n\n"
            else:
                response = f"🔍 No memories found for query: {args['query']}"
                
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error retrieving memories: {str(e)}"
            )]
    
    async def _handle_memory_status(self, args: dict) -> List[types.TextContent]:
        """Handle memory system status requests"""
        try:
            include_details = args.get('include_details', False)
            
            status = "🧠 5-Tier Memory System Status\n"
            status += "================================\n\n"
            
            # Tier statistics
            for tier in range(5):
                count = len(self.memory_system.tiers[tier])
                tier_names = ["CPU Cache", "Process Memory", "Shared Memory", "PostgreSQL", "Weaviate"]
                latency = ["~1ns", "~10ns", "~100ns", "~1ms", "~10ms"]
                status += f"L{tier} ({tier_names[tier]}): {count} entries ({latency[tier]})\n"
            
            status += "\n📊 Persona Context Windows:\n"
            status += "- 💼 Sophia (Pay Ready Guru): 12,000 tokens\n"
            status += "- 🍒 Cherry (Coordinator): 8,000 tokens\n" 
            status += "- ⚕️ Karen (ParagonRX): 6,000 tokens\n"
            
            if include_details:
                status += "\n🔍 Detailed Statistics:\n"
                for persona, config in self.memory_system.personas.items():
                    status += f"\n{persona.title()}:\n"
                    status += f"  - Max memories: {config.max_memories}\n"
                    status += f"  - Retention: {config.retention_days} days\n"
                    status += f"  - Cross-domain access: {config.cross_domain_access}\n"
            
            return [types.TextContent(type="text", text=status)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error getting memory status: {str(e)}"
            )]
    
    async def _handle_cross_domain_query(self, args: dict) -> List[types.TextContent]:
        """Handle Cherry's cross-domain memory queries"""
        try:
            query = args['query']
            domains = args.get('domains', ['cherry', 'sophia', 'karen'])
            
            all_results = []
            
            # Search across specified domains
            for domain in domains:
                results = await self.memory_system.retrieve_memory(
                    persona='cherry',  # Cherry has cross-domain access
                    query=query
                )
                all_results.extend(results)
            
            # Remove duplicates and sort by importance
            unique_results = {r.id: r for r in all_results}.values()
            sorted_results = sorted(unique_results, key=lambda x: x.importance, reverse=True)
            
            if sorted_results:
                response = f"🔄 Cross-domain search results for: {query}\n"
                response += f"Searched domains: {', '.join(domains)}\n\n"
                
                for i, entry in enumerate(sorted_results[:10], 1):
                    response += f"{i}. [{entry.persona.upper()}] [L{entry.tier}] {entry.content[:100]}...\n"
                    response += f"   Importance: {entry.importance:.2f} | Tags: {', '.join(entry.tags)}\n\n"
            else:
                response = f"🔍 No cross-domain results found for: {query}"
            
            return [types.TextContent(type="text", text=response)]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error in cross-domain query: {str(e)}"
            )]

async def main():
    """Main server execution"""
    logger.info("🧠 Starting Enhanced Memory Server v2 (5-Tier Architecture)")
    logger.info("📊 Persona Configuration:")
    logger.info("   - Sophia (Pay Ready Guru): 12K context, 25K memories, 365 days retention")
    logger.info("   - Cherry (Coordinator): 8K context, 15K memories, 365 days retention")
    logger.info("   - Karen (ParagonRX): 6K context, 12K memories, 180 days retention")
    
    server = EnhancedMemoryMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            None
        )

if __name__ == "__main__":
    asyncio.run(main()) 