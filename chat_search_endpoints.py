# Orchestra AI Chat and Search Endpoints
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests
import psycopg2
from typing import List, Dict, Any
import os
import json

# Request models
class ChatRequest(BaseModel):
    message: str
    persona: str = "sophia"

class SearchRequest(BaseModel):
    query: str
    include_database: bool = True
    include_internet: bool = True

# Response models
class ChatResponse(BaseModel):
    response: str
    persona: str
    sources: List[str] = []

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    database_results: List[Dict[str, Any]] = []
    internet_results: List[Dict[str, Any]] = []

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="orchestra_prod",
            user="orchestra",
            password="Orchestra_Prod_2025_Secure"
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

# Internet search function
def search_internet(query: str) -> List[Dict[str, Any]]:
    """Search the internet using a search API"""
    try:
        # Using DuckDuckGo instant answer API as a simple example
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        results = []
        if data.get('AbstractText'):
            results.append({
                'title': data.get('Heading', 'Search Result'),
                'content': data.get('AbstractText'),
                'url': data.get('AbstractURL', ''),
                'source': 'DuckDuckGo'
            })
        
        # Add related topics
        for topic in data.get('RelatedTopics', [])[:3]:
            if isinstance(topic, dict) and topic.get('Text'):
                results.append({
                    'title': topic.get('Text', '')[:50] + '...',
                    'content': topic.get('Text', ''),
                    'url': topic.get('FirstURL', ''),
                    'source': 'DuckDuckGo Related'
                })
        
        return results
    except Exception as e:
        print(f"Internet search failed: {e}")
        return []

# Database search function
def search_database(query: str) -> List[Dict[str, Any]]:
    """Search the database for relevant information"""
    try:
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor()
        results = []
        
        # Search personas
        cursor.execute("""
            SELECT name, description, persona_type 
            FROM orchestra.personas 
            WHERE description ILIKE %s OR name ILIKE %s
        """, (f'%{query}%', f'%{query}%'))
        
        for row in cursor.fetchall():
            results.append({
                'type': 'persona',
                'name': row[0],
                'description': row[1],
                'persona_type': row[2],
                'source': 'Database'
            })
        
        # Search users (if table exists)
        try:
            cursor.execute("SELECT COUNT(*) FROM orchestra.users")
            user_count = cursor.fetchone()[0]
            if 'user' in query.lower() or 'count' in query.lower():
                results.append({
                    'type': 'user_count',
                    'count': user_count,
                    'description': f'Total users in database: {user_count}',
                    'source': 'Database'
                })
        except:
            pass
        
        cursor.close()
        conn.close()
        return results
        
    except Exception as e:
        print(f"Database search failed: {e}")
        return []

# AI chat function
def generate_ai_response(message: str, persona: str, context: List[Dict[str, Any]]) -> str:
    """Generate AI response using OpenAI"""
    try:
        # Set up OpenAI (you'll need to add your API key)
        openai.api_key = os.getenv('OPENAI_API_KEY', 'demo_key')
        
        # Build context from search results
        context_text = ""
        if context:
            context_text = "\\n\\nRelevant information:\\n"
            for item in context:
                if item.get('content'):
                    context_text += f"- {item['content']}\\n"
                elif item.get('description'):
                    context_text += f"- {item['description']}\\n"
        
        # Persona-specific prompts
        persona_prompts = {
            'sophia': "You are Sophia, a strategic AI assistant focused on analysis and planning. Provide analytical insights.",
            'cherry': "You are Cherry, a friendly and helpful AI assistant. Provide warm, conversational responses.",
            'karen': "You are Karen, an operational AI focused on execution and workflow management. Provide structured, actionable responses."
        }
        
        system_prompt = persona_prompts.get(persona, persona_prompts['sophia'])
        
        # For demo purposes, return a structured response
        if 'weather' in message.lower() and 'database' in message.lower():
            return f"I can help you with both requests! For weather information, I would typically search live weather APIs. For database queries, I found relevant information in our system. {context_text}"
        
        return f"As {persona.title()}, I understand you're asking: '{message}'. {context_text} I'm ready to help with both database queries and internet searches once fully configured."
        
    except Exception as e:
        print(f"AI response generation failed: {e}")
        return f"I'm {persona.title()}, and I received your message: '{message}'. I'm working on connecting to live data sources to provide better responses."

# Add these endpoints to your main FastAPI app
def add_chat_endpoints(app: FastAPI):
    
    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """Handle chat messages with AI responses"""
        try:
            # Search for relevant context
            context = []
            
            # Search database
            db_results = search_database(request.message)
            context.extend(db_results)
            
            # Search internet
            internet_results = search_internet(request.message)
            context.extend(internet_results)
            
            # Generate AI response
            response = generate_ai_response(request.message, request.persona, context)
            
            # Collect sources
            sources = [item.get('source', 'Unknown') for item in context]
            
            return ChatResponse(
                response=response,
                persona=request.persona,
                sources=list(set(sources))
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/search", response_model=SearchResponse)
    async def search(request: SearchRequest):
        """Handle search requests"""
        try:
            all_results = []
            database_results = []
            internet_results = []
            
            if request.include_database:
                database_results = search_database(request.query)
                all_results.extend(database_results)
            
            if request.include_internet:
                internet_results = search_internet(request.query)
                all_results.extend(internet_results)
            
            return SearchResponse(
                results=all_results,
                database_results=database_results,
                internet_results=internet_results
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# Usage: Import and call add_chat_endpoints(app) in your main API file

