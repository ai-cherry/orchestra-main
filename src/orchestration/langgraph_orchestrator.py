"""
Orchestra AI - LangGraph Orchestrator
Implements dynamic, flexible, and deeply contextual AI orchestration
"""

import os
import asyncio
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import json
import logging

from langgraph.graph import Graph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import redis.asyncio as redis
import pinecone
from pinecone import Pinecone, ServerlessSpec

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type definitions for state management
class SearchState(TypedDict):
    query: str
    persona: str
    search_mode: str
    blend_ratio: Dict[str, float]
    context: Dict[str, Any]
    search_results: Dict[str, List[Dict]]
    blended_results: List[Dict]
    summary: str
    response: str

class OrchestraOrchestrator:
    """Main orchestrator using LangGraph for dynamic AI coordination"""
    
    def __init__(self):
        # Initialize LLM - use OpenAI directly for now
        # TODO: Switch to OpenRouter when API key is available
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4-turbo-preview",
            temperature=0.7
        )
        
        # Initialize Redis for caching
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        
        # Initialize Pinecone for vector storage (if API key available)
        pinecone_key = os.getenv("PINECONE_API_KEY")
        if pinecone_key:
            pc = Pinecone(api_key=pinecone_key)
            if "orchestra-context" not in pc.list_indexes().names():
                pc.create_index(
                    name="orchestra-context",
                    dimension=1536,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-west-2"
                    )
                )
            self.pinecone_index = pc.Index("orchestra-context")
        else:
            logger.warning("Pinecone API key not found - vector storage disabled")
            self.pinecone_index = None
        
        # Build the orchestration graph
        self.graph = self._build_graph()
        
        # Persona configurations with domain prompts
        self.persona_configs = self._load_persona_configs()
    
    def _load_persona_configs(self) -> Dict[str, Dict]:
        """Load persona configurations with domain-specific prompts"""
        return {
            "cherry": {
                "base_prompt": "You are Cherry, a creative and personal AI assistant focused on helping with personal interests and creative exploration.",
                "domain_context": """
                Focus on creative, personal, and entertainment topics.
                Be open-minded and supportive of unconventional ideas.
                When searching, prioritize diverse perspectives and creative solutions.
                User preferences: {user_preferences}
                """,
                "search_weights": {
                    "creativity": 0.8,
                    "diversity": 0.9,
                    "accuracy": 0.6
                },
                "invisible_prompts": [
                    "Consider alternative and creative interpretations",
                    "Include diverse viewpoints and unconventional sources",
                    "Prioritize user's personal interests and creative goals"
                ]
            },
            "sophia": {
                "base_prompt": "You are Sophia, a strategic business AI assistant specializing in property technology and financial services.",
                "domain_context": """
                Focus on business intelligence, particularly in:
                - Apartment rental and property management
                - Property technology (PropTech)
                - Debt collection and payment systems
                - Financial technology solutions
                
                Pay Ready clients: {pay_ready_clients}
                Pay Ready competitors: {pay_ready_competitors}
                Industry keywords: {industry_keywords}
                """,
                "search_weights": {
                    "business_relevance": 0.9,
                    "financial_accuracy": 0.95,
                    "competitive_intelligence": 0.8
                },
                "invisible_prompts": [
                    "Consider business implications and ROI",
                    "Include competitive analysis when relevant",
                    "Focus on practical, implementable solutions",
                    "Highlight financial and operational benefits"
                ]
            },
            "karen": {
                "base_prompt": "You are Karen, an operational AI assistant specializing in healthcare and clinical research.",
                "domain_context": """
                Focus on clinical and healthcare operations:
                - Clinical trials and pharmaceutical research
                - Drug approvals and regulatory compliance
                - Healthcare operations and efficiency
                - Medical accuracy and patient safety
                
                Tracked trials: {tracked_trials}
                Specialties: {specialties}
                Regulatory focus areas: {regulatory_areas}
                """,
                "search_weights": {
                    "clinical_accuracy": 0.95,
                    "regulatory_compliance": 0.9,
                    "operational_efficiency": 0.85
                },
                "invisible_prompts": [
                    "Prioritize clinical accuracy and patient safety",
                    "Include regulatory compliance considerations",
                    "Focus on evidence-based recommendations",
                    "Consider operational efficiency and scalability"
                ]
            }
        }
    
    def _build_graph(self) -> Graph:
        """Build the LangGraph orchestration graph"""
        workflow = Graph()
        
        # Define nodes
        workflow.add_node("route_persona", self.route_by_persona)
        workflow.add_node("enhance_query", self.enhance_query)
        workflow.add_node("execute_search", self.execute_parallel_search)
        workflow.add_node("blend_results", self.blend_search_results)
        workflow.add_node("generate_summary", self.generate_ai_summary)
        workflow.add_node("manage_context", self.manage_conversation_context)
        workflow.add_node("generate_response", self.generate_final_response)
        
        # Define edges
        workflow.add_edge("route_persona", "enhance_query")
        workflow.add_edge("enhance_query", "execute_search")
        workflow.add_edge("execute_search", "blend_results")
        workflow.add_edge("blend_results", "generate_summary")
        workflow.add_edge("generate_summary", "manage_context")
        workflow.add_edge("manage_context", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Set entry point
        workflow.set_entry_point("route_persona")
        
        return workflow.compile()
    
    async def route_by_persona(self, state: SearchState) -> SearchState:
        """Route request based on active persona with domain context"""
        persona = state["persona"]
        config = self.persona_configs.get(persona, self.persona_configs["cherry"])
        
        # Load user-specific context
        user_context = await self._load_user_context(state.get("user_id"), persona)
        
        # Format domain context with actual data
        domain_context = config["domain_context"].format(
            user_preferences=user_context.get("preferences", []),
            pay_ready_clients=user_context.get("pay_ready_clients", []),
            pay_ready_competitors=user_context.get("pay_ready_competitors", []),
            industry_keywords=user_context.get("industry_keywords", []),
            tracked_trials=user_context.get("tracked_trials", []),
            specialties=user_context.get("specialties", []),
            regulatory_areas=user_context.get("regulatory_areas", [])
        )
        
        # Add invisible prompts to context
        state["context"]["persona_config"] = config
        state["context"]["domain_context"] = domain_context
        state["context"]["invisible_prompts"] = config["invisible_prompts"]
        
        logger.info(f"Routed to persona: {persona}")
        return state
    
    async def enhance_query(self, state: SearchState) -> SearchState:
        """Enhance query based on persona and domain context"""
        query = state["query"]
        persona_config = state["context"]["persona_config"]
        
        # Create enhancement prompt
        enhance_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=persona_config["base_prompt"]),
            SystemMessage(content=state["context"]["domain_context"]),
            HumanMessage(content=f"""
            Enhance this search query for better results:
            Original query: {query}
            
            Generate:
            1. An expanded query with synonyms and related terms
            2. A domain-focused query for this persona's specialty
            3. Alternative phrasings to capture different perspectives
            
            Keep each enhanced query concise and focused.
            """)
        ])
        
        # Get enhanced queries
        response = await self.llm.ainvoke(enhance_prompt.format_messages())
        enhanced_queries = self._parse_enhanced_queries(response.content)
        
        state["context"]["enhanced_queries"] = enhanced_queries
        logger.info(f"Enhanced query: {query} -> {enhanced_queries}")
        
        return state
    
    async def execute_parallel_search(self, state: SearchState) -> SearchState:
        """Execute searches in parallel based on search mode"""
        from ..search.unified_search_manager import UnifiedSearchManager
        
        search_manager = UnifiedSearchManager()
        search_mode = state["search_mode"]
        queries = [state["query"]] + state["context"]["enhanced_queries"]
        
        # Execute parallel searches
        search_tasks = []
        for query in queries[:3]:  # Limit to top 3 queries
            task = search_manager.execute_search(
                query=query,
                mode=search_mode,
                persona=state["persona"],
                blend_ratio=state["blend_ratio"]
            )
            search_tasks.append(task)
        
        # Wait for all searches to complete
        results = await asyncio.gather(*search_tasks)
        
        # Aggregate results by source
        aggregated_results = {}
        for result_set in results:
            for source, items in result_set.items():
                if source not in aggregated_results:
                    aggregated_results[source] = []
                aggregated_results[source].extend(items)
        
        state["search_results"] = aggregated_results
        logger.info(f"Executed {len(search_tasks)} parallel searches")
        
        return state
    
    async def blend_search_results(self, state: SearchState) -> SearchState:
        """Intelligently blend results from multiple sources"""
        from ..search.result_blender import SearchResultBlender
        
        blender = SearchResultBlender(self.redis_client, self.pinecone_index)
        
        blended = await blender.blend_results(
            results_by_source=state["search_results"],
            query=state["query"],
            persona=state["persona"],
            blend_ratio=state["blend_ratio"],
            persona_weights=state["context"]["persona_config"]["search_weights"]
        )
        
        state["blended_results"] = blended["results"]
        state["context"]["blend_metadata"] = {
            "sources_used": blended["sources_used"],
            "blend_ratio_applied": blended["blend_ratio_applied"],
            "deduplication_count": blended.get("deduplication_count", 0)
        }
        
        logger.info(f"Blended {len(state['blended_results'])} results from {len(blended['sources_used'])} sources")
        
        return state
    
    async def generate_ai_summary(self, state: SearchState) -> SearchState:
        """Generate AI summary of search results"""
        results = state["blended_results"][:10]  # Top 10 results
        persona_config = state["context"]["persona_config"]
        
        # Create summary prompt with invisible prompts
        invisible_context = "\n".join(persona_config["invisible_prompts"])
        
        summary_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=persona_config["base_prompt"]),
            SystemMessage(content=f"Additional context: {invisible_context}"),
            HumanMessage(content=f"""
            Summarize these search results for the query: "{state['query']}"
            
            Results:
            {json.dumps(results, indent=2)}
            
            Create a comprehensive summary that:
            1. Highlights key findings and insights
            2. Notes any contradictions or consensus
            3. Provides actionable recommendations
            4. Maintains the persona's domain focus
            
            Format as a clear, structured summary.
            """)
        ])
        
        response = await self.llm.ainvoke(summary_prompt.format_messages())
        state["summary"] = response.content
        
        logger.info("Generated AI summary of search results")
        return state
    
    async def manage_conversation_context(self, state: SearchState) -> SearchState:
        """Manage conversation context with large context windows"""
        session_id = state.get("session_id", "default")
        
        # Create context entry
        context_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": state["query"],
            "persona": state["persona"],
            "summary": state["summary"],
            "search_mode": state["search_mode"],
            "results_count": len(state["blended_results"])
        }
        
        # Store in Redis for fast access
        context_key = f"context:{session_id}"
        await self.redis_client.lpush(context_key, json.dumps(context_entry))
        await self.redis_client.ltrim(context_key, 0, 99)  # Keep last 100 entries
        await self.redis_client.expire(context_key, 3600)  # 1 hour TTL
        
        # Store embedding in Pinecone for semantic retrieval
        embedding = await self._generate_embedding(state["summary"])
        self.pinecone_index.upsert(
            vectors=[{
                "id": f"{session_id}:{datetime.utcnow().timestamp()}",
                "values": embedding,
                "metadata": {
                    "session_id": session_id,
                    "persona": state["persona"],
                    "query": state["query"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }]
        )
        
        # Load recent context
        recent_context = await self._load_recent_context(session_id)
        state["context"]["conversation_history"] = recent_context
        
        logger.info(f"Managed context for session: {session_id}")
        return state
    
    async def generate_final_response(self, state: SearchState) -> SearchState:
        """Generate final response incorporating all context"""
        persona_config = state["context"]["persona_config"]
        
        response_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=persona_config["base_prompt"]),
            SystemMessage(content=state["context"]["domain_context"]),
            HumanMessage(content=f"""
            Query: {state['query']}
            
            Search Summary:
            {state['summary']}
            
            Recent Conversation Context:
            {json.dumps(state['context'].get('conversation_history', []), indent=2)}
            
            Generate a helpful response that:
            1. Directly addresses the user's query
            2. Incorporates the search findings
            3. Maintains conversational continuity
            4. Reflects the persona's expertise and style
            5. Provides clear next steps or recommendations
            """)
        ])
        
        response = await self.llm.ainvoke(response_prompt.format_messages())
        state["response"] = response.content
        
        logger.info("Generated final response")
        return state
    
    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the orchestration workflow"""
        # Initialize state
        state: SearchState = {
            "query": request["query"],
            "persona": request["persona"],
            "search_mode": request.get("search_mode", "normal"),
            "blend_ratio": request.get("blend_ratio", {"database": 0.5, "web": 0.5}),
            "context": {
                "user_id": request.get("user_id"),
                "session_id": request.get("session_id", "default")
            },
            "search_results": {},
            "blended_results": [],
            "summary": "",
            "response": ""
        }
        
        # Execute workflow
        final_state = await self.graph.ainvoke(state)
        
        # Return structured response
        return {
            "response": final_state["response"],
            "summary": final_state["summary"],
            "search_results": final_state["blended_results"][:10],
            "metadata": {
                "persona": final_state["persona"],
                "search_mode": final_state["search_mode"],
                "sources_used": final_state["context"]["blend_metadata"]["sources_used"],
                "processing_time": datetime.utcnow().isoformat()
            }
        }
    
    # Helper methods
    async def _load_user_context(self, user_id: Optional[str], persona: str) -> Dict[str, Any]:
        """Load user-specific context from database"""
        if not user_id:
            return {}
        
        # This would load from database in production
        # For now, return mock data
        return {
            "preferences": ["technology", "innovation"],
            "pay_ready_clients": ["ABC Properties", "XYZ Management"],
            "pay_ready_competitors": ["RentTech", "PropPay"],
            "industry_keywords": ["PropTech", "payment automation"],
            "tracked_trials": ["NCT12345", "NCT67890"],
            "specialties": ["oncology", "cardiology"],
            "regulatory_areas": ["FDA approvals", "clinical compliance"]
        }
    
    async def _load_recent_context(self, session_id: str, limit: int = 5) -> List[Dict]:
        """Load recent conversation context from Redis"""
        context_key = f"context:{session_id}"
        recent_entries = await self.redis_client.lrange(context_key, 0, limit - 1)
        
        return [json.loads(entry) for entry in recent_entries]
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding for vector storage"""
        # This would use OpenAI embeddings API in production
        # For now, return mock embedding
        import random
        return [random.random() for _ in range(1536)]
    
    def _parse_enhanced_queries(self, response: str) -> List[str]:
        """Parse enhanced queries from LLM response"""
        # Simple parsing - in production would be more robust
        lines = response.strip().split('\n')
        queries = []
        for line in lines:
            if line.strip() and not line.startswith('#'):
                queries.append(line.strip())
        return queries[:3]  # Return top 3 