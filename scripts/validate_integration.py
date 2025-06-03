# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
'''Validate integration of advanced system'''
        'search_history',
        'file_ingestions',
        'multimedia_generations',
        'operator_tasks'
    ]
    
    for table in tables:
        result = await db.fetch_one(
            f"SELECT COUNT(*) as count FROM information_schema.tables WHERE table_name = %s",
            (table,)
        )
        assert result['count'] > 0, f"Table {table} not found"
    
    print("✅ All database tables present")

async def validate_weaviate():
    from shared.weaviate_client import WeaviateClient
    client = WeaviateClient()
    
    classes = ['SearchIndex', 'MultimediaAsset']
    for class_name in classes:
        assert client.schema.exists(class_name), f"Class {class_name} not found"
    
    print("✅ All Weaviate classes present")

if __name__ == "__main__":
    asyncio.run(validate_endpoints())
    asyncio.run(validate_database())
    asyncio.run(validate_weaviate())
