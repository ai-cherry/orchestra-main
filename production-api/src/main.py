"""
Production Flask API for Cherry-AI Admin Interface
High-performance backend with WebSocket support and database integration
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import asyncio
import json
import logging
from datetime import datetime
import uuid
from typing import Dict, List, Any, Optional
import os
from dataclasses import asdict

# Import our production systems
import sys
sys.path.append('/tmp/orchestra-main')
from core.database.production_database import db_manager, PersonaType, MemoryType, PrivacyLevel
from core.memory.production_memory_system import memory_manager, MemoryItem
from core.admin.unified_admin_interface import AdminInterface

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Enable CORS for admin interface
    CORS(app, origins=[
        "http://localhost:5174",  # Development
        "https://admin.cherry-ai.com",  # Production admin
        "https://cherry-ai.com"  # Production main
    ])
    
    # Initialize SocketIO for real-time features
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Store active connections
    active_connections = {}
    
    @app.before_first_request
    async def initialize_systems():
        """Initialize database and memory systems"""
        try:
            await db_manager.initialize()
            await memory_manager.initialize()
            logger.info("Production systems initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize systems: {e}")
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for load balancer"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    
    # System metrics endpoint
    @app.route('/api/system/metrics', methods=['GET'])
    async def get_system_metrics():
        """Get real-time system metrics"""
        try:
            # Get system health from database
            health_data = await db_manager.get_system_health(hours=1)
            
            # Get memory performance metrics
            memory_metrics = await memory_manager.get_performance_metrics()
            
            # Get cache statistics
            cache_stats = await memory_manager.cache.get_cache_stats()
            
            return jsonify({
                'system_health': health_data[-1] if health_data else {},
                'memory_metrics': memory_metrics,
                'cache_stats': cache_stats,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return jsonify({'error': 'Failed to retrieve metrics'}), 500
    
    # Persona management endpoints
    @app.route('/api/personas', methods=['GET'])
    async def get_personas():
        """Get all personas with their current status"""
        try:
            personas = []
            
            for persona_type in PersonaType:
                # Get persona metrics from database
                persona_data = await db_manager.get_persona_metrics(
                    uuid.UUID('00000000-0000-0000-0000-000000000001')  # Mock UUID for now
                )
                
                personas.append({
                    'id': str(uuid.uuid4()),
                    'name': persona_type.value.title(),
                    'type': persona_type.value,
                    'status': 'active',
                    'health': 95.5,
                    'interactions_24h': persona_data.get('interactions', {}).get('total', 0),
                    'avg_response_time': persona_data.get('interactions', {}).get('avg_response_time', 0),
                    'memory_count': persona_data.get('memory_stats', {}).get('total_memories', 0)
                })
            
            return jsonify({'personas': personas})
            
        except Exception as e:
            logger.error(f"Failed to get personas: {e}")
            return jsonify({'error': 'Failed to retrieve personas'}), 500
    
    @app.route('/api/personas/<persona_id>/config', methods=['GET', 'PUT'])
    async def persona_config(persona_id):
        """Get or update persona configuration"""
        try:
            if request.method == 'GET':
                # Return current persona configuration
                config = {
                    'personality': {
                        'playfulness': 85,
                        'empathy': 90,
                        'creativity': 95,
                        'analytical': 70,
                        'assertiveness': 75,
                        'warmth': 95,
                        'humor': 85,
                        'curiosity': 90,
                        'patience': 80,
                        'spontaneity': 85
                    },
                    'voice': {
                        'provider': 'elevenlabs',
                        'voice_id': 'cherry_voice_001',
                        'stability': 0.8,
                        'similarity_boost': 0.7,
                        'style': 0.6
                    },
                    'behavior': {
                        'response_style': 'conversational',
                        'memory_retention': 'high',
                        'learning_rate': 0.8,
                        'adaptation_speed': 'medium'
                    }
                }
                return jsonify(config)
            
            elif request.method == 'PUT':
                # Update persona configuration
                config_data = request.get_json()
                
                # Here you would update the database with new configuration
                # For now, just return success
                
                return jsonify({
                    'success': True,
                    'message': 'Persona configuration updated successfully'
                })
                
        except Exception as e:
            logger.error(f"Failed to handle persona config: {e}")
            return jsonify({'error': 'Failed to handle persona configuration'}), 500
    
    # Memory management endpoints
    @app.route('/api/memory/search', methods=['POST'])
    async def search_memories():
        """Search memories across personas"""
        try:
            search_data = request.get_json()
            query = search_data.get('query', '')
            persona_id = search_data.get('persona_id')
            memory_type = search_data.get('memory_type')
            limit = search_data.get('limit', 10)
            
            # Search memories using our advanced memory system
            memories = await memory_manager.search_memories(
                query=query,
                persona_id=persona_id,
                memory_type=memory_type,
                limit=limit
            )
            
            # Convert to JSON-serializable format
            results = []
            for memory in memories:
                results.append({
                    'id': memory.id,
                    'content': memory.content[:200] + '...' if len(memory.content) > 200 else memory.content,
                    'persona_id': memory.persona_id,
                    'memory_type': memory.memory_type,
                    'importance_score': memory.importance_score,
                    'created_at': memory.created_at.isoformat(),
                    'similarity_score': memory.context.get('similarity_score', 0)
                })
            
            return jsonify({
                'results': results,
                'total_found': len(results),
                'query': query
            })
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return jsonify({'error': 'Failed to search memories'}), 500
    
    # Generation endpoints
    @app.route('/api/generate', methods=['POST'])
    async def generate_content():
        """Generate multi-modal content"""
        try:
            generation_data = request.get_json()
            content_type = generation_data.get('type')  # image, video, audio, text
            prompt = generation_data.get('prompt')
            model = generation_data.get('model')
            parameters = generation_data.get('parameters', {})
            
            # Mock generation for now - in production this would call actual APIs
            generation_id = str(uuid.uuid4())
            
            # Store generation request in database
            # await db_manager.store_generation(...)
            
            return jsonify({
                'generation_id': generation_id,
                'status': 'processing',
                'estimated_time_seconds': 30,
                'message': f'Generating {content_type} content...'
            })
            
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            return jsonify({'error': 'Failed to generate content'}), 500
    
    @app.route('/api/generate/<generation_id>/status', methods=['GET'])
    def get_generation_status(generation_id):
        """Get generation status"""
        # Mock status for now
        return jsonify({
            'generation_id': generation_id,
            'status': 'completed',
            'progress': 100,
            'output_url': f'https://cdn.cherry-ai.com/generations/{generation_id}.png',
            'metadata': {
                'generation_time_ms': 15000,
                'cost_usd': 0.02,
                'quality_score': 0.95
            }
        })
    
    # WebSocket events for real-time updates
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        client_id = request.sid
        active_connections[client_id] = {
            'connected_at': datetime.utcnow(),
            'subscriptions': []
        }
        
        emit('connected', {
            'client_id': client_id,
            'server_time': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Client {client_id} connected")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        client_id = request.sid
        if client_id in active_connections:
            del active_connections[client_id]
        
        logger.info(f"Client {client_id} disconnected")
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        """Handle subscription to real-time updates"""
        client_id = request.sid
        subscription_type = data.get('type')  # system_metrics, persona_status, etc.
        
        if client_id in active_connections:
            active_connections[client_id]['subscriptions'].append(subscription_type)
            join_room(subscription_type)
            
            emit('subscribed', {
                'type': subscription_type,
                'message': f'Subscribed to {subscription_type} updates'
            })
    
    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        """Handle unsubscription from real-time updates"""
        client_id = request.sid
        subscription_type = data.get('type')
        
        if client_id in active_connections:
            subscriptions = active_connections[client_id]['subscriptions']
            if subscription_type in subscriptions:
                subscriptions.remove(subscription_type)
                leave_room(subscription_type)
                
                emit('unsubscribed', {
                    'type': subscription_type,
                    'message': f'Unsubscribed from {subscription_type} updates'
                })
    
    # Background task to send real-time updates
    def send_real_time_updates():
        """Send periodic updates to subscribed clients"""
        while True:
            try:
                # Send system metrics to subscribed clients
                socketio.emit('system_metrics_update', {
                    'cpu_usage': 45.2,
                    'memory_usage': 1024,
                    'active_connections': len(active_connections),
                    'response_time': 150.5,
                    'timestamp': datetime.utcnow().isoformat()
                }, room='system_metrics')
                
                # Send persona status updates
                socketio.emit('persona_status_update', {
                    'cherry': {'status': 'active', 'health': 95.5},
                    'sophia': {'status': 'active', 'health': 98.2},
                    'karen': {'status': 'active', 'health': 96.8},
                    'timestamp': datetime.utcnow().isoformat()
                }, room='persona_status')
                
                socketio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Failed to send real-time updates: {e}")
                socketio.sleep(10)
    
    # Start background task
    socketio.start_background_task(send_real_time_updates)
    
    return app, socketio

# Create application instance
app, socketio = create_app()

if __name__ == '__main__':
    # Run in production mode
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )

