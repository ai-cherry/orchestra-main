#!/usr/bin/env python3
"""
Cherry AI System Startup Script
Launches the complete Cherry AI admin interface system
"""

import os
import sys
import subprocess
import time
import signal
import webbrowser
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'asyncpg',
        'pydantic',
        'jwt',
        'bcrypt'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall dependencies with:")
        print("  pip install -r requirements.txt")
        return False
    
    print("✅ All required dependencies are installed")
    return True

def setup_environment():
    """Set up environment variables"""
    env_vars = {
        'DATABASE_URL': 'postgresql://postgres:postgres@localhost:5432/cherry_ai',
        'JWT_SECRET_KEY': 'cherry-ai-secret-key-development-only',
        'PYTHONPATH': str(Path.cwd())
    }
    
    for key, default_value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = default_value
            print(f"🔧 Set {key} to default value")
    
    print("✅ Environment variables configured")

def check_database():
    """Check if database is available"""
    try:
        import asyncpg
        import asyncio
        
        async def test_connection():
            try:
                conn = await asyncpg.connect(os.environ['DATABASE_URL'])
                await conn.close()
                return True
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                print("Note: API will run with mock data if database is unavailable")
                return False
        
        return asyncio.run(test_connection())
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting Cherry AI API server...")
    
    api_path = Path("api/main.py")
    if not api_path.exists():
        print(f"❌ API file not found: {api_path}")
        return None
    
    # Start uvicorn server
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ], cwd=Path.cwd())
        
        print("✅ API server started on http://localhost:8000")
        print("📚 API documentation available at http://localhost:8000/docs")
        return process
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def open_admin_interface():
    """Open the admin interface in the browser"""
    admin_file = Path("admin-interface/enhanced-production-interface.html")
    
    if not admin_file.exists():
        print(f"❌ Admin interface not found: {admin_file}")
        return False
    
    # Wait a moment for the API server to start
    time.sleep(3)
    
    try:
        file_url = f"file://{admin_file.absolute()}"
        webbrowser.open(file_url)
        print(f"🌐 Admin interface opened: {file_url}")
        return True
    except Exception as e:
        print(f"❌ Failed to open admin interface: {e}")
        return False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down Cherry AI system...")
    sys.exit(0)

def main():
    """Main startup function"""
    print("🍒 Cherry AI System Startup")
    print("=" * 50)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check system requirements
    check_python_version()
    
    if not check_dependencies():
        print("\n💡 To install dependencies:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Set up environment
    setup_environment()
    
    # Check database (optional)
    db_available = check_database()
    if db_available:
        print("✅ Database connection successful")
    else:
        print("⚠️  Database unavailable - using mock data")
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        print("❌ Failed to start API server")
        sys.exit(1)
    
    # Open admin interface
    if not open_admin_interface():
        print("⚠️  Could not open admin interface automatically")
        print("   Please open: admin-interface/enhanced-production-interface.html")
    
    print("\n🎉 Cherry AI system is running!")
    print("📍 Services:")
    print("   • API Server: http://localhost:8000")
    print("   • API Docs: http://localhost:8000/docs")
    print("   • Admin Interface: admin-interface/enhanced-production-interface.html")
    print("\n⌨️  Press Ctrl+C to stop the system")
    
    try:
        # Keep the script running
        api_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        # Clean up
        if api_process:
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
        print("✅ Cherry AI system stopped")

if __name__ == "__main__":
    main() 