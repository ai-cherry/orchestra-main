"""
Orchestra AI - Chat v2 API Routes (CLEANED)
Integrates with LangGraph orchestrator for enhanced search and chat
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import asyncio
import logging

# Fixed imports - removed non-existent modules
try:
    from ..orchestration.langgraph_orchestrator import OrchestraOrchestrator
except ImportError:
    # Fallback for development
    OrchestraOrchestrator = None

logger = logging.getLogger(__name__)

chat_v2_bp = Blueprint('chat_v2', __name__)

# Global orchestrator instance
orchestrator = None

def get_orchestrator():
    """Get or create orchestrator instance"""
    global orchestrator
    if orchestrator is None and OrchestraOrchestrator:
        orchestrator = OrchestraOrchestrator()
    return orchestrator

@chat_v2_bp.route('/api/chat/v2', methods=['POST'])
def chat_with_search():
    """
    Enhanced chat endpoint with integrated search capabilities
    
    Request body:
    {
        "message": "user query",
        "persona": "cherry|sophia|karen",
        "search_mode": "normal|deep|deeper|uncensored",
        "blend_ratio": {"database": 0.5, "web": 0.5},  // optional
        "session_id": "session_123"  // optional
    }
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        persona = data.get('persona', 'cherry')
        search_mode = data.get('search_mode', 'normal')
        blend_ratio = data.get('blend_ratio')
        session_id = data.get('session_id', 'default')
        
        # Validate persona
        if persona not in ['cherry', 'sophia', 'karen']:
            return jsonify({'error': 'Invalid persona'}), 400
        
        # Validate search mode
        valid_modes = ['normal', 'deep', 'deeper']
        if persona == 'cherry':
            valid_modes.append('uncensored')
        
        if search_mode not in valid_modes:
            return jsonify({'error': f'Invalid search mode for {persona}'}), 400
        
        # Get orchestrator
        orch = get_orchestrator()
        
        if not orch:
            # Fallback response when orchestrator is not available
            return jsonify({
                'response': f"I'm {persona}, and I understand you're asking about: {message}. The advanced orchestration system is currently being set up. Please try the basic chat endpoint at /api/chat for now.",
                'summary': 'Orchestrator not available',
                'search_results': [],
                'sources': [],
                'metadata': {'fallback': True},
                'session_id': session_id
            }), 200
        
        # Execute orchestration
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(orch.execute({
            'query': message,
            'persona': persona,
            'search_mode': search_mode,
            'blend_ratio': blend_ratio,
            'session_id': session_id,
            'user_id': request.headers.get('X-User-ID')  # Optional user ID
        }))
        
        # Format response
        response = {
            'response': result['response'],
            'summary': result.get('summary', ''),
            'search_results': result.get('search_results', []),
            'sources': [r['source'] for r in result.get('search_results', [])[:5]],
            'metadata': result.get('metadata', {}),
            'session_id': session_id
        }
        
        logger.info(f"Chat v2 response generated for {persona} in {search_mode} mode")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Chat v2 error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'An error occurred processing your request',
            'details': str(e) if request.headers.get('X-Debug') else None
        }), 500

@chat_v2_bp.route('/api/search/v2', methods=['POST'])
def unified_search():
    """
    Direct search endpoint for advanced search interface
    
    Request body:
    {
        "query": "search query",
        "persona": "cherry|sophia|karen",
        "search_mode": "normal|deep|deeper|uncensored",
        "blend_ratio": {"database": 0.5, "web": 0.5},
        "filters": {...}  // optional filters
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        persona = data.get('persona', 'cherry')
        search_mode = data.get('search_mode', 'normal')
        blend_ratio = data.get('blend_ratio')
        filters = data.get('filters', {})
        
        # Get orchestrator
        orch = get_orchestrator()
        
        if not orch:
            # Fallback search response
            return jsonify({
                'query': query,
                'total_results': 0,
                'results': [],
                'summary': 'Advanced search system is being set up. Please use basic search for now.',
                'sources_used': [],
                'search_mode': search_mode,
                'blend_ratio_applied': blend_ratio or {'database': 0.5, 'web': 0.5},
                'processing_time_ms': 0,
                'fallback': True
            }), 200
        
        # Execute search only (no chat response)
        try:
            from ..search.unified_search_manager import UnifiedSearchManager
            search_manager = UnifiedSearchManager()
        except ImportError:
            return jsonify({'error': 'Search manager not available'}), 503
        
        # Execute search
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(search_manager.execute_search(
            query=query,
            mode=search_mode,
            persona=persona,
            blend_ratio=blend_ratio,
            max_results=50
        ))
        
        # Blend results
        try:
            from ..search.result_blender import SearchResultBlender
            blender = SearchResultBlender(orch.redis_client, orch.pinecone_index)
        except ImportError:
            # Simple fallback blending
            blended = {
                'results': results.get('web', [])[:20] if isinstance(results, dict) else [],
                'summary': f'Found results for: {query}',
                'sources_used': ['fallback'],
                'blend_ratio_applied': blend_ratio or {'database': 0.5, 'web': 0.5}
            }
        else:
            blended = loop.run_until_complete(blender.blend_results(
                results_by_source=results,
                query=query,
                persona=persona,
                blend_ratio=blend_ratio or {'database': 0.5, 'web': 0.5}
            ))
        
        response = {
            'query': query,
            'total_results': len(blended['results']),
            'results': blended['results'][:20],  # Top 20 results
            'summary': blended.get('summary', ''),
            'sources_used': blended['sources_used'],
            'search_mode': search_mode,
            'blend_ratio_applied': blended['blend_ratio_applied'],
            'processing_time_ms': 0  # TODO: Add timing
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Search v2 error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Search failed',
            'details': str(e) if request.headers.get('X-Debug') else None
        }), 500

@chat_v2_bp.route('/api/search/modes', methods=['GET'])
def get_search_modes():
    """Get available search modes and their descriptions"""
    modes = {
        'normal': {
            'name': 'Normal',
            'description': 'Quick search using database and web',
            'max_time': 5,
            'providers': ['database', 'duckduckgo']
        },
        'deep': {
            'name': 'Deep Search',
            'description': 'Comprehensive search with multiple sources',
            'max_time': 15,
            'providers': ['database', 'duckduckgo', 'exa_ai', 'serp']
        },
        'deeper': {
            'name': 'Deeper Search',
            'description': 'Exhaustive search including web scraping',
            'max_time': 30,
            'providers': ['database', 'exa_ai', 'serp', 'apify', 'zenrows']
        },
        'uncensored': {
            'name': 'Uncensored',
            'description': 'Unfiltered search results (Cherry only)',
            'max_time': 20,
            'providers': ['venice_ai', 'database'],
            'persona_restricted': ['cherry']
        }
    }
    
    return jsonify(modes), 200

@chat_v2_bp.route('/api/chat/context/<session_id>', methods=['GET'])
def get_chat_context(session_id):
    """Get conversation context for a session"""
    try:
        orch = get_orchestrator()
        
        if not orch:
            return jsonify({
                'session_id': session_id,
                'context': [],
                'message_count': 0,
                'note': 'Context storage not available - orchestrator not initialized'
            }), 200
        
        # Load context from Redis
        context_key = f"context:{session_id}"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        context_data = loop.run_until_complete(orch.redis_client.lrange(context_key, 0, -1))
        
        context = []
        for entry in context_data:
            import json
            context.append(json.loads(entry))
        
        return jsonify({
            'session_id': session_id,
            'context': context,
            'message_count': len(context)
        }), 200
        
    except Exception as e:
        logger.error(f"Context retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve context'}), 500

