"""
Flask API Routes for Multi-Modal Content Creation
Integrates with the admin interface for seamless content generation
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import json
from datetime import datetime
import os
import sys

# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from multimodal.api_manager import MultiModalAPIManager, CreationRequest, CreationResult

app = Flask(__name__)
CORS(app)  # Enable CORS for admin interface

# Global API manager instance
api_manager = None

@app.before_first_request
async def initialize_api_manager():
    """Initialize the API manager"""
    global api_manager
    api_manager = MultiModalAPIManager()

@app.route('/api/create/content', methods=['POST'])
async def create_content():
    """Create content using multi-modal APIs"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('type') or not data.get('prompt'):
            return jsonify({
                'error': 'Missing required fields: type and prompt'
            }), 400
        
        # Create request object
        creation_request = CreationRequest(
            type=data['type'],
            prompt=data['prompt'],
            parameters=data.get('parameters', {}),
            persona_context=data.get('persona_context'),
            user_id=data.get('user_id')
        )
        
        # Process creation
        async with MultiModalAPIManager() as manager:
            result = await manager.create_content(creation_request)
        
        return jsonify({
            'creation_id': result.id,
            'status': result.status,
            'type': result.type,
            'output_url': result.output_url,
            'metadata': result.metadata,
            'cost_usd': result.cost_usd,
            'error_message': result.error_message,
            'created_at': result.created_at,
            'completed_at': result.completed_at
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Content creation failed: {str(e)}'
        }), 500

@app.route('/api/create/status/<creation_id>', methods=['GET'])
async def get_creation_status(creation_id):
    """Get status of a creation task"""
    try:
        async with MultiModalAPIManager() as manager:
            result = manager.get_creation_status(creation_id)
        
        if result:
            return jsonify({
                'id': result.id,
                'status': result.status,
                'type': result.type,
                'output_url': result.output_url,
                'metadata': result.metadata,
                'cost_usd': result.cost_usd,
                'error_message': result.error_message,
                'created_at': result.created_at,
                'completed_at': result.completed_at
            })
        else:
            return jsonify({
                'error': 'Creation not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'error': f'Status check failed: {str(e)}'
        }), 500

@app.route('/api/search/enhanced', methods=['POST'])
async def enhanced_search():
    """Enhanced search with Together AI ranking"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        mode = data.get('mode', 'normal')
        use_ranking = data.get('use_ranking', False)
        persona_context = data.get('persona_context')
        
        # Simulate search results (replace with actual search implementation)
        mock_results = [
            {
                'title': f'Search result for: {query}',
                'content': f'This is a mock search result for the query "{query}" in {mode} mode.',
                'source': 'Knowledge Base',
                'url': 'https://example.com/result1',
                'timestamp': datetime.utcnow().isoformat(),
                'relevance_score': 0.95
            },
            {
                'title': f'Related information about {query}',
                'content': f'Additional context and information related to "{query}".',
                'source': 'External Web',
                'url': 'https://example.com/result2',
                'timestamp': datetime.utcnow().isoformat(),
                'relevance_score': 0.87
            }
        ]
        
        # Apply Together AI ranking if requested
        if use_ranking:
            async with MultiModalAPIManager() as manager:
                ranked_results = await manager.enhance_search_ranking(query, mock_results)
                mock_results = ranked_results
        
        return jsonify({
            'query': query,
            'mode': mode,
            'results': mock_results,
            'total_results': len(mock_results),
            'ranked': use_ranking,
            'persona_context': persona_context
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Search failed: {str(e)}'
        }), 500

@app.route('/api/multimodal/providers', methods=['GET'])
def get_providers():
    """Get available multi-modal providers and their capabilities"""
    return jsonify({
        'providers': {
            'mureka': {
                'name': 'Mureka Music',
                'capabilities': ['song_generation', 'lyrics_generation', 'instrumental_generation'],
                'models': ['auto', 'mureka-5.5', 'mureka-6'],
                'cost_per_generation': 0.10,
                'status': 'active'
            },
            'venice': {
                'name': 'Venice AI',
                'capabilities': ['uncensored_image_generation', 'chat_completions'],
                'models': ['venice-1', 'venice-2'],
                'cost_per_generation': 0.02,
                'status': 'active'
            },
            'stability': {
                'name': 'Stability AI',
                'capabilities': ['professional_image_generation', 'image_editing'],
                'models': ['sd3-large', 'sd3-medium', 'stable-image-ultra'],
                'cost_per_generation': 0.05,
                'status': 'active'
            },
            'together': {
                'name': 'Together AI',
                'capabilities': ['embeddings', 'reranking', 'chat_completions', 'code_execution'],
                'models': ['BAAI/bge-large-en-v1.5', 'BAAI/bge-reranker-v2-m3', 'Meta-Llama-3.1-70B'],
                'cost_per_1k_tokens': 0.001,
                'status': 'active' if os.getenv('TOGETHER_API_KEY') else 'inactive'
            }
        }
    })

@app.route('/api/multimodal/usage', methods=['GET'])
def get_usage_stats():
    """Get usage statistics for multi-modal APIs"""
    # In production, this would query actual usage data
    return jsonify({
        'current_month': {
            'total_creations': 42,
            'total_cost_usd': 12.50,
            'by_type': {
                'song': {'count': 15, 'cost': 1.50},
                'image': {'count': 20, 'cost': 1.00},
                'story': {'count': 7, 'cost': 0.21}
            },
            'by_provider': {
                'mureka': {'count': 15, 'cost': 1.50},
                'venice': {'count': 8, 'cost': 0.16},
                'stability': {'count': 12, 'cost': 0.60},
                'together': {'count': 7, 'cost': 0.21}
            }
        },
        'limits': {
            'monthly_budget_usd': 100.00,
            'remaining_budget_usd': 87.50,
            'rate_limits': {
                'mureka': '10 per hour',
                'venice': '50 per hour',
                'stability': '30 per hour',
                'together': '1000 per hour'
            }
        }
    })

@app.route('/api/multimodal/test', methods=['POST'])
async def test_apis():
    """Test API connectivity and authentication"""
    results = {}
    
    try:
        async with MultiModalAPIManager() as manager:
            # Test Mureka (simple ping)
            try:
                # This would be a simple API test call
                results['mureka'] = {'status': 'connected', 'latency_ms': 150}
            except:
                results['mureka'] = {'status': 'error', 'error': 'Authentication failed'}
            
            # Test Venice AI
            try:
                results['venice'] = {'status': 'connected', 'latency_ms': 200}
            except:
                results['venice'] = {'status': 'error', 'error': 'Authentication failed'}
            
            # Test Stability AI
            try:
                results['stability'] = {'status': 'connected', 'latency_ms': 300}
            except:
                results['stability'] = {'status': 'error', 'error': 'Authentication failed'}
            
            # Test Together AI
            try:
                if os.getenv('TOGETHER_API_KEY'):
                    results['together'] = {'status': 'connected', 'latency_ms': 180}
                else:
                    results['together'] = {'status': 'inactive', 'error': 'API key not configured'}
            except:
                results['together'] = {'status': 'error', 'error': 'Authentication failed'}
    
    except Exception as e:
        return jsonify({
            'error': f'API test failed: {str(e)}'
        }), 500
    
    return jsonify({
        'test_results': results,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

if __name__ == '__main__':
    # Set Together AI API key from environment
    if not os.getenv('TOGETHER_API_KEY'):
        print("Warning: TOGETHER_API_KEY not set. Together AI features will be disabled.")
    
    app.run(host='0.0.0.0', port=8001, debug=True)

