#!/usr/bin/env python3
"""
Database Setup for Cursor AI Integration
Creates necessary tables for logging and performance tracking
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.database import initialize_database

async def setup_cursor_ai_database():
    """Setup database tables for Cursor AI integration"""
    
    # Get database URL from environment or use default
    postgres_url = os.environ.get(
        'POSTGRES_URL',
        'postgresql://postgres:password@localhost:5432/orchestra'
    )
    
    weaviate_url = os.environ.get('WEAVIATE_URL', 'http://localhost:8080')
    weaviate_api_key = os.environ.get('WEAVIATE_API_KEY')
    
    db = await initialize_database(postgres_url, weaviate_url, weaviate_api_key)
    
    try:
        print("🗄️  Setting up Cursor AI database tables...")
        
        # Create cursor_ai_logs table
        await db.execute_query("""
            CREATE TABLE IF NOT EXISTS cursor_ai_logs (
                id SERIAL PRIMARY KEY,
                action VARCHAR(100) NOT NULL,
                file_path TEXT,
                status VARCHAR(50) NOT NULL,
                latency_seconds FLOAT,
                result JSONB,
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """, fetch=False)
        
        # Create indexes for performance
        await db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cursor_ai_logs_action 
            ON cursor_ai_logs(action);
        """, fetch=False)
        
        await db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cursor_ai_logs_status 
            ON cursor_ai_logs(status);
        """, fetch=False)
        
        await db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cursor_ai_logs_created_at 
            ON cursor_ai_logs(created_at DESC);
        """, fetch=False)
        
        await db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cursor_ai_logs_file_path 
            ON cursor_ai_logs(file_path);
        """, fetch=False)
        
        # Create performance metrics table
        await db.execute_query("""
            CREATE TABLE IF NOT EXISTS cursor_ai_performance_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(100) NOT NULL,
                metric_value FLOAT NOT NULL,
                metric_unit VARCHAR(20),
                metadata JSONB,
                recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
                UNIQUE(metric_name, recorded_at)
            );
        """, fetch=False)
        
        await db.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_cursor_ai_performance_metrics_name_time 
            ON cursor_ai_performance_metrics(metric_name, recorded_at DESC);
        """, fetch=False)
        
        print("✅ Cursor AI database tables created successfully!")
        
        # Insert initial test data
        await db.execute_query("""
            INSERT INTO cursor_ai_logs 
            (action, file_path, status, latency_seconds, result, created_at)
            VALUES 
            ('test_setup', 'setup_cursor_ai_database.py', 'success', 0.001, 
             '{"message": "Database setup completed"}', CURRENT_TIMESTAMP)
            ON CONFLICT DO NOTHING;
        """, fetch=False)
        
        print("✅ Test data inserted!")
    
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(setup_cursor_ai_database()) 