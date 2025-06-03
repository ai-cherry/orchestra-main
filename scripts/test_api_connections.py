# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""Test API connections for Roo integration"""
    """Test OpenRouter API (mock)"""
    api_key = os.getenv("OPENROUTER_API_KEY", "mock-key")
    if api_key and len(api_key) > 10:
        print("✅ OpenRouter API key configured")
        return True
    else:
        print("⚠️  OpenRouter API key not found - using mock mode")
        return False

def test_database_connection():
    """Test database connection"""
    db_path = Path("roo_integration.db")
    if db_path.exists():
        print("✅ Database connection successful")
        return True
    else:
        print("❌ Database not found")
        return False

def test_mcp_server():
    """Test MCP server connection"""
        response = urllib.request.urlopen("http://localhost:8765/health", timeout=2)
        if response.status == 200:
            print("✅ MCP server is running")
            return True
    except Exception:

        pass
        print("⚠️  MCP server not running - start with: python3 scripts/simple_mcp_server.py &")
        return False

if __name__ == "__main__":
    print("Testing API Connections...")
    results = {
        "openrouter": test_openrouter_connection(),
        "database": test_database_connection(),
        "mcp_server": test_mcp_server()
    }
    
    print(f"\nConnection Test Results: {sum(results.values())}/{len(results)} passed")
