#!/usr/bin/env python3
"""Standalone Roo integration that works without external dependencies"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

class StandaloneRooIntegration:
    """Minimal Roo integration using only standard library"""
    
    def __init__(self):
        self.db_path = Path("roo_integration.db")
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database instead of PostgreSQL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mode_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode_name TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mode_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_mode TEXT,
                to_mode TEXT,
                context_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")
    
    def log_execution(self, mode_name, input_data, output_data):
        """Log mode execution to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO mode_executions (mode_name, input_data, output_data) VALUES (?, ?, ?)",
            (mode_name, json.dumps(input_data), json.dumps(output_data))
        )
        conn.commit()
        conn.close()
    
    def get_mode_stats(self):
        """Get mode execution statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mode_name, COUNT(*) as count 
            FROM mode_executions 
            GROUP BY mode_name
        """)
        stats = cursor.fetchall()
        conn.close()
        return stats

if __name__ == "__main__":
    integration = StandaloneRooIntegration()
    print("Roo Integration (Standalone) Ready!")
