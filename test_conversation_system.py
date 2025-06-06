#!/usr/bin/env python3
"""
Cherry AI Conversation System Test
Tests the complete conversation and learning system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_conversation_engine():
    """Test the conversation engine functionality"""
    print("🧪 Testing Conversation Engine...")
    
    try:
        # Import necessary modules
        import asyncpg
        from api.conversation_engine import ConversationEngine, ConversationMode
        
        # Set up test database connection
        database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:postgres@localhost:5432/cherry_ai"
        )
        
        print(f"Connecting to database: {database_url}")
        
        # Create database connection pool
        try:
            pool = await asyncpg.create_pool(database_url, min_size=1, max_size=2)
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("Note: Make sure PostgreSQL is running and database exists")
            return False
        
        # Initialize conversation engine
        engine = ConversationEngine(pool)
        await engine.initialize()
        print("✅ Conversation engine initialized")
        
        # Test persona personalities
        personas = ['cherry', 'sophia', 'karen']
        for persona in personas:
            if persona in engine.personalities:
                personality = engine.personalities[persona]
                traits = list(personality.base_traits.keys())[:3]
                print(f"✅ {persona.capitalize()} personality loaded with traits: {traits}")
            else:
                print(f"❌ {persona.capitalize()} personality not found")
                return False
        
        # Test conversation generation (mock user)
        test_user_id = 1
        test_message = "Hello! How are you today?"
        
        print(f"\n📝 Testing conversation with Cherry...")
        try:
            response = await engine.generate_response(
                user_id=test_user_id,
                persona_type='cherry',
                user_message=test_message,
                mode=ConversationMode.CASUAL
            )
            
            print(f"✅ Generated response: {response['response'][:100]}...")
            print(f"✅ Response time: {response['response_time_ms']}ms")
            print(f"✅ Session ID: {response['session_id']}")
            
        except Exception as e:
            print(f"❌ Conversation generation failed: {e}")
            return False
        
        # Test relationship insights
        print(f"\n🔍 Testing relationship insights...")
        try:
            insights = await engine.get_relationship_insights(
                user_id=test_user_id,
                persona_type='cherry'
            )
            
            print(f"✅ Trust score: {insights['trust_score']}")
            print(f"✅ Interaction count: {insights['interaction_count']}")
            print(f"✅ Learning patterns: {insights['learning_patterns_active']}")
            
        except Exception as e:
            print(f"❌ Relationship insights failed: {e}")
            return False
        
        # Close database connection
        await pool.close()
        print("✅ Database connection closed")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_api_integration():
    """Test API integration with conversation system"""
    print("\n🌐 Testing API Integration...")
    
    try:
        # Import API main module
        from api.main import app, conversation_engine
        
        print("✅ API module imported successfully")
        
        # Check if conversation engine is available
        if conversation_engine is None:
            print("⚠️  Conversation engine not initialized in API")
            print("   This is normal if database is not available")
        else:
            print("✅ Conversation engine integrated with API")
        
        # Test API endpoints exist
        routes = [route.path for route in app.routes]
        conversation_routes = [
            '/api/conversation',
            '/api/conversation/history/{persona_type}',
            '/api/relationship/insights/{persona_type}',
            '/api/conversation/active-sessions'
        ]
        
        for route in conversation_routes:
            if any(route.replace('{persona_type}', '') in api_route for api_route in routes):
                print(f"✅ API route exists: {route}")
            else:
                print(f"❌ API route missing: {route}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

def test_frontend_files():
    """Test that frontend files exist and are properly configured"""
    print("\n🎨 Testing Frontend Files...")
    
    required_files = [
        'admin-interface/chat.html',
        'admin-interface/api-client.js',
        'admin-interface/enhanced-production-interface.html'
    ]
    
    all_files_exist = True
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_files_exist = False
    
    # Check chat.html for required components
    chat_file = Path('admin-interface/chat.html')
    if chat_file.exists():
        content = chat_file.read_text()
        required_components = [
            'class ChatInterface',
            'sendMessage',
            'apiClient',
            'persona-tab',
            'conversation-engine'
        ]
        
        for component in required_components:
            if component in content:
                print(f"✅ Chat interface has: {component}")
            else:
                print(f"⚠️  Chat interface missing: {component}")
    
    # Check API client for conversation methods
    api_client_file = Path('admin-interface/api-client.js')
    if api_client_file.exists():
        content = api_client_file.read_text()
        required_methods = [
            'sendMessage',
            'getConversationHistory',
            'getRelationshipInsights',
            'getActiveSessions'
        ]
        
        for method in required_methods:
            if method in content:
                print(f"✅ API client has: {method}")
            else:
                print(f"❌ API client missing: {method}")
                all_files_exist = False
    
    return all_files_exist

async def main():
    """Run all tests"""
    print("🍒 Cherry AI Conversation System Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Conversation Engine
    result1 = await test_conversation_engine()
    test_results.append(("Conversation Engine", result1))
    
    # Test 2: API Integration
    result2 = await test_api_integration()
    test_results.append(("API Integration", result2))
    
    # Test 3: Frontend Files
    result3 = test_frontend_files()
    test_results.append(("Frontend Files", result3))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 All tests passed! Cherry AI conversation system is ready.")
        print("\n🚀 Next steps:")
        print("1. Run: python start_cherry_ai.py")
        print("2. Open: admin-interface/chat.html")
        print("3. Register a user and start chatting!")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print("\n🔧 Common fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start PostgreSQL database")
        print("3. Run database setup if needed")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1) 