#!/usr/bin/env python3
"""
Main entry point for running the API as a module
Usage: python -m api
"""

import os
import sys
from pathlib import Path

# Set environment variables
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/orchestra_ai")
os.environ.setdefault("UPLOAD_DIR", str(Path(__file__).parent / "uploads"))

def main():
    """Start the Orchestra AI API server"""
    try:
        import uvicorn
        from .main import app
        
        print("🎼 Starting Orchestra AI Admin API - Phase 2")
        print("📡 Server will be available at: http://localhost:8000")
        print("📚 API documentation at: http://localhost:8000/docs")
        print("🔧 Admin interface at: http://localhost:3000")
        print("⚡ Running as Python module")
        print("")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Server Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 