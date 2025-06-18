import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
import asyncio
from asgiref.wsgi import WsgiToAsgi
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.chat_v2 import chat_v2_bp
from src.routes.chat import chat_bp
from src.routes.search import search_bp
from src.routes.personas import personas_bp
from src.routes.health import health_bp
from src.routes.conversations import conversations_bp
from src.config import Config

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config.from_object(Config)

# Enable CORS for all routes (unified app eliminates cross-origin issues)
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Register all API blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(chat_v2_bp)
app.register_blueprint(chat_bp, url_prefix='/api')
app.register_blueprint(search_bp, url_prefix='/api')
app.register_blueprint(personas_bp, url_prefix='/api')
app.register_blueprint(health_bp, url_prefix='/api')
app.register_blueprint(conversations_bp, url_prefix='/api')

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve React frontend and handle client-side routing"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    # Serve static files directly
    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        # For all other routes, serve index.html (React Router will handle routing)
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            # Fallback HTML if React build not available
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Orchestra AI - Unified Platform</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: white; }
                    .container { max-width: 800px; margin: 0 auto; text-align: center; }
                    .status { background: #2a2a2a; padding: 20px; border-radius: 10px; margin: 20px 0; }
                    .api-link { color: #4CAF50; text-decoration: none; }
                    .api-link:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎯 Orchestra AI - Unified Platform</h1>
                    <div class="status">
                        <h2>✅ Backend API Active</h2>
                        <p>The unified Flask backend is running successfully!</p>
                        <p><strong>API Endpoints Available:</strong></p>
                        <ul style="text-align: left; display: inline-block;">
                            <li><a href="/api/health" class="api-link">/api/health</a> - System health check</li>
                            <li><a href="/api/chat" class="api-link">/api/chat</a> - AI chat with personas</li>
                            <li><a href="/api/search" class="api-link">/api/search</a> - Multi-source search</li>
                            <li><a href="/api/personas" class="api-link">/api/personas</a> - Persona management</li>
                        </ul>
                        <p><em>Frontend React build will be integrated next...</em></p>
                    </div>
                </div>
            </body>
            </html>
            """, 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

