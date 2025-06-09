#!/usr/bin/env python3
"""
🔍 Minimal Weaviate MCP Server for Testing
Provides basic vector database capabilities for  integration
"""

import json
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeaviateHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_json_response({
                "status": "healthy", 
                "service": "weaviate-direct",
                "capabilities": ["vector_search", "schema_management", "hybrid_search"]
            })
        else:
            self.send_error(404)
    
    def send_json_response(self, data):
        json_data = json.dumps(data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(json_data)))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Suppress logging

def start_server():
    server = HTTPServer(("localhost", 8011), WeaviateHandler)
    logger.info("🔍 Weaviate MCP Server starting on port 8011")
    server.serve_forever()

if __name__ == "__main__":
    start_server() 