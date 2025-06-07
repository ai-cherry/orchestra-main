#!/usr/bin/env python3
"""
"""
    """Test Weaviate connection with v4 API"""
            host="localhost",
            port=8080,
            grpc_port=50051
        )
        
        print("✅ Connected to Weaviate!")
        
        # Check if ready
        if client.is_ready():
            print("✅ Weaviate is ready!")
            
            # List collections
            collections = client.collections.list_all()
            print(f"📊 Found {len(collections)} collections")
            
            # Create a test collection if none exist
            if len(collections) == 0:
                print("Creating test collection...")
                client.collections.create(
                    name="TestCollection",
                    vectorizer_config=wvc.config.Configure.Vectorizer.none()
                )
                print("✅ Test collection created!")
            
            # List collections again
            collections = client.collections.list_all()
            for collection in collections:
                print(f"  - {collection}")
        
        client.close()
        print("✅ Connection test successful!")
        
    except Exception:

        
        pass
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_weaviate()