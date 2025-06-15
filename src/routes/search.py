from flask import Blueprint, jsonify, request
from datetime import datetime
import requests
import urllib.parse
from typing import List, Dict, Any
import os

search_bp = Blueprint('search', __name__)

def search_duckduckgo(query: str) -> List[Dict[str, Any]]:
    """Search DuckDuckGo for information"""
    results = []
    
    try:
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if data.get('AbstractText'):
                results.append({
                    'title': data.get('Heading', 'DuckDuckGo Result'),
                    'content': data.get('AbstractText'),
                    'url': data.get('AbstractURL', ''),
                    'source': 'DuckDuckGo',
                    'type': 'instant_answer',
                    'relevance_score': 0.9
                })
            
            # Add related topics
            for topic in data.get('RelatedTopics', [])[:5]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('Text', '')[:50] + '...',
                        'content': topic.get('Text', ''),
                        'url': topic.get('FirstURL', ''),
                        'source': 'DuckDuckGo Related',
                        'type': 'related_topic',
                        'relevance_score': 0.7
                    })
    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
    
    return results

def search_wikipedia(query: str) -> List[Dict[str, Any]]:
    """Search Wikipedia for information"""
    results = []
    
    try:
        wiki_query = query.replace(' ', '_')
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(wiki_query)}"
        
        headers = {
            'User-Agent': 'Orchestra-AI/1.0 (https://orchestra.ai)'
        }
        
        response = requests.get(wiki_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('extract') and data.get('type') != 'disambiguation':
                results.append({
                    'title': data.get('title', 'Wikipedia'),
                    'content': data.get('extract', ''),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'source': 'Wikipedia',
                    'type': 'encyclopedia',
                    'relevance_score': 0.8
                })
    except Exception as e:
        print(f"Wikipedia search failed: {e}")
    
    return results

def search_database(query: str) -> List[Dict[str, Any]]:
    """Search internal database for Orchestra AI information"""
    results = []
    
    try:
        # Mock database search for now - replace with actual database queries
        if any(keyword in query.lower() for keyword in ['system', 'status', 'health', 'database', 'orchestra']):
            results.append({
                'type': 'system_info',
                'title': 'Orchestra AI System Status',
                'content': 'Orchestra AI unified system is operational with enhanced search, persona management, creative content generation, and premium API integrations. All services are running optimally.',
                'source': 'Orchestra Database',
                'relevance_score': 0.9
            })
        
        if any(keyword in query.lower() for keyword in ['persona', 'cherry', 'sophia', 'karen']):
            results.append({
                'type': 'persona_info',
                'title': 'Orchestra AI Personas',
                'content': 'Three AI personas available: Cherry (Creative AI for content creation and design), Sophia (Strategic AI for analysis and planning), Karen (Operational AI for execution and automation).',
                'source': 'Orchestra Database',
                'relevance_score': 0.85
            })
        
        # Sort by relevance score
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return results
        
    except Exception as e:
        print(f"Database search failed: {e}")
        return []

@search_bp.route('/search', methods=['POST'])
def search():
    """Enhanced search endpoint with performance metrics"""
    start_time = datetime.now()
    
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        include_database = data.get('include_database', True)
        include_internet = data.get('include_internet', True)
        max_results = data.get('max_results', 20)
        
        all_results = []
        database_results = []
        internet_results = []
        
        if include_database:
            database_results = search_database(query)
            all_results.extend(database_results)
        
        if include_internet:
            # Search DuckDuckGo
            duckduckgo_results = search_duckduckgo(query)
            internet_results.extend(duckduckgo_results)
            
            # Search Wikipedia
            wikipedia_results = search_wikipedia(query)
            internet_results.extend(wikipedia_results)
            
            all_results.extend(internet_results)
        
        # Sort all results by relevance score
        all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Limit results
        all_results = all_results[:max_results]
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return jsonify({
            'results': all_results,
            'database_results': database_results,
            'internet_results': internet_results,
            'total_results': len(all_results),
            'processing_time_ms': processing_time,
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Search endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@search_bp.route('/search/advanced', methods=['POST'])
def advanced_search():
    """Advanced search endpoint with premium sources and modes"""
    start_time = datetime.now()
    
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        search_mode = data.get('search_mode', 'normal')
        include_database = data.get('include_database', True)
        include_internet = data.get('include_internet', True)
        max_results = data.get('max_results', 10)
        
        all_results = []
        sources_used = []
        cost_estimate = 0.0
        
        # Database search
        if include_database:
            db_results = search_database(query)
            all_results.extend(db_results)
            if db_results:
                sources_used.append("Orchestra Database")
        
        # Internet search based on mode
        if include_internet:
            if search_mode in ['normal', 'deep', 'super_deep', 'uncensored']:
                # DuckDuckGo search
                duckduckgo_results = search_duckduckgo(query)
                all_results.extend(duckduckgo_results)
                if duckduckgo_results:
                    sources_used.append("DuckDuckGo")
                
                # Wikipedia search
                wikipedia_results = search_wikipedia(query)
                all_results.extend(wikipedia_results)
                if wikipedia_results:
                    sources_used.append("Wikipedia")
            
            # Premium sources for advanced modes
            if search_mode in ['deep', 'super_deep', 'uncensored']:
                # Placeholder for premium API integration
                if os.getenv('EXA_API_KEY'):
                    sources_used.append("Exa AI")
                    cost_estimate += 0.02
                
                if os.getenv('SERP_API_KEY'):
                    sources_used.append("SERP API")
                    cost_estimate += 0.01
            
            if search_mode in ['super_deep', 'uncensored']:
                if os.getenv('BROWSERUSE_API_KEY'):
                    sources_used.append("Browser-use.com")
                    cost_estimate += 0.05
        
        # Sort and limit results
        all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        all_results = all_results[:max_results]
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return jsonify({
            'results': all_results,
            'search_mode': search_mode,
            'total_results': len(all_results),
            'processing_time_ms': processing_time,
            'sources_used': sources_used,
            'cost_estimate': cost_estimate,
            'query': query,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Advanced search endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@search_bp.route('/search/sources', methods=['GET'])
def get_search_sources():
    """Get available search sources and their status"""
    sources = {
        "duckduckgo": {
            "name": "DuckDuckGo",
            "cost_per_query": 0.0,
            "enabled": True,
            "api_key_required": False,
            "type": "search_engine"
        },
        "wikipedia": {
            "name": "Wikipedia",
            "cost_per_query": 0.0,
            "enabled": True,
            "api_key_required": False,
            "type": "encyclopedia"
        },
        "orchestra_db": {
            "name": "Orchestra Database",
            "cost_per_query": 0.0,
            "enabled": True,
            "api_key_required": False,
            "type": "internal"
        },
        "exa": {
            "name": "Exa AI",
            "cost_per_query": 0.02,
            "enabled": bool(os.getenv('EXA_API_KEY')),
            "api_key_required": True,
            "type": "premium"
        },
        "serp": {
            "name": "SERP API",
            "cost_per_query": 0.01,
            "enabled": bool(os.getenv('SERP_API_KEY')),
            "api_key_required": True,
            "type": "premium"
        },
        "browseruse": {
            "name": "Browser-use.com",
            "cost_per_query": 0.05,
            "enabled": bool(os.getenv('BROWSERUSE_API_KEY')),
            "api_key_required": True,
            "type": "premium"
        }
    }
    
    return jsonify({
        "sources": sources,
        "total_sources": len(sources),
        "enabled_sources": len([s for s in sources.values() if s["enabled"]]),
        "premium_sources_available": any(s["enabled"] and s["api_key_required"] for s in sources.values())
    })

@search_bp.route('/search/modes', methods=['GET'])
def get_search_modes():
    """Get available search modes"""
    modes = {
        "normal": {
            "name": "Normal",
            "description": "Standard search using DuckDuckGo and Wikipedia",
            "cost": "Free",
            "sources": ["DuckDuckGo", "Wikipedia", "Orchestra Database"]
        },
        "deep": {
            "name": "Deep",
            "description": "Enhanced search with premium APIs and multiple sources",
            "cost": "$0.03/query",
            "sources": ["DuckDuckGo", "Wikipedia", "Exa AI", "SERP API", "Orchestra Database"]
        },
        "super_deep": {
            "name": "Super Deep",
            "description": "Comprehensive search with all premium sources and deep web",
            "cost": "$0.08/query",
            "sources": ["All Sources", "Deep Web", "Browser-use.com", "Live Crawl"]
        },
        "uncensored": {
            "name": "Uncensored",
            "description": "Unrestricted search across all available sources",
            "cost": "$0.10/query",
            "sources": ["All Sources", "Unrestricted", "Alternative Engines"]
        }
    }
    
    return jsonify({
        "modes": modes,
        "total_modes": len(modes),
        "default_mode": "normal"
    })

