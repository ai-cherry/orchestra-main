#!/usr/bin/env python3
"""
Orchestra AI API Server Startup Script

This script properly handles package imports and starts the FastAPI server.
"""

import sys
import os
from pathlib import Path

# Add the API directory to Python path FIRST
api_dir = Path(__file__).parent.absolute()
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

# Set environment variables for development
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/orchestra_ai")
os.environ.setdefault("UPLOAD_DIR", str(api_dir / "uploads"))

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'asyncpg', 'pydantic',
        'structlog', 'numpy', 'sentence_transformers'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("💡 Install them with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Start the Orchestra AI API server"""
    try:
        # Check dependencies first
        if not check_dependencies():
            sys.exit(1)
        
        # Import main application
        from main import app
        import uvicorn
        
        print("🎼 Starting Orchestra AI Admin API - Phase 2")
        print("📡 Server will be available at: http://localhost:8000")
        print("📚 API documentation at: http://localhost:8000/docs")
        print("🔧 Admin interface at: http://localhost:3000")
        print("⚡ Environment: development")
        print("")
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,  # Enable auto-reload for development
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        print("")
        print("🔍 Checking specific module imports...")
        
        # Try to identify which specific import is failing
        test_imports = [
            ('database.connection', 'Database connection module'),
            ('database.models', 'Database models'),
            ('services.file_service', 'File service'),
            ('main', 'Main application')
        ]
        
        for module, description in test_imports:
            try:
                __import__(module)
                print(f"  ✅ {description}")
            except ImportError as ie:
                print(f"  ❌ {description}: {ie}")
        
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Server Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 