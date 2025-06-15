import unittest
import json
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app

class TestOrchestraAPI(unittest.TestCase):
    """Comprehensive test suite for Orchestra AI API"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test data
        self.test_message = "artificial intelligence"
        self.test_persona = "sophia"
        self.test_search_query = "machine learning"
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('services', data)
        self.assertEqual(data['status'], 'healthy')
        
        # Check required services
        services = data['services']
        self.assertEqual(services['chat_api'], 'operational')
        self.assertEqual(services['search_api'], 'operational')
        self.assertEqual(services['persona_management'], 'operational')
    
    def test_detailed_health_endpoint(self):
        """Test detailed health check endpoint"""
        response = self.client.get('/api/health/detailed')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('application', data)
        self.assertIn('system', data)
        self.assertIn('services', data)
        self.assertEqual(data['application']['name'], 'Orchestra AI Unified')
    
    def test_ping_endpoint(self):
        """Test ping endpoint"""
        response = self.client.get('/api/health/ping')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('timestamp', data)
    
    def test_version_endpoint(self):
        """Test version endpoint"""
        response = self.client.get('/api/health/version')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['application'], 'Orchestra AI Unified')
        self.assertEqual(data['version'], '1.0.0')
    
    def test_chat_endpoint_valid_request(self):
        """Test chat endpoint with valid request"""
        payload = {
            'message': self.test_message,
            'persona': self.test_persona
        }
        
        response = self.client.post('/api/chat',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('response', data)
        self.assertIn('persona', data)
        self.assertIn('sources', data)
        self.assertIn('search_results', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['persona'], self.test_persona)
    
    def test_chat_endpoint_missing_message(self):
        """Test chat endpoint with missing message"""
        payload = {'persona': self.test_persona}
        
        response = self.client.post('/api/chat',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_chat_endpoint_invalid_persona(self):
        """Test chat endpoint with invalid persona"""
        payload = {
            'message': self.test_message,
            'persona': 'invalid_persona'
        }
        
        response = self.client.post('/api/chat',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        # Should default to sophia
        self.assertEqual(data['persona'], 'sophia')
    
    def test_chat_personas_endpoint(self):
        """Test chat personas endpoint"""
        response = self.client.get('/api/chat/personas')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('personas', data)
        self.assertIn('total', data)
        self.assertEqual(data['total'], 3)
        
        # Check required personas
        persona_ids = list(data['personas'].keys())
        self.assertIn('cherry', persona_ids)
        self.assertIn('sophia', persona_ids)
        self.assertIn('karen', persona_ids)
    
    def test_search_endpoint_valid_request(self):
        """Test search endpoint with valid request"""
        payload = {
            'query': self.test_search_query,
            'include_database': True,
            'include_internet': True,
            'max_results': 10
        }
        
        response = self.client.post('/api/search',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertIn('total_results', data)
        self.assertIn('processing_time_ms', data)
        self.assertIn('query', data)
        self.assertEqual(data['query'], self.test_search_query)
    
    def test_search_endpoint_missing_query(self):
        """Test search endpoint with missing query"""
        payload = {'include_database': True}
        
        response = self.client.post('/api/search',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_advanced_search_endpoint(self):
        """Test advanced search endpoint"""
        payload = {
            'query': self.test_search_query,
            'search_mode': 'deep',
            'include_database': True,
            'include_internet': True,
            'max_results': 5
        }
        
        response = self.client.post('/api/search/advanced',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertIn('search_mode', data)
        self.assertIn('sources_used', data)
        self.assertIn('cost_estimate', data)
        self.assertEqual(data['search_mode'], 'deep')
    
    def test_search_sources_endpoint(self):
        """Test search sources endpoint"""
        response = self.client.get('/api/search/sources')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('sources', data)
        self.assertIn('total_sources', data)
        self.assertIn('enabled_sources', data)
        
        # Check required sources
        sources = data['sources']
        self.assertIn('duckduckgo', sources)
        self.assertIn('wikipedia', sources)
        self.assertIn('orchestra_db', sources)
    
    def test_search_modes_endpoint(self):
        """Test search modes endpoint"""
        response = self.client.get('/api/search/modes')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('modes', data)
        self.assertIn('total_modes', data)
        self.assertIn('default_mode', data)
        
        # Check required modes
        modes = data['modes']
        self.assertIn('normal', modes)
        self.assertIn('deep', modes)
        self.assertIn('super_deep', modes)
        self.assertIn('uncensored', modes)
    
    def test_personas_endpoint(self):
        """Test personas endpoint"""
        response = self.client.get('/api/personas')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('personas', data)
        self.assertIn('total', data)
        self.assertIn('active_personas', data)
        self.assertEqual(data['total'], 3)
        self.assertEqual(data['active_personas'], 3)
    
    def test_persona_detail_endpoint(self):
        """Test individual persona detail endpoint"""
        response = self.client.get(f'/api/personas/{self.test_persona}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('persona', data)
        
        persona = data['persona']
        self.assertEqual(persona['id'], self.test_persona)
        self.assertIn('name', persona)
        self.assertIn('description', persona)
        self.assertIn('expertise', persona)
        self.assertIn('capabilities', persona)
    
    def test_persona_not_found(self):
        """Test persona detail endpoint with invalid persona"""
        response = self.client.get('/api/personas/invalid_persona')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_persona_capabilities_endpoint(self):
        """Test persona capabilities endpoint"""
        response = self.client.get(f'/api/personas/{self.test_persona}/capabilities')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('persona_id', data)
        self.assertIn('expertise', data)
        self.assertIn('knowledge_domains', data)
        self.assertIn('capabilities', data)
        self.assertEqual(data['persona_id'], self.test_persona)
    
    def test_persona_analytics_endpoint(self):
        """Test persona analytics endpoint"""
        response = self.client.get('/api/personas/analytics/summary')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('total_personas', data)
        self.assertIn('active_personas', data)
        self.assertIn('persona_breakdown', data)
        self.assertIn('expertise_areas', data)
        self.assertEqual(data['total_personas'], 3)
    
    def test_persona_domain_leanings_endpoint(self):
        """Test persona domain leanings endpoint"""
        response = self.client.get(f'/api/personas/{self.test_persona}/domain-leanings')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('persona_id', data)
        self.assertIn('domain_leanings', data)
        self.assertIn('top_domains', data)
        self.assertEqual(data['persona_id'], self.test_persona)
    
    def test_persona_search_endpoint(self):
        """Test persona search endpoint"""
        payload = {'query': 'strategic'}
        
        response = self.client.post('/api/personas/search',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('query', data)
        self.assertIn('results', data)
        self.assertIn('total_matches', data)
        self.assertEqual(data['query'], 'strategic')
    
    def test_frontend_serving(self):
        """Test frontend serving"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Should return HTML content
        self.assertIn('text/html', response.content_type)
    
    def test_static_file_serving(self):
        """Test static file serving (fallback)"""
        response = self.client.get('/nonexistent-static-file.js')
        # Should return index.html for client-side routing
        self.assertEqual(response.status_code, 200)

