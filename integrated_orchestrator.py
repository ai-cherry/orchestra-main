"""
Integrated Orchestrator System
Combines advanced memory architecture with deep persona profiles
for Cherry, Sophia, and Karen AI orchestrators
"""

from typing import Dict, List, Any, Optional, Tuple
import asyncio
import json
from datetime import datetime, timedelta
from dataclasses import asdict

from memory_architecture import (
    LayeredMemoryManager, MemoryTier, PersonaDomain, 
    PERSONA_CONFIGS, HybridSearchEngine, TokenCompressionEngine
)
from persona_profiles import (
    PersonaManager, PersonaProfile, create_persona,
    CommunicationStyle, EmotionalTone
)

class OrchestrationContext:
    """Context manager for persona interactions and memory operations"""
    
    def __init__(self, 
                 requesting_persona: str,
                 task_type: str,
                 urgency_level: float = 0.5,
                 technical_complexity: float = 0.5,
                 collaborative: bool = False,
                 cross_domain_required: List[str] = None):
        self.requesting_persona = requesting_persona
        self.task_type = task_type
        self.urgency_level = urgency_level
        self.technical_complexity = technical_complexity
        self.collaborative = collaborative
        self.cross_domain_required = cross_domain_required or []
        self.timestamp = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for memory storage"""
        return {
            "persona": self.requesting_persona,
            "task_type": self.task_type,
            "urgency": self.urgency_level,
            "technical_complexity": self.technical_complexity,
            "collaborative": self.collaborative,
            "cross_domain": self.cross_domain_required,
            "timestamp": self.timestamp.isoformat()
        }

class IntegratedOrchestrator:
    """Main orchestrator that integrates memory and persona systems"""
    
    def __init__(self):
        self.memory_manager = LayeredMemoryManager()
        self.persona_manager = PersonaManager()
        self.compression_engine = TokenCompressionEngine()
        self.search_engine = HybridSearchEngine()
        
        # Performance tracking
        self.performance_metrics = {
            "total_interactions": 0,
            "cross_domain_queries": 0,
            "memory_compressions": 0,
            "average_response_time": 0.0,
            "persona_switches": 0
        }
        
    async def initialize(self, config: Dict[str, Any]):
        """Initialize all memory tiers and persona configurations"""
        
        # Initialize memory tiers
        for tier in MemoryTier:
            tier_config = config.get(tier.value, {})
            await self.memory_manager.initialize_tier(tier, tier_config)
            
        # Load persona-specific memory configurations
        for persona_domain in PersonaDomain:
            persona_config = PERSONA_CONFIGS[persona_domain]
            await self._initialize_persona_memory(persona_domain, persona_config)
            
        print("🚀 Integrated Orchestrator initialized with all personas and memory tiers")
        
    async def _initialize_persona_memory(self, domain: PersonaDomain, config):
        """Initialize memory structures for specific persona"""
        
        # Create persona-specific tables/collections
        if domain == PersonaDomain.CHERRY:
            await self._create_cherry_memory_structures(config)
        elif domain == PersonaDomain.SOPHIA:
            await self._create_sophia_memory_structures(config)
        elif domain == PersonaDomain.KAREN:
            await self._create_karen_memory_structures(config)
            
    async def process_request(self, 
                            persona_name: str, 
                            query: str, 
                            context: OrchestrationContext = None) -> Dict[str, Any]:
        """Main request processing pipeline"""
        
        start_time = datetime.now()
        
        # Get persona profile
        persona = self.persona_manager.get_persona(persona_name)
        if not persona:
            raise ValueError(f"Unknown persona: {persona_name}")
            
        # Set default context if none provided
        if not context:
            context = OrchestrationContext(
                requesting_persona=persona_name,
                task_type="general_query"
            )
            
        # Step 1: Retrieve relevant memories
        relevant_memories = await self._retrieve_memories(persona, query, context)
        
        # Step 2: Compress context if needed
        compressed_context = await self._manage_context_window(
            persona, query, relevant_memories, context
        )
        
        # Step 3: Handle cross-domain requirements
        cross_domain_context = {}
        if context.cross_domain_required:
            cross_domain_context = await self._handle_cross_domain_query(
                persona, context.cross_domain_required
            )
            
        # Step 4: Generate persona-specific response
        response = await self._generate_response(
            persona, query, compressed_context, cross_domain_context, context
        )
        
        # Step 5: Store interaction in memory
        await self._store_interaction(persona, query, response, context)
        
        # Update performance metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        await self._update_metrics(processing_time, context)
        
        return {
            "persona": persona_name,
            "response": response,
            "context_used": compressed_context,
            "cross_domain_data": cross_domain_context,
            "processing_time_ms": processing_time * 1000,
            "memory_compression_ratio": getattr(compressed_context, 'compression_ratio', 1.0)
        }
        
    async def _retrieve_memories(self, 
                               persona: PersonaProfile, 
                               query: str, 
                               context: OrchestrationContext) -> List[Dict]:
        """Retrieve relevant memories using hybrid search"""
        
        # Determine search strategy based on persona and query
        persona_domain = PersonaDomain(persona.name.lower())
        
        # Use hybrid search engine with persona-specific parameters
        search_results = await self.search_engine.search(
            query=query,
            persona=persona_domain,
            cross_domain=bool(context.cross_domain_required)
        )
        
        # Filter results based on persona's memory configuration
        config = PERSONA_CONFIGS[persona_domain]
        filtered_results = self._filter_by_importance(
            search_results, config.importance_threshold
        )
        
        # Limit to max memories per context
        max_memories = config.max_memories_per_context if hasattr(config, 'max_memories_per_context') else 10
        return filtered_results[:max_memories]
        
    async def _manage_context_window(self, 
                                   persona: PersonaProfile,
                                   query: str, 
                                   memories: List[Dict],
                                   context: OrchestrationContext) -> str:
        """Manage context window through compression and prioritization"""
        
        persona_domain = PersonaDomain(persona.name.lower())
        config = PERSONA_CONFIGS[persona_domain]
        
        # Combine query, memories, and context into full context
        full_context = {
            "query": query,
            "memories": memories,
            "context": context.to_dict(),
            "persona_config": asdict(config)
        }
        
        context_text = json.dumps(full_context, indent=2)
        
        # Check if compression is needed
        estimated_tokens = len(context_text) // 4  # Rough token estimation
        
        if estimated_tokens > config.context_window:
            # Apply compression
            compressed = await self.compression_engine.compress_context(
                context_text, persona_domain
            )
            
            # Track compression metrics
            self.performance_metrics["memory_compressions"] += 1
            compression_ratio = len(context_text) / len(compressed)
            
            return {
                "content": compressed,
                "compression_ratio": compression_ratio,
                "original_tokens": estimated_tokens,
                "compressed_tokens": len(compressed) // 4
            }
        else:
            return {
                "content": context_text,
                "compression_ratio": 1.0,
                "original_tokens": estimated_tokens,
                "compressed_tokens": estimated_tokens
            }
            
    async def _handle_cross_domain_query(self, 
                                       requesting_persona: PersonaProfile,
                                       required_domains: List[str]) -> Dict[str, Any]:
        """Handle cross-domain queries with appropriate access controls"""
        
        cross_domain_data = {}
        
        for domain in required_domains:
            # Check if requesting persona has access
            requesting_config = PERSONA_CONFIGS[PersonaDomain(requesting_persona.name.lower())]
            
            if domain in requesting_config.cross_domain_access:
                # Get expert persona for this domain
                expert_persona = self.persona_manager._find_domain_expert(domain)
                
                if expert_persona:
                    # Retrieve domain-specific context
                    domain_context = await self._get_domain_context(expert_persona, domain)
                    cross_domain_data[domain] = {
                        "expert_persona": expert_persona.name,
                        "context": domain_context,
                        "access_granted": True
                    }
                else:
                    cross_domain_data[domain] = {
                        "expert_persona": None,
                        "context": None,
                        "access_granted": False,
                        "reason": "No expert found"
                    }
            else:
                cross_domain_data[domain] = {
                    "access_granted": False,
                    "reason": "Insufficient permissions"
                }
                
        # Track cross-domain usage
        self.performance_metrics["cross_domain_queries"] += 1
        
        return cross_domain_data
        
    async def _generate_response(self, 
                               persona: PersonaProfile,
                               query: str,
                               context: Dict[str, Any],
                               cross_domain_context: Dict[str, Any],
                               orchestration_context: OrchestrationContext) -> str:
        """Generate persona-specific response using all available context"""
        
        # Build full prompt with persona characteristics
        personality_prompt = persona.get_context_adapted_prompt(
            orchestration_context.to_dict()
        )
        
        # Combine all context elements
        full_prompt = f"""
{personality_prompt}

