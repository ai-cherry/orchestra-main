"""
Advanced Memory Architecture Implementation
Core memory system with three-layer architecture for deep, contextualized AI relationships
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import redis
import pinecone
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

class ConversationalMemory:
    """
    Redis-based conversational memory for real-time session context
    Handles short-term memory with automatic expiration and threading
    """
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        self.session_ttl = 86400  # 24 hours
        self.thread_ttl = 604800  # 7 days for conversation threads
        
    async def store_conversation_context(self, user_id: str, persona_id: str, context: Dict[str, Any]) -> str:
        """Store conversation context with automatic expiration and threading"""
        try:
            timestamp = int(time.time())
            key = f"conv:{user_id}:{persona_id}:{timestamp}"
            
            # Enhance context with metadata
            enhanced_context = {
                **context,
                'timestamp': timestamp,
                'user_id': user_id,
                'persona_id': persona_id,
                'session_id': context.get('session_id', str(uuid.uuid4())),
                'emotional_state': context.get('emotional_state', 'neutral'),
                'importance_score': self._calculate_importance(context)
            }
            
            # Store with TTL
            self.redis_client.setex(key, self.session_ttl, json.dumps(enhanced_context))
            
            # Update session index
            session_key = f"session:{user_id}:{persona_id}:{enhanced_context['session_id']}"
            self.redis_client.lpush(session_key, key)
            self.redis_client.expire(session_key, self.session_ttl)
            
            logger.info(f"Stored conversation context: {key}")
            return key
            
        except Exception as e:
            logger.error(f"Error storing conversation context: {e}")
            raise
    
    async def get_recent_context(self, user_id: str, persona_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent conversation context with intelligent filtering"""
        try:
            pattern = f"conv:{user_id}:{persona_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if not keys:
                return []
            
            # Sort by timestamp (embedded in key) and get most recent
            sorted_keys = sorted(keys, key=lambda x: int(x.split(':')[-1]), reverse=True)[:limit]
            
            contexts = []
            for key in sorted_keys:
                context_data = self.redis_client.get(key)
                if context_data:
                    context = json.loads(context_data)
                    contexts.append(context)
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error retrieving recent context: {e}")
            return []
    
    async def create_conversation_thread(self, user_id: str, persona_id: str, topic: str, initial_context: Dict[str, Any]) -> str:
        """Create a new conversation thread for topic-based organization"""
        try:
            thread_id = f"thread:{user_id}:{persona_id}:{uuid.uuid4()}"
            
            thread_data = {
                'thread_id': thread_id,
                'user_id': user_id,
                'persona_id': persona_id,
                'topic': topic,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'message_count': 0,
                'emotional_progression': ['neutral'],
                'key_insights': [],
                'relationship_markers': [],
                'initial_context': initial_context
            }
            
            self.redis_client.setex(thread_id, self.thread_ttl, json.dumps(thread_data))
            
            # Add to user's thread index
            user_threads_key = f"threads:{user_id}:{persona_id}"
            self.redis_client.lpush(user_threads_key, thread_id)
            self.redis_client.expire(user_threads_key, self.thread_ttl)
            
            logger.info(f"Created conversation thread: {thread_id}")
            return thread_id
            
        except Exception as e:
            logger.error(f"Error creating conversation thread: {e}")
            raise
    
    async def add_to_thread(self, thread_id: str, message: Dict[str, Any]) -> bool:
        """Add message to existing conversation thread with relationship tracking"""
        try:
            thread_data_raw = self.redis_client.get(thread_id)
            if not thread_data_raw:
                logger.warning(f"Thread not found: {thread_id}")
                return False
            
            thread_data = json.loads(thread_data_raw)
            
            # Update thread with new message
            thread_data['message_count'] += 1
            thread_data['last_activity'] = datetime.now().isoformat()
            
            # Track emotional progression
            emotion = message.get('emotion', 'neutral')
            thread_data['emotional_progression'].append(emotion)
            
            # Extract and store key insights
            if message.get('importance_score', 0) > 0.7:
                insight = {
                    'content': message.get('content', ''),
                    'timestamp': datetime.now().isoformat(),
                    'importance': message.get('importance_score'),
                    'type': message.get('insight_type', 'general')
                }
                thread_data['key_insights'].append(insight)
            
            # Track relationship markers
            if self._is_relationship_marker(message):
                marker = {
                    'type': message.get('relationship_marker_type'),
                    'description': message.get('content', ''),
                    'timestamp': datetime.now().isoformat()
                }
                thread_data['relationship_markers'].append(marker)
            
            # Update thread in Redis
            self.redis_client.setex(thread_id, self.thread_ttl, json.dumps(thread_data))
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding to thread: {e}")
            return False
    
    def _calculate_importance(self, context: Dict[str, Any]) -> float:
        """Calculate importance score for conversation context"""
        score = 0.0
        
        # Emotional intensity
        emotion = context.get('emotional_state', 'neutral')
        emotion_weights = {
            'joy': 0.8, 'love': 0.9, 'excitement': 0.7,
            'sadness': 0.8, 'anger': 0.7, 'fear': 0.6,
            'surprise': 0.5, 'neutral': 0.1
        }
        score += emotion_weights.get(emotion, 0.1) * 0.3
        
        # Personal revelation indicators
        content = context.get('content', '').lower()
        personal_keywords = ['feel', 'think', 'believe', 'dream', 'hope', 'fear', 'love', 'hate']
        personal_score = sum(1 for keyword in personal_keywords if keyword in content) / len(personal_keywords)
        score += personal_score * 0.25
        
        # Goal or commitment indicators
        commitment_keywords = ['will', 'going to', 'plan to', 'want to', 'need to', 'promise']
        commitment_score = sum(1 for keyword in commitment_keywords if keyword in content) / len(commitment_keywords)
        score += commitment_score * 0.2
        
        # Relationship depth indicators
        relationship_keywords = ['we', 'us', 'together', 'relationship', 'close', 'trust']
        relationship_score = sum(1 for keyword in relationship_keywords if keyword in content) / len(relationship_keywords)
        score += relationship_score * 0.25
        
        return min(score, 1.0)
    
    def _is_relationship_marker(self, message: Dict[str, Any]) -> bool:
        """Identify if message contains relationship milestone markers"""
        content = message.get('content', '').lower()
        markers = [
            'first time', 'never told', 'trust you', 'feel close',
            'special to me', 'care about', 'important to me'
        ]
        return any(marker in content for marker in markers)


