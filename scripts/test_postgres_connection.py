# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""Test PostgreSQL connection with various configurations."""
    """Test different PostgreSQL connection configurations."""
            "name": "postgres@localhost",
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "",
            "database": "postgres"
        },
        {
            "name": "postgres@orchestra",
            "host": "localhost", 
            "port": 5432,
            "user": "postgres",
            "password": "",
            "database": "orchestra"
        },
        {
            "name": "orchestra@orchestra",
            "host": "localhost",
            "port": 5432,
            "user": "orchestra",
            "password": "",
            "database": "orchestra"
        },
        {
            "name": "postgres@127.0.0.1",
            "host": "127.0.0.1",
            "port": 5432,
            "user": "postgres",
            "password": "",
            "database": "postgres"
        }
    ]
    
    for attempt in attempts:
        name = attempt.pop("name")
        try:

            pass
            print(f"\nTrying {name}...")
            conn = await asyncpg.connect(**attempt, timeout=5)
            version = await conn.fetchval('SELECT version()')
            await conn.close()
            print(f"✅ SUCCESS: {name}")
            print(f"   Version: {version.split(',')[0]}")
        except Exception:

            pass
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}")
    
    # Test with environment variables
    print("\n\nTesting with environment variables...")
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["POSTGRES_USER"] = "postgres"
    os.environ["POSTGRES_PASSWORD"] = ""
    os.environ["POSTGRES_DB"] = "orchestra"
    
    try:

    
        pass
        from shared.database import UnifiedDatabase
        await UnifiedDatabase.initialize_pool()
        async with UnifiedDatabase() as db:
            result = await db.fetch_one("SELECT 1 as test")
            print(f"✅ UnifiedDatabase SUCCESS: {result}")
    except Exception:

        pass
        print(f"❌ UnifiedDatabase FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(test_connections())