class TestSearchFunctionality(unittest.TestCase):
    """Test search functionality in isolation"""
    
    def setUp(self):
        """Set up test environment"""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'routes'))
        from search import search_duckduckgo, search_wikipedia, search_database
        
        self.search_duckduckgo = search_duckduckgo
        self.search_wikipedia = search_wikipedia
        self.search_database = search_database
    
    def test_duckduckgo_search(self):
        """Test DuckDuckGo search function"""
        results = self.search_duckduckgo("artificial intelligence")
        
        # Should return a list
        self.assertIsInstance(results, list)
        
        # If results exist, check structure
        if results:
            result = results[0]
            self.assertIn('title', result)
            self.assertIn('content', result)
            self.assertIn('source', result)
            self.assertEqual(result['source'], 'DuckDuckGo')
    
    def test_wikipedia_search(self):
        """Test Wikipedia search function"""
        results = self.search_wikipedia("machine learning")
        
        # Should return a list
        self.assertIsInstance(results, list)
        
        # If results exist, check structure
        if results:
            result = results[0]
            self.assertIn('title', result)
            self.assertIn('content', result)
            self.assertIn('source', result)
            self.assertEqual(result['source'], 'Wikipedia')
    
    def test_database_search(self):
        """Test database search function"""
        results = self.search_database("orchestra")
        
        # Should return a list
        self.assertIsInstance(results, list)
        
        # If results exist, check structure
        if results:
            result = results[0]
            self.assertIn('title', result)
            self.assertIn('content', result)
            self.assertIn('source', result)
            self.assertEqual(result['source'], 'Orchestra Database')

class TestPerformance(unittest.TestCase):
    """Test performance and load handling"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_health_endpoint_performance(self):
        """Test health endpoint response time"""
        start_time = datetime.now()
        response = self.client.get('/api/health')
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds() * 1000
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1000)  # Should respond within 1 second
    
    def test_chat_endpoint_performance(self):
        """Test chat endpoint response time"""
        payload = {
            'message': 'test message',
            'persona': 'sophia'
        }
        
        start_time = datetime.now()
        response = self.client.post('/api/chat',
                                  data=json.dumps(payload),
                                  content_type='application/json')
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds() * 1000
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 5000)  # Should respond within 5 seconds
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = self.client.get('/api/health')
            results.append(response.status_code)
        
        # Create 10 concurrent threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status == 200 for status in results))

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestOrchestraAPI))
    test_suite.addTest(unittest.makeSuite(TestSearchFunctionality))
    test_suite.addTest(unittest.makeSuite(TestPerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)