Current Context:
{context.get('content', '')}

Cross-Domain Information:
{json.dumps(cross_domain_context, indent=2) if cross_domain_context else 'None'}

User Query: {query}

Please provide a response that:
1. Reflects your personality and communication style
2. Uses your domain expertise appropriately
3. Incorporates relevant cross-domain information if available
4. Maintains appropriate professional boundaries
"""
        
        # This would integrate with your LLM of choice
        # For now, return a structured response format
        response = await self._call_llm(full_prompt, persona)
        
        return response
        
    async def _call_llm(self, prompt: str, persona: PersonaProfile) -> str:
        """Call LLM with persona-specific parameters"""
        
        # This would integrate with your actual LLM service
        # Example structure:
        
        llm_params = {
            "prompt": prompt,
            "temperature": 0.7 if persona.personality.openness > 0.8 else 0.5,
            "max_tokens": 2000 if persona.communication.response_length == "detailed" else 1000,
            "frequency_penalty": 0.1 if persona.communication.use_of_metaphors else 0.0
        }
        
        # Placeholder response - replace with actual LLM call
        return f"[{persona.name} response would be generated here with LLM integration]"
        
    async def _store_interaction(self, 
                               persona: PersonaProfile,
                               query: str,
                               response: str,
                               context: OrchestrationContext):
        """Store interaction in appropriate memory tiers"""
        
        interaction_data = {
            "persona": persona.name,
            "query": query,
            "response": response,
            "context": context.to_dict(),
            "timestamp": datetime.now().isoformat(),
            "memory_tier": "L3_POSTGRESQL"  # Primary storage
        }
        
        # Store in PostgreSQL (L3)
        await self._store_in_postgresql(interaction_data)
        
        # Cache in Redis (L2) for hot access
        await self._store_in_redis(interaction_data)
        
        # Create vector embedding for long-term semantic search (L4)
        await self._store_vector_embedding(interaction_data)
        
        # Update persona's interaction history
        persona.interaction_history.append(interaction_data)
        
        # Learn from interaction
        await persona.adaptation_engine.update_from_interaction(query, response)
        
    async def _update_metrics(self, processing_time: float, context: OrchestrationContext):
        """Update performance metrics"""
        
        self.performance_metrics["total_interactions"] += 1
        
        # Update average response time
        current_avg = self.performance_metrics["average_response_time"]
        total_interactions = self.performance_metrics["total_interactions"]
        
        new_avg = ((current_avg * (total_interactions - 1)) + processing_time) / total_interactions
        self.performance_metrics["average_response_time"] = new_avg
        
        # Track persona switches if context indicates cross-domain activity
        if context.cross_domain_required:
            self.performance_metrics["persona_switches"] += 1
            
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        
        return {
            "performance_metrics": self.performance_metrics,
            "persona_states": {
                name: {
                    "total_interactions": len(persona.interaction_history),
                    "learned_patterns": len(persona.learned_patterns),
                    "current_context": persona.current_context
                }
                for name, persona in self.persona_manager.personas.items()
            },
            "memory_tiers_status": {
                tier.value: "active" for tier in MemoryTier
            }
        }
        
    # Helper methods for memory operations
    async def _filter_by_importance(self, results: List[Dict], threshold: float) -> List[Dict]:
        """Filter search results by importance threshold"""
        return [r for r in results if r.get('importance_score', 0) >= threshold]
        
    async def _get_domain_context(self, expert_persona: PersonaProfile, domain: str) -> Dict[str, Any]:
        """Get domain-specific context from expert persona"""
        return {
            "expertise_level": expert_persona.expertise.primary_domains.get(domain, 0.0),
            "recent_interactions": expert_persona.interaction_history[-5:],  # Last 5 interactions
            "learned_patterns": expert_persona.learned_patterns.get(domain, {})
        }
        
    async def _create_cherry_memory_structures(self, config):
        """Create Cherry's memory structures"""
        # Implementation would create Cherry-specific tables and indexes
        pass
        
    async def _create_sophia_memory_structures(self, config):
        """Create Sophia's memory structures with encryption"""
        # Implementation would create Sophia-specific encrypted tables
        pass
        
    async def _create_karen_memory_structures(self, config):
        """Create Karen's memory structures with medical compliance"""
        # Implementation would create Karen-specific HIPAA-compliant tables
        pass
        
    async def _store_in_postgresql(self, data: Dict[str, Any]):
        """Store in PostgreSQL (L3 tier)"""
        # Implementation for PostgreSQL storage
        pass
        
    async def _store_in_redis(self, data: Dict[str, Any]):
        """Store in Redis cache (L2 tier)"""
        # Implementation for Redis caching
        pass
        
    async def _store_vector_embedding(self, data: Dict[str, Any]):
        """Store vector embedding in Weaviate (L4 tier)"""
        # Implementation for vector storage
        pass

