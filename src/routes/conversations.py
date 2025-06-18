from flask import Blueprint, jsonify, request
import os
import redis

from src.models.conversation import EnhancedConversation, db

conversations_bp = Blueprint('conversations', __name__)

# Initialize Redis connection if URL provided
redis_url = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(redis_url) if redis_url else None

@conversations_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Retrieve conversations with optional caching and limiting."""
    limit = request.args.get('limit', type=int)
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

    cache_key = f'conversations:{limit}'

    if redis_client and not force_refresh:
        cached = redis_client.get(cache_key)
        if cached:
            import json
            return jsonify({'conversations': json.loads(cached)}), 200

    query = EnhancedConversation.query.order_by(
        EnhancedConversation.created_at.desc()
    )
    if limit:
        query = query.limit(limit)

    conversations = query.all()
    results = [c.to_dict() for c in conversations]

    if redis_client:
        import json
        ttl = int(os.getenv('REDIS_TTL', '300'))
        redis_client.setex(cache_key, ttl, json.dumps(results))

    return jsonify({'conversations': results}), 200
