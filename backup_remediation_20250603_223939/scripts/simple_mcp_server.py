#!/usr/bin/env python3
"""Simple MCP-compatible server for Roo integration"""
        """Handle GET requests"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for mode execution"""
        if self.path.startswith("/execute/"):
            mode = self.path.split("/")[-1]
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Simple mode execution simulation
            response = {
                "mode": mode,
                "status": "completed",
                "result": f"Executed {mode} mode successfully"
            }
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    PORT = 8765
    with socketserver.TCPServer(("", PORT), MCPHandler) as httpd:
        print(f"MCP Server running on port {PORT}")
        httpd.serve_forever()
