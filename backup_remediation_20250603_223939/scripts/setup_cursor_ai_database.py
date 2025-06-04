# TODO: Consider adding connection pooling configuration
#!/usr/bin/env python3
"""
"""
    """Setup database tables for Cursor AI integration"""
        print("🗄️  Setting up Cursor AI database tables...")
        
        # Create cursor_ai_logs table
        await db.execute_query("""
        """
        await db.execute_query("""
        """
        await db.execute_query("""
        """
        await db.execute_query("""
        """
        await db.execute_query("""
        """
        await db.execute_query("""
        """
        await db.execute_query("""
        """
        print("✅ Cursor AI database tables created successfully!")
        
        # Insert initial test data
        await db.execute_query("""
             '{"message": "Database setup completed"}', CURRENT_TIMESTAMP)
            ON CONFLICT DO NOTHING;
        """
        print("✅ Test data inserted!")
    
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(setup_cursor_ai_database()) 