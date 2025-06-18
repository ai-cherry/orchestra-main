#!/usr/bin/env python3
"""
PR #157 Merge Conflict Resolution Script
Applies the beneficial changes from PR #157 while avoiding conflicts
"""

import os
import shutil
import subprocess
import sys

def run_command(cmd, cwd=None):
    """Run shell command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def apply_pr157_improvements():
    """Apply the beneficial changes from PR #157"""
    
    print("🔧 Applying PR #157 improvements to main branch...")
    
    # 1. Update conversation.py - remove unnecessary import
    conversation_py_content = '''from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from decimal import Decimal

from .user import db

class EnhancedConversation(db.Model):
    __tablename__ = 'enhanced_conversations'

    id = db.Column(db.Integer, primary_key=True)
    gong_call_id = db.Column(db.String(255), unique=True)
    title = db.Column(db.Text)
    duration = db.Column(db.Integer)
    apartment_relevance = db.Column(db.Numeric(5, 2))
    business_value = db.Column(db.Numeric(12, 2))
    call_outcome = db.Column(db.String(100))
    competitive_mentions = db.Column(JSONB)
    sophia_insights = db.Column(JSONB)
    created_at = db.Column(db.DateTime, server_default=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'gong_call_id': self.gong_call_id,
            'title': self.title,
            'duration': self.duration,
            'apartment_relevance': float(self.apartment_relevance) if isinstance(self.apartment_relevance, Decimal) else self.apartment_relevance,
            'business_value': float(self.business_value) if isinstance(self.business_value, Decimal) else self.business_value,
            'call_outcome': self.call_outcome,
            'competitive_mentions': self.competitive_mentions,
            'sophia_insights': self.sophia_insights,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
'''
    
    # 2. Update conversations.py - add json import and default limit
    conversations_py_content = '''from flask import Blueprint, jsonify, request
import os
import redis
import json

from src.models.conversation import EnhancedConversation, db

conversations_bp = Blueprint('conversations', __name__)

# Initialize Redis connection if URL provided
redis_url = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(redis_url) if redis_url else None

DEFAULT_LIMIT = int(os.getenv("CONVERSATIONS_LIMIT", "10"))

@conversations_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Retrieve conversations with optional caching and limiting."""
    limit = request.args.get('limit', default=DEFAULT_LIMIT, type=int)
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

    cache_key = f'conversations:{limit}'

    if redis_client and not force_refresh:
        cached = redis_client.get(cache_key)
        if cached:
            return jsonify({'conversations': json.loads(cached)}), 200

    query = EnhancedConversation.query.order_by(
        EnhancedConversation.created_at.desc()
    )
    if limit:
        query = query.limit(limit)

    conversations = query.all()
    results = [c.to_dict() for c in conversations]

    if redis_client:
        ttl = int(os.getenv('REDIS_TTL', '300'))
        redis_client.setex(cache_key, ttl, json.dumps(results))

    return jsonify({'conversations': results}), 200
'''
    
    try:
        # Write the improved files
        with open('src/models/conversation.py', 'w') as f:
            f.write(conversation_py_content)
        print("✅ Updated src/models/conversation.py")
        
        with open('src/routes/conversations.py', 'w') as f:
            f.write(conversations_py_content)
        print("✅ Updated src/routes/conversations.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying improvements: {e}")
        return False

def fix_vercel_deployment():
    """Fix Vercel deployment configuration"""
    
    print("🔧 Fixing Vercel deployment configuration...")
    
    # Update vercel.json with proper configuration
    vercel_config = '''{
  "version": 2,
  "builds": [
    {
      "src": "src/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "src/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "web/index.html"
    }
  ],
  "env": {
    "FLASK_ENV": "production"
  }
}'''
    
    try:
        with open('vercel.json', 'w') as f:
            f.write(vercel_config)
        print("✅ Updated vercel.json")
        
        # Update requirements.txt to include all dependencies
        requirements = '''flask==2.3.3
flask-cors==4.0.0
flask-sqlalchemy==3.0.5
psycopg2-binary==2.9.7
redis==4.6.0
requests==2.31.0
python-dotenv==1.0.0
gunicorn==21.2.0
pytest==7.4.2
'''
        
        with open('requirements.txt', 'w') as f:
            f.write(requirements)
        print("✅ Updated requirements.txt")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing Vercel config: {e}")
        return False

def fix_testing_issues():
    """Fix testing configuration and dependencies"""
    
    print("🔧 Fixing testing configuration...")
    
    # Update pytest.ini
    pytest_config = '''[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
'''
    
    try:
        with open('pytest.ini', 'w') as f:
            f.write(pytest_config)
        print("✅ Updated pytest.ini")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing testing config: {e}")
        return False

def commit_changes():
    """Commit the resolved changes"""
    
    print("🔧 Committing resolved changes...")
    
    success, stdout, stderr = run_command("git add .")
    if not success:
        print(f"❌ Error staging changes: {stderr}")
        return False
    
    success, stdout, stderr = run_command('git commit -m "Resolve PR #157 conflicts: Apply beneficial changes and fix deployment"')
    if not success:
        print(f"❌ Error committing changes: {stderr}")
        return False
    
    print("✅ Changes committed successfully")
    return True

def main():
    """Main resolution process"""
    
    print("🚀 Starting PR #157 merge conflict resolution...")
    
    # Check if we're in the right directory
    if not os.path.exists('src/models/conversation.py'):
        print("❌ Error: Not in orchestra-main repository directory")
        sys.exit(1)
    
    # Apply improvements
    if not apply_pr157_improvements():
        print("❌ Failed to apply PR #157 improvements")
        sys.exit(1)
    
    # Fix deployment issues
    if not fix_vercel_deployment():
        print("❌ Failed to fix Vercel deployment")
        sys.exit(1)
    
    # Fix testing issues
    if not fix_testing_issues():
        print("❌ Failed to fix testing configuration")
        sys.exit(1)
    
    # Commit changes
    if not commit_changes():
        print("❌ Failed to commit changes")
        sys.exit(1)
    
    print("🎉 PR #157 merge conflict resolution completed successfully!")
    print("\n📋 Next steps:")
    print("1. Push changes to main branch")
    print("2. Close PR #157 as resolved")
    print("3. Test Vercel deployment")
    print("4. Implement missing Sophia features")

if __name__ == "__main__":
    main()