class ContextualMemory:
    """
    Pinecone-based contextual memory for semantic long-term storage
    Handles relationship patterns, preferences, and important memories
    """
    
    def __init__(self, api_key: str, environment: str, index_name: str = "ai-personas"):
        pinecone.init(api_key=api_key, environment=environment)
        self.index = pinecone.Index(index_name)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def store_memory(self, user_id: str, persona_id: str, content: str, metadata: Dict[str, Any]) -> str:
        """Store long-term contextual memory with semantic indexing"""
        try:
            namespace = f"{user_id}_{persona_id}"
            
            # Generate embedding
            embedding = self.encoder.encode(content).tolist()
            
            # Create unique ID with timestamp
            memory_id = f"{user_id}_{persona_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Enhance metadata
            enhanced_metadata = {
                **metadata,
                'user_id': user_id,
                'persona_id': persona_id,
                'content_preview': content[:200],
                'stored_at': datetime.now().isoformat(),
                'importance_score': metadata.get('importance_score', 0.5),
                'privacy_level': metadata.get('privacy_level', 1),
                'memory_type': metadata.get('memory_type', 'general'),
                'emotional_context': metadata.get('emotional_context', 'neutral')
            }
            
            # Store in Pinecone
            self.index.upsert(
                vectors=[(memory_id, embedding, enhanced_metadata)],
                namespace=namespace
            )
            
            logger.info(f"Stored contextual memory: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing contextual memory: {e}")
            raise
    
    async def search_memories(self, user_id: str, persona_id: str, query: str, 
                            filters: Optional[Dict[str, Any]] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector similarity with metadata filtering"""
        try:
            namespace = f"{user_id}_{persona_id}"
            
            # Generate query embedding
            query_embedding = self.encoder.encode(query).tolist()
            
            # Build filter conditions
            filter_conditions = filters or {}
            
            # Always respect privacy levels (default max privacy level 2 for general queries)
            max_privacy = filter_conditions.get('max_privacy_level', 2)
            filter_conditions['privacy_level'] = {'$lte': max_privacy}
            
            # Perform vector search
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=namespace,
                filter=filter_conditions,
                include_metadata=True
            )
            
            # Process and rank results
            processed_results = []
            for match in results.matches:
                result = {
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata,
                    'relevance_score': self._calculate_relevance(match, query)
                }
                processed_results.append(result)
            
            # Sort by relevance score
            processed_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def get_relationship_patterns(self, user_id: str, persona_id: str) -> Dict[str, Any]:
        """Analyze relationship patterns from stored memories"""
        try:
            # Search for relationship-related memories
            relationship_memories = await self.search_memories(
                user_id, persona_id, 
                "relationship communication preferences personality",
                filters={'memory_type': 'relationship'},
                top_k=50
            )
            
            if not relationship_memories:
                return {'patterns': [], 'preferences': {}, 'depth_indicators': []}
            
            # Analyze patterns
            patterns = self._extract_relationship_patterns(relationship_memories)
            preferences = self._extract_communication_preferences(relationship_memories)
            depth_indicators = self._assess_relationship_depth(relationship_memories)
            
            return {
                'patterns': patterns,
                'preferences': preferences,
                'depth_indicators': depth_indicators,
                'total_memories': len(relationship_memories),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing relationship patterns: {e}")
            return {'patterns': [], 'preferences': {}, 'depth_indicators': []}
    
    def _calculate_relevance(self, match, query: str) -> float:
        """Calculate relevance score combining vector similarity with other factors"""
        base_score = match.score
        
        # Boost recent memories
        stored_at = datetime.fromisoformat(match.metadata.get('stored_at', datetime.now().isoformat()))
        days_old = (datetime.now() - stored_at).days
        recency_boost = max(0, 1 - (days_old / 365))  # Decay over a year
        
        # Boost high importance memories
        importance = match.metadata.get('importance_score', 0.5)
        
        # Combine factors
        relevance = base_score * 0.6 + recency_boost * 0.2 + importance * 0.2
        
        return relevance
    
    def _extract_relationship_patterns(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract relationship patterns from memory collection"""
        patterns = []
        
        # Analyze emotional progression
        emotions = [m['metadata'].get('emotional_context', 'neutral') for m in memories]
        emotion_trend = self._analyze_emotion_trend(emotions)
        if emotion_trend:
            patterns.append({
                'type': 'emotional_progression',
                'description': emotion_trend,
                'confidence': 0.8
            })
        
        # Analyze communication frequency
        timestamps = [m['metadata'].get('stored_at') for m in memories if m['metadata'].get('stored_at')]
        if len(timestamps) > 5:
            frequency_pattern = self._analyze_communication_frequency(timestamps)
            patterns.append({
                'type': 'communication_frequency',
                'description': frequency_pattern,
                'confidence': 0.7
            })
        
        return patterns
    
    def _extract_communication_preferences(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract communication preferences from memories"""
        preferences = {
            'preferred_topics': [],
            'communication_style': 'balanced',
            'response_preferences': {},
            'emotional_needs': []
        }
        
        # Analyze content for topic preferences
        all_content = ' '.join([m['metadata'].get('content_preview', '') for m in memories])
        
        # Simple topic extraction (in production, use more sophisticated NLP)
        topic_keywords = {
            'personal': ['feel', 'think', 'personal', 'life', 'family'],
            'professional': ['work', 'business', 'career', 'job', 'project'],
            'creative': ['art', 'music', 'creative', 'design', 'write'],
            'health': ['health', 'fitness', 'wellness', 'exercise', 'medical'],
            'travel': ['travel', 'trip', 'vacation', 'explore', 'adventure']
        }
        
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in all_content.lower())
            if score > 2:  # Threshold for topic preference
                preferences['preferred_topics'].append({
                    'topic': topic,
                    'score': score,
                    'confidence': min(score / 10, 1.0)
                })
        
        return preferences
    
    def _assess_relationship_depth(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assess relationship depth indicators from memories"""
        depth_indicators = []
        
        # Count high-importance memories
        high_importance_count = len([m for m in memories if m['metadata'].get('importance_score', 0) > 0.7])
        if high_importance_count > 5:
            depth_indicators.append({
                'indicator': 'deep_sharing',
                'description': f'{high_importance_count} high-importance shared memories',
                'strength': min(high_importance_count / 20, 1.0)
            })
        
        # Analyze privacy levels shared
        privacy_levels = [m['metadata'].get('privacy_level', 1) for m in memories]
        max_privacy = max(privacy_levels) if privacy_levels else 1
        if max_privacy >= 3:
            depth_indicators.append({
                'indicator': 'trust_level',
                'description': f'Shared privacy level {max_privacy} information',
                'strength': max_privacy / 4.0
            })
        
        return depth_indicators
    
    def _analyze_emotion_trend(self, emotions: List[str]) -> Optional[str]:
        """Analyze emotional trend in relationship"""
        if len(emotions) < 5:
            return None
        
        positive_emotions = ['joy', 'love', 'excitement', 'happiness']
        negative_emotions = ['sadness', 'anger', 'fear', 'frustration']
        
        recent_emotions = emotions[-10:]  # Last 10 interactions
        early_emotions = emotions[:10]    # First 10 interactions
        
        recent_positive = sum(1 for e in recent_emotions if e in positive_emotions)
        early_positive = sum(1 for e in early_emotions if e in positive_emotions)
        
        if recent_positive > early_positive + 2:
            return "Relationship showing positive emotional growth"
        elif early_positive > recent_positive + 2:
            return "Relationship may need attention - emotional decline detected"
        else:
            return "Stable emotional pattern in relationship"
    
    def _analyze_communication_frequency(self, timestamps: List[str]) -> str:
        """Analyze communication frequency patterns"""
        try:
            dates = [datetime.fromisoformat(ts) for ts in timestamps if ts]
            dates.sort()
            
            if len(dates) < 2:
                return "Insufficient data for frequency analysis"
            
            # Calculate average time between interactions
            intervals = [(dates[i+1] - dates[i]).total_seconds() / 3600 for i in range(len(dates)-1)]
            avg_interval_hours = sum(intervals) / len(intervals)
            
            if avg_interval_hours < 24:
                return "High frequency communication (multiple times daily)"
            elif avg_interval_hours < 168:  # 1 week
                return "Regular communication (several times weekly)"
            elif avg_interval_hours < 720:  # 1 month
                return "Moderate communication (weekly to monthly)"
            else:
                return "Infrequent communication (monthly or less)"
                
        except Exception as e:
            logger.error(f"Error analyzing communication frequency: {e}")
            return "Unable to analyze communication frequency"


class FoundationalMemory:
    """
    PostgreSQL-based foundational memory for structured persona and user data
    Handles user profiles, persona configurations, and relationship tracking
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        
    async def get_connection(self):
        """Get database connection with proper error handling"""
        try:
            return psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    async def get_user_profile(self, user_id: str, persona_id: str) -> Dict[str, Any]:
        """Retrieve comprehensive user profile for persona"""
        try:
            conn = await self.get_connection()
            cursor = conn.cursor()
            
            # Get user profile
            cursor.execute("""
                SELECT * FROM user_profiles WHERE user_id = %s
            """, (user_id,))
            user_profile = cursor.fetchone()
            
            # Get persona-specific configuration
            cursor.execute("""
                SELECT * FROM persona_configurations 
                WHERE user_id = %s AND persona_id = %s
            """, (user_id, persona_id))
            persona_config = cursor.fetchone()
            
            # Get relationship depth metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_interactions,
                    AVG(satisfaction_score) as avg_satisfaction,
                    AVG(importance_score) as avg_importance,
                    MAX(privacy_level) as max_privacy_shared
                FROM interaction_history 
                WHERE user_id = %s AND persona_id = %s
                AND created_at > NOW() - INTERVAL '90 days'
            """, (user_id, persona_id))
            relationship_metrics = cursor.fetchone()
            
            conn.close()
            
            return {
                'user_profile': dict(user_profile) if user_profile else {},
                'persona_config': dict(persona_config) if persona_config else {},
                'relationship_metrics': dict(relationship_metrics) if relationship_metrics else {},
                'retrieved_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving user profile: {e}")
            return {}
    
    async def update_relationship_depth(self, user_id: str, persona_id: str, interaction_data: Dict[str, Any]) -> bool:
        """Update relationship depth based on interaction"""
        try:
            conn = await self.get_connection()
            cursor = conn.cursor()
            
            # Calculate relationship depth change
            depth_change = self._calculate_depth_change(interaction_data)
            
            # Update user profile relationship depth
            depth_column = f"{persona_id}_relationship_depth"
            cursor.execute(f"""
                UPDATE user_profiles 
                SET {depth_column} = COALESCE({depth_column}, 0) + %s,
                    updated_at = NOW()
                WHERE user_id = %s
            """, (depth_change, user_id))
            
            # Log interaction
            cursor.execute("""
                INSERT INTO interaction_history 
                (user_id, persona_id, interaction_type, content_summary, 
                 emotional_context, privacy_level, satisfaction_score, importance_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, persona_id,
                interaction_data.get('type', 'conversation'),
                interaction_data.get('summary', ''),
                json.dumps(interaction_data.get('emotional_context', {})),
                interaction_data.get('privacy_level', 1),
                interaction_data.get('satisfaction_score'),
                interaction_data.get('importance_score')
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating relationship depth: {e}")
            return False
    
    async def store_persona_adaptation(self, user_id: str, persona_id: str, adaptation_data: Dict[str, Any]) -> bool:
        """Store persona adaptation and learning data"""
        try:
            conn = await self.get_connection()
            cursor = conn.cursor()
            
            # Update or insert persona configuration
            cursor.execute("""
                INSERT INTO persona_configurations 
                (user_id, persona_id, personality_traits, communication_style, 
                 knowledge_domains, adaptation_history, performance_metrics)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, persona_id) 
                DO UPDATE SET
                    personality_traits = EXCLUDED.personality_traits,
                    communication_style = EXCLUDED.communication_style,
                    knowledge_domains = EXCLUDED.knowledge_domains,
                    adaptation_history = EXCLUDED.adaptation_history,
                    performance_metrics = EXCLUDED.performance_metrics,
                    updated_at = NOW()
            """, (
                user_id, persona_id,
                json.dumps(adaptation_data.get('personality_traits', {})),
                json.dumps(adaptation_data.get('communication_style', {})),
                json.dumps(adaptation_data.get('knowledge_domains', {})),
                json.dumps(adaptation_data.get('adaptation_history', [])),
                json.dumps(adaptation_data.get('performance_metrics', {}))
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing persona adaptation: {e}")
            return False
    
    def _calculate_depth_change(self, interaction_data: Dict[str, Any]) -> float:
        """Calculate relationship depth change from interaction"""
        base_change = 0.1  # Base increment for any interaction
        
        # Boost for high importance interactions
        importance = interaction_data.get('importance_score', 0.5)
        importance_boost = importance * 0.5
        
        # Boost for high privacy level sharing
        privacy_level = interaction_data.get('privacy_level', 1)
        privacy_boost = (privacy_level - 1) * 0.3
        
        # Boost for positive emotional interactions
        emotional_context = interaction_data.get('emotional_context', {})
        emotion = emotional_context.get('primary_emotion', 'neutral')
        emotion_boost = 0.2 if emotion in ['joy', 'love', 'excitement'] else 0.0
        
        # Penalty for negative interactions
        satisfaction = interaction_data.get('satisfaction_score', 0.5)
        satisfaction_modifier = (satisfaction - 0.5) * 0.4
        
        total_change = base_change + importance_boost + privacy_boost + emotion_boost + satisfaction_modifier
        
        # Cap the change to prevent extreme jumps
        return max(-0.5, min(1.0, total_change))


class MemoryRouter:
    """
    Intelligent memory routing system that coordinates between all memory layers
    Provides unified interface for memory operations with smart layer selection
    """
    
    def __init__(self, conversational_memory: ConversationalMemory, 
                 contextual_memory: ContextualMemory, 
                 foundational_memory: FoundationalMemory):
        self.conv_memory = conversational_memory
        self.context_memory = contextual_memory
        self.foundation_memory = foundational_memory
        
    async def route_query(self, user_id: str, persona_id: str, query: str, 
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """Intelligently route memory queries to appropriate layers"""
        try:
            # Analyze query to determine memory needs
            query_analysis = await self._analyze_query(query, context)
            
            results = {}
            
            # Always check conversational memory for recent context
            if query_analysis['needs_recent_context']:
                results['conversational'] = await self.conv_memory.get_recent_context(
                    user_id, persona_id, limit=query_analysis.get('context_limit', 5)
                )
            
            # Check contextual memory for semantic matches
            if query_analysis['needs_semantic_search']:
                results['contextual'] = await self.context_memory.search_memories(
                    user_id, persona_id, query, 
                    filters=query_analysis.get('filters', {}),
                    top_k=query_analysis.get('search_limit', 10)
                )
            
            # Check foundational memory for persona/user data
            if query_analysis['needs_foundational_data']:
                results['foundational'] = await self.foundation_memory.get_user_profile(
                    user_id, persona_id
                )
            
            # Get relationship patterns if needed
            if query_analysis['needs_relationship_analysis']:
                results['relationship_patterns'] = await self.context_memory.get_relationship_patterns(
                    user_id, persona_id
                )
            
            # Synthesize results from multiple layers
            synthesized_result = await self._synthesize_memory_results(results, query_analysis)
            
            return synthesized_result
            
        except Exception as e:
            logger.error(f"Error in memory routing: {e}")
            return {
                'context': '',
                'confidence_score': 0.0,
                'memory_sources': [],
                'error': str(e)
            }
    
    async def store_interaction(self, user_id: str, persona_id: str, interaction_data: Dict[str, Any]) -> bool:
        """Store interaction across appropriate memory layers"""
        try:
            success_flags = []
            
            # Store in conversational memory
            conv_key = await self.conv_memory.store_conversation_context(
                user_id, persona_id, interaction_data
            )
            success_flags.append(bool(conv_key))
            
            # Store in contextual memory if important enough
            importance = interaction_data.get('importance_score', 0.5)
            if importance > 0.6:  # Threshold for long-term storage
                memory_id = await self.context_memory.store_memory(
                    user_id, persona_id,
                    interaction_data.get('content', ''),
                    {
                        'importance_score': importance,
                        'privacy_level': interaction_data.get('privacy_level', 1),
                        'memory_type': interaction_data.get('memory_type', 'conversation'),
                        'emotional_context': interaction_data.get('emotional_context', 'neutral')
                    }
                )
                success_flags.append(bool(memory_id))
            
            # Update foundational memory
            foundation_success = await self.foundation_memory.update_relationship_depth(
                user_id, persona_id, interaction_data
            )
            success_flags.append(foundation_success)
            
            return all(success_flags)
            
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
            return False
    
    async def _analyze_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze query to determine memory layer requirements"""
        query_lower = query.lower()
        
        analysis = {
            'original_query': query,
            'needs_recent_context': True,  # Almost always need recent context
            'needs_semantic_search': False,
            'needs_foundational_data': False,
            'needs_relationship_analysis': False,
            'context_limit': 5,
            'search_limit': 10,
            'filters': {}
        }
        
        # Determine if semantic search is needed
        semantic_indicators = [
            'remember', 'told me', 'discussed', 'talked about', 'mentioned',
            'what did', 'when did', 'how do', 'preference', 'like', 'dislike'
        ]
        if any(indicator in query_lower for indicator in semantic_indicators):
            analysis['needs_semantic_search'] = True
        
        # Determine if foundational data is needed
        foundational_indicators = [
            'profile', 'settings', 'preferences', 'configuration', 'relationship',
            'how long', 'since when', 'our relationship'
        ]
        if any(indicator in query_lower for indicator in foundational_indicators):
            analysis['needs_foundational_data'] = True
        
        # Determine if relationship analysis is needed
        relationship_indicators = [
            'relationship', 'how are we', 'our connection', 'trust', 'close',
            'patterns', 'communication style', 'how do I'
        ]
        if any(indicator in query_lower for indicator in relationship_indicators):
            analysis['needs_relationship_analysis'] = True
        
        # Set privacy filters based on context
        max_privacy = context.get('max_privacy_level', 2)
        analysis['filters']['max_privacy_level'] = max_privacy
        
        # Adjust limits based on query complexity
        if len(query.split()) > 10:  # Complex query
            analysis['context_limit'] = 10
            analysis['search_limit'] = 15
        
        return analysis
    
    async def _synthesize_memory_results(self, memory_results: Dict[str, Any], 
                                       query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize memory from multiple layers into coherent context"""
        try:
            # Build context from different memory sources
            context_parts = []
            memory_sources = []
            confidence_scores = []
            
            # Process conversational memory
            if 'conversational' in memory_results and memory_results['conversational']:
                conv_context = self._process_conversational_context(memory_results['conversational'])
                if conv_context:
                    context_parts.append(f"Recent conversation context: {conv_context}")
                    memory_sources.append('conversational')
                    confidence_scores.append(0.9)  # High confidence for recent context
            
            # Process contextual memory
            if 'contextual' in memory_results and memory_results['contextual']:
                contextual_context = self._process_contextual_memories(memory_results['contextual'])
                if contextual_context:
                    context_parts.append(f"Relevant memories: {contextual_context}")
                    memory_sources.append('contextual')
                    # Use average relevance score from search results
                    avg_relevance = sum(r['relevance_score'] for r in memory_results['contextual']) / len(memory_results['contextual'])
                    confidence_scores.append(avg_relevance)
            
            # Process foundational memory
            if 'foundational' in memory_results and memory_results['foundational']:
                foundational_context = self._process_foundational_data(memory_results['foundational'])
                if foundational_context:
                    context_parts.append(f"User profile and relationship data: {foundational_context}")
                    memory_sources.append('foundational')
                    confidence_scores.append(0.8)  # High confidence for profile data
            
            # Process relationship patterns
            if 'relationship_patterns' in memory_results and memory_results['relationship_patterns']:
                relationship_context = self._process_relationship_patterns(memory_results['relationship_patterns'])
                if relationship_context:
                    context_parts.append(f"Relationship insights: {relationship_context}")
                    memory_sources.append('relationship_analysis')
                    confidence_scores.append(0.7)  # Moderate confidence for pattern analysis
            
            # Combine all context
            combined_context = "\n\n".join(context_parts)
            
            # Calculate overall confidence
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            # Assess relationship depth from available data
            relationship_depth = self._assess_relationship_depth_from_results(memory_results)
            
            return {
                'context': combined_context,
                'confidence_score': overall_confidence,
                'memory_sources': memory_sources,
                'relationship_depth': relationship_depth,
                'query_analysis': query_analysis,
                'synthesis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error synthesizing memory results: {e}")
            return {
                'context': '',
                'confidence_score': 0.0,
                'memory_sources': [],
                'error': str(e)
            }
    
    def _process_conversational_context(self, conv_memories: List[Dict[str, Any]]) -> str:
        """Process conversational memories into readable context"""
        if not conv_memories:
            return ""
        
        # Sort by timestamp and take most relevant
        sorted_memories = sorted(conv_memories, key=lambda x: x.get('timestamp', 0), reverse=True)
        
        context_items = []
        for memory in sorted_memories[:3]:  # Top 3 most recent
            content = memory.get('content', '')
            emotion = memory.get('emotional_state', 'neutral')
            timestamp = memory.get('timestamp', 0)
            
            # Format timestamp
            try:
                dt = datetime.fromtimestamp(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = "recent"
            
            context_items.append(f"[{time_str}] {content} (emotion: {emotion})")
        
        return "; ".join(context_items)
    
    def _process_contextual_memories(self, contextual_memories: List[Dict[str, Any]]) -> str:
        """Process contextual memories into readable context"""
        if not contextual_memories:
            return ""
        
        # Sort by relevance score
        sorted_memories = sorted(contextual_memories, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        context_items = []
        for memory in sorted_memories[:5]:  # Top 5 most relevant
            metadata = memory.get('metadata', {})
            content_preview = metadata.get('content_preview', '')
            importance = metadata.get('importance_score', 0)
            memory_type = metadata.get('memory_type', 'general')
            
            context_items.append(f"{memory_type}: {content_preview} (importance: {importance:.2f})")
        
        return "; ".join(context_items)
    
    def _process_foundational_data(self, foundational_data: Dict[str, Any]) -> str:
        """Process foundational data into readable context"""
        context_parts = []
        
        # User profile information
        user_profile = foundational_data.get('user_profile', {})
        if user_profile:
            name = user_profile.get('name', 'User')
            preferences = user_profile.get('communication_preferences', {})
            context_parts.append(f"User: {name}, Communication preferences: {preferences}")
        
        # Relationship metrics
        relationship_metrics = foundational_data.get('relationship_metrics', {})
        if relationship_metrics:
            total_interactions = relationship_metrics.get('total_interactions', 0)
            avg_satisfaction = relationship_metrics.get('avg_satisfaction', 0)
            max_privacy = relationship_metrics.get('max_privacy_shared', 1)
            
            context_parts.append(
                f"Relationship: {total_interactions} interactions, "
                f"satisfaction: {avg_satisfaction:.2f}, "
                f"trust level: {max_privacy}"
            )
        
        return "; ".join(context_parts)
    
    def _process_relationship_patterns(self, relationship_data: Dict[str, Any]) -> str:
        """Process relationship pattern data into readable context"""
        context_parts = []
        
        patterns = relationship_data.get('patterns', [])
        for pattern in patterns:
            pattern_type = pattern.get('type', 'unknown')
            description = pattern.get('description', '')
            confidence = pattern.get('confidence', 0)
            context_parts.append(f"{pattern_type}: {description} (confidence: {confidence:.2f})")
        
        preferences = relationship_data.get('preferences', {})
        preferred_topics = preferences.get('preferred_topics', [])
        if preferred_topics:
            topics = [t['topic'] for t in preferred_topics[:3]]  # Top 3 topics
            context_parts.append(f"Preferred topics: {', '.join(topics)}")
        
        return "; ".join(context_parts)
    
    def _assess_relationship_depth_from_results(self, memory_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess relationship depth from memory results"""
        depth_assessment = {
            'level': 'new',
            'score': 0.0,
            'indicators': []
        }
        
        # Check foundational data for relationship metrics
        foundational_data = memory_results.get('foundational', {})
        relationship_metrics = foundational_data.get('relationship_metrics', {})
        
        if relationship_metrics:
            total_interactions = relationship_metrics.get('total_interactions', 0)
            max_privacy = relationship_metrics.get('max_privacy_shared', 1)
            avg_satisfaction = relationship_metrics.get('avg_satisfaction', 0.5)
            
            # Calculate depth score
            interaction_score = min(total_interactions / 100, 1.0)  # Normalize to 1.0
            privacy_score = max_privacy / 4.0  # Privacy levels 1-4
            satisfaction_score = avg_satisfaction
            
            depth_score = (interaction_score * 0.4 + privacy_score * 0.4 + satisfaction_score * 0.2)
            
            # Determine depth level
            if depth_score < 0.2:
                depth_level = 'new'
            elif depth_score < 0.4:
                depth_level = 'developing'
            elif depth_score < 0.6:
                depth_level = 'established'
            elif depth_score < 0.8:
                depth_level = 'deep'
            else:
                depth_level = 'intimate'
            
            depth_assessment.update({
                'level': depth_level,
                'score': depth_score,
                'indicators': [
                    f"{total_interactions} total interactions",
                    f"Privacy level {max_privacy} shared",
                    f"Average satisfaction: {avg_satisfaction:.2f}"
                ]
            })
        
        return depth_assessment


# Example usage and testing
async def main():
    """Example usage of the advanced memory architecture"""
    
    # Initialize memory components
    conv_memory = ConversationalMemory()
    
    # Note: These would need actual API keys and connection strings
    # contextual_memory = ContextualMemory(
    #     api_key="your-pinecone-api-key",
    #     environment="your-pinecone-environment"
    # )
    # foundational_memory = FoundationalMemory(
    #     "postgresql://user:password@localhost:5432/ai_personas"
    # )
    
    # memory_router = MemoryRouter(conv_memory, contextual_memory, foundational_memory)
    
    # Example interaction storage
    interaction_data = {
        'content': "I'm really excited about my upcoming trip to Japan! I've always wanted to visit Tokyo.",
        'emotional_state': 'excitement',
        'importance_score': 0.8,
        'privacy_level': 2,
        'memory_type': 'personal_sharing',
        'session_id': str(uuid.uuid4())
    }
    
    # Store conversation context
    context_key = await conv_memory.store_conversation_context(
        user_id="user123",
        persona_id="cherry",
        context=interaction_data
    )
    
    print(f"Stored conversation context: {context_key}")
    
    # Retrieve recent context
    recent_context = await conv_memory.get_recent_context(
        user_id="user123",
        persona_id="cherry",
        limit=5
    )
    
    print(f"Retrieved {len(recent_context)} recent context items")
    
    # Create conversation thread
    thread_id = await conv_memory.create_conversation_thread(
        user_id="user123",
        persona_id="cherry",
        topic="Travel Planning",
        initial_context=interaction_data
    )
    
    print(f"Created conversation thread: {thread_id}")

if __name__ == "__main__":
    asyncio.run(main())



class MemoryLayer:
    """Memory layer for agent context management"""
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.short_term_memory = []
        self.long_term_memory = []
        
    async def store(self, data: dict):
        """Store data in memory"""
        self.short_term_memory.append(data)
        if len(self.short_term_memory) > 100:
            # Move to long-term memory
            self.long_term_memory.extend(self.short_term_memory[:50])
            self.short_term_memory = self.short_term_memory[50:]
            
    async def retrieve(self, query: str, limit: int = 10):
        """Retrieve relevant memories"""
        # Simple implementation - in production would use vector similarity
        relevant = []
        for memory in self.short_term_memory + self.long_term_memory[-100:]:
            if query.lower() in str(memory).lower():
                relevant.append(memory)
                if len(relevant) >= limit:
                    break
        return relevant
        
    async def clear(self):
        """Clear all memories"""
        self.short_term_memory = []
        self.long_term_memory = []