# Factory function for easy orchestrator creation
async def create_orchestrator(config_path: str = None) -> IntegratedOrchestrator:
    """Create and initialize integrated orchestrator"""
    
    orchestrator = IntegratedOrchestrator()
    
    # Load configuration
    if config_path:
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            "cpu_cache": {"max_size": 1024},
            "process_memory": {"max_size": "2GB"},
            "shared_memory": {"redis_url": "redis://localhost:6379"},
            "postgresql": {"url": "postgresql://localhost/orchestra"},
            "weaviate": {"url": "http://localhost:8080"}
        }
    
    await orchestrator.initialize(config)
    return orchestrator

# Usage example
async def example_usage():
    """Example of how to use the integrated orchestrator"""
    
    # Create orchestrator
    orchestrator = await create_orchestrator()
    
    # Example 1: Cherry coordinating a project
    cherry_context = OrchestrationContext(
        requesting_persona="cherry",
        task_type="project_coordination",
        urgency_level=0.6,
        collaborative=True,
        cross_domain_required=["financial_services", "medical_coding"]
    )
    
    cherry_response = await orchestrator.process_request(
        persona_name="cherry",
        query="Help me coordinate a project that involves both PayReady financial integration and ParagonRX medical coding updates",
        context=cherry_context
    )
    
    # Example 2: Sophia handling financial compliance
    sophia_context = OrchestrationContext(
        requesting_persona="sophia",
        task_type="compliance_review",
        urgency_level=0.8,
        technical_complexity=0.9
    )
    
    sophia_response = await orchestrator.process_request(
        persona_name="sophia",
        query="Review the latest PCI DSS compliance requirements for PayReady payment processing",
        context=sophia_context
    )
    
    # Example 3: Karen providing medical coding guidance
    karen_context = OrchestrationContext(
        requesting_persona="karen",
        task_type="medical_coding",
        urgency_level=0.7,
        technical_complexity=0.95
    )
    
    karen_response = await orchestrator.process_request(
        persona_name="karen",
        query="What are the latest ICD-10 coding updates for pharmaceutical prescriptions in ParagonRX?",
        context=karen_context
    )
    
    # Get performance summary
    performance = orchestrator.get_performance_summary()
    
    print("🎯 Example orchestration complete!")
    print(f"📊 Performance: {performance['performance_metrics']}")

if __name__ == "__main__":
    asyncio.run(example_usage()) 