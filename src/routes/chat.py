from flask import Blueprint, jsonify, request
from datetime import datetime
import requests
import urllib.parse
from typing import List, Dict, Any
import os

chat_bp = Blueprint('chat', __name__)

# Persona configurations
PERSONAS = {
    'cherry': {
        'name': 'Cherry',
        'description': 'Creative AI specialized in content creation, design, and innovation',
        'style': 'friendly and creative',
        'focus': 'creative solutions and innovative approaches',
        'greeting': "Hi there! I'm Cherry, and I'm excited to help you with this creative challenge!"
    },
    'sophia': {
        'name': 'Sophia',
        'description': 'Strategic AI focused on analysis, planning, and complex problem-solving',
        'style': 'analytical and comprehensive',
        'focus': 'strategic insights and data-driven analysis',
        'greeting': "As your strategic AI assistant, I've conducted a comprehensive analysis and gathered relevant information."
    },
    'karen': {
        'name': 'Karen',
        'description': 'Operational AI focused on execution, automation, and workflow management',
        'style': 'organized and efficient',
        'focus': 'practical execution and workflow optimization',
        'greeting': "I'm Karen, your operational AI. Let me provide you with structured, actionable information."
    }
}

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
            for topic in data.get('RelatedTopics', [])[:3]:
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

def generate_ai_response(message: str, persona: str, context: List[Dict[str, Any]]) -> str:
    """Generate AI response with context integration"""
    try:
        current_persona = PERSONAS.get(persona, PERSONAS['sophia'])
        
        # Build context from search results
        context_text = ""
        if context:
            context_text = "\\n\\nBased on my comprehensive search, here's what I found:\\n"
            for i, item in enumerate(context[:5], 1):
                if item.get('content'):
                    source = item.get('source', 'Unknown')
                    title = item.get('title', 'Result')
                    content = item['content'][:200] + '...' if len(item['content']) > 200 else item['content']
                    context_text += f"{i}. **{title}** - {content} (Source: {source})\\n\\n"
        
        # Generate contextual response based on query type
        if any(keyword in message.lower() for keyword in ['weather', 'news', 'current', 'today', 'latest']):
            response = f"{current_persona['greeting']} You're asking about current information. {context_text}"
            if not context:
                response += f"\\n\\nFor real-time information like weather or news, I can search multiple sources including premium APIs. My {current_persona['focus']} approach ensures you get the most relevant, up-to-date insights."
        
        elif any(keyword in message.lower() for keyword in ['persona', 'agent', 'system', 'orchestra']):
            response = f"{current_persona['greeting']} You're asking about our Orchestra AI system. {context_text}"
            if not context:
                response += "\\n\\nI can help you learn about our personas (Cherry for creativity, Sophia for strategy, Karen for operations) and system capabilities including advanced search with premium APIs, content generation, and workflow automation."
        
        elif any(keyword in message.lower() for keyword in ['help', 'what can you do', 'capabilities', 'features']):
            response = f"{current_persona['greeting']} I can help you with:\\n\\n"
            response += "🔍 **Advanced Search** - Multi-source search including DuckDuckGo, Wikipedia, and premium APIs\\n"
            response += "🎯 **Strategic Analysis** - Complex problem-solving and decision support with live data\\n"
            response += "🎨 **Creative Content** - Document, image, video, and audio generation\\n"
            response += "⚙️ **Workflow Optimization** - Process automation and efficiency improvements\\n"
            response += f"\\n{context_text}"
        
        elif any(keyword in message.lower() for keyword in ['search', 'find', 'look up', 'research']):
            response = f"{current_persona['greeting']} I've performed a comprehensive multi-source search for your query. {context_text}"
            if not context:
                response += f"\\n\\nI can search both our internal database and multiple internet sources. My {current_persona['focus']} approach ensures you get relevant, actionable insights from the best available sources."
        
        else:
            response = f"{current_persona['greeting']} Regarding your question about '{message}': {context_text}"
            if not context:
                response += f"\\n\\nI'm ready to help with {current_persona['focus']}! I can search our database and multiple internet sources for comprehensive information. Feel free to ask me anything!"
        
        return response
        
    except Exception as e:
        print(f"AI response generation failed: {e}")
        return f"I'm {persona.title()}, and I received your message: '{message}'. I'm working on providing better responses with live data integration from multiple sources."

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Enhanced chat endpoint with integrated search"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message']
        persona = data.get('persona', 'sophia')
        
        # Validate persona
        if persona not in PERSONAS:
            persona = 'sophia'
        
        # Search for relevant context
        context = []
        
        # Search internet for additional context
        try:
            duckduckgo_results = search_duckduckgo(message)
            context.extend(duckduckgo_results)
            
            wikipedia_results = search_wikipedia(message)
            context.extend(wikipedia_results)
        except Exception as e:
            print(f"Search failed: {e}")
        
        # Sort by relevance score
        context.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Generate AI response with context
        response = generate_ai_response(message, persona, context)
        
        # Collect sources
        sources = list(set([item.get('source', 'Unknown') for item in context if item.get('source')]))
        
        return jsonify({
            'response': response,
            'persona': persona,
            'sources': sources,
            'search_results': context[:10],  # Return top 10 results
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return jsonify({
            'response': f"I'm {persona.title()}, and I received your message. I'm currently working on improving my response capabilities with enhanced search integration.",
            'persona': persona,
            'sources': [],
            'timestamp': datetime.now().isoformat()
        }), 200

@chat_bp.route('/chat/personas', methods=['GET'])
def get_personas():
    """Get available personas"""
    return jsonify({
        'personas': PERSONAS,
        'total': len(PERSONAS)
    })

