#!/usr/bin/env python3
"""
Test script for the Public Endpoint Bridge implementation
Tests connectivity, authentication, and basic operations
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path

# Add the services directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from services.ai_collaboration.manus_client_enhanced import ManusAIClient, ManusAIOrchestrator
from services.ai_collaboration.cursor_client_enhanced import CursorAIClient, CursorCodeAssistant

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BridgeTestSuite:
    """Test suite for the public endpoint bridge"""
    
    def __init__(self, bridge_url: str, manus_key: str, cursor_key: str):
        self.bridge_url = bridge_url
        self.manus_key = manus_key
        self.cursor_key = cursor_key
        self.test_results = []
        
    async def run_all_tests(self):
        """Run all test scenarios"""
        logger.info("🧪 Starting Public Endpoint Bridge Test Suite")
        logger.info("=" * 50)
        
        # Test 1: Basic connectivity
        await self.test_basic_connectivity()
        
        # Test 2: Authentication
        await self.test_authentication()
        
        # Test 3: Message exchange
        await self.test_message_exchange()
        
        # Test 4: Collaboration workflow
        await self.test_collaboration_workflow()
        
        # Test 5: Error handling
        await self.test_error_handling()
        
        # Print results
        self.print_results()
        
    async def test_basic_connectivity(self):
        """Test basic WebSocket connectivity"""
        test_name = "Basic Connectivity"
        logger.info(f"\n📋 Test: {test_name}")
        
        try:
            import websockets
            
            # Try to connect without authentication
            async with websockets.connect(self.bridge_url) as ws:
                await ws.ping()
                result = "✅ PASSED - WebSocket connection established"
                
        except Exception as e:
            result = f"❌ FAILED - {str(e)}"
            
        self.test_results.append((test_name, result))
        logger.info(result)
        
    async def test_authentication(self):
        """Test authentication for both clients"""
        test_name = "Authentication"
        logger.info(f"\n📋 Test: {test_name}")
        
        results = []
        
        # Test Manus authentication
        manus_client = ManusAIClient(self.bridge_url, self.manus_key)
        if await manus_client.connect():
            results.append("✅ Manus authentication successful")
            await manus_client.close()
        else:
            results.append("❌ Manus authentication failed")
            
        # Test Cursor authentication
        cursor_client = CursorAIClient(self.bridge_url, self.cursor_key)
        if await cursor_client.connect():
            results.append("✅ Cursor authentication successful")
            await cursor_client.close()
        else:
            results.append("❌ Cursor authentication failed")
            
        result = " | ".join(results)
        self.test_results.append((test_name, result))
        logger.info(result)
        
    async def test_message_exchange(self):
        """Test message exchange between clients"""
        test_name = "Message Exchange"
        logger.info(f"\n📋 Test: {test_name}")
        
        try:
            # Create clients
            manus_client = ManusAIClient(self.bridge_url, self.manus_key)
            cursor_client = CursorAIClient(self.bridge_url, self.cursor_key)
            
            # Track received messages
            manus_received = []
            cursor_received = []
            
            # Register test handlers
            manus_client.register_handler("test_message", 
                lambda data: manus_received.append(data))
            cursor_client.register_handler("test_message", 
                lambda data: cursor_received.append(data))
            
            # Connect both clients
            if await manus_client.connect() and await cursor_client.connect():
                # Send test message from Manus
                await manus_client.send_message({
                    "type": "test_message",
                    "content": "Hello from Manus"
                })
                
                # Wait for message propagation
                await asyncio.sleep(1)
                
                # Send test message from Cursor
                await cursor_client.send_message({
                    "type": "test_message",
                    "content": "Hello from Cursor"
                })
                
                # Wait for message propagation
                await asyncio.sleep(1)
                
                # Check results
                if len(cursor_received) > 0 and len(manus_received) > 0:
                    result = "✅ PASSED - Bidirectional message exchange working"
                else:
                    result = f"❌ FAILED - Messages not received (Manus: {len(manus_received)}, Cursor: {len(cursor_received)})"
                    
                await manus_client.close()
                await cursor_client.close()
            else:
                result = "❌ FAILED - Could not connect clients"
                
        except Exception as e:
            result = f"❌ FAILED - {str(e)}"
            
        self.test_results.append((test_name, result))
        logger.info(result)
        
    async def test_collaboration_workflow(self):
        """Test a complete collaboration workflow"""
        test_name = "Collaboration Workflow"
        logger.info(f"\n📋 Test: {test_name}")
        
        try:
            # Create clients
            manus_client = ManusAIClient(self.bridge_url, self.manus_key)
            cursor_client = CursorAIClient(self.bridge_url, self.cursor_key)
            
            # Track collaboration events
            collaboration_events = []
            
            # Register collaboration handler
            async def track_collaboration(data):
                collaboration_events.append(data)
                
            cursor_client.register_handler("code_assistance_request", track_collaboration)
            
            # Connect clients
            if await manus_client.connect() and await cursor_client.connect():
                # Create orchestrator and assistant
                orchestrator = ManusAIOrchestrator(manus_client)
                assistant = CursorCodeAssistant(cursor_client)
                
                # Initiate collaboration
                await orchestrator.collaborate_with_cursor(
                    "Optimize WebSocket handling",
                    ["test_file.py"]
                )
                
                # Wait for collaboration
                await asyncio.sleep(2)
                
                if len(collaboration_events) > 0:
                    result = "✅ PASSED - Collaboration workflow executed"
                else:
                    result = "❌ FAILED - No collaboration events received"
                    
                await manus_client.close()
                await cursor_client.close()
            else:
                result = "❌ FAILED - Could not connect clients"
                
        except Exception as e:
            result = f"❌ FAILED - {str(e)}"
            
        self.test_results.append((test_name, result))
        logger.info(result)
        
    async def test_error_handling(self):
        """Test error handling and reconnection"""
        test_name = "Error Handling"
        logger.info(f"\n📋 Test: {test_name}")
        
        try:
            # Test invalid authentication
            invalid_client = ManusAIClient(self.bridge_url, "invalid_key", auto_reconnect=False)
            
            if not await invalid_client.connect():
                result = "✅ PASSED - Invalid authentication properly rejected"
            else:
                result = "❌ FAILED - Invalid authentication was accepted"
                await invalid_client.close()
                
        except Exception as e:
            result = f"❌ FAILED - {str(e)}"
            
        self.test_results.append((test_name, result))
        logger.info(result)
        
    def print_results(self):
        """Print test results summary"""
        logger.info("\n" + "=" * 50)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 50)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results:
            logger.info(f"{test_name}: {result}")
            if "PASSED" in result:
                passed += 1
            else:
                failed += 1
                
        logger.info("\n" + "-" * 50)
        logger.info(f"Total Tests: {len(self.test_results)}")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")

async def main():
    """Main test runner"""
    # Get configuration from environment or use defaults
    bridge_url = os.getenv("BRIDGE_URL", "ws://localhost:8765")
    manus_key = os.getenv("MANUS_API_KEY", "manus_live_collab_2024")
    cursor_key = os.getenv("CURSOR_API_KEY", "cursor_live_collab_2024")
    
    # Show configuration
    logger.info("🔧 Test Configuration:")
    logger.info(f"Bridge URL: {bridge_url}")
    logger.info(f"Manus Key: {'*' * 10}{manus_key[-4:]}")
    logger.info(f"Cursor Key: {'*' * 10}{cursor_key[-4:]}")
    
    # Create and run test suite
    test_suite = BridgeTestSuite(bridge_url, manus_key, cursor_key)
    await test_suite.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 Test suite interrupted")
    except Exception as e:
        logger.error(f"❌ Test suite error: {e}")
        sys.exit(1